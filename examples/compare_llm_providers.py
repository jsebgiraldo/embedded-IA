#!/usr/bin/env python3
"""
Compare Local vs Cloud LLM Performance

Prueba el mismo caso con diferentes proveedores y compara:
- Velocidad (tokens/segundo)
- Calidad de la respuesta
- Costo estimado

Usage:
    python3 examples/compare_llm_providers.py
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_provider import get_llm, LLMConfig, LLMProvider


# Test case: ESP32 GPIO with missing include
TEST_CASE = {
    "name": "GPIO Missing Include",
    "code": """#include <stdio.h>

void app_main() {
    gpio_set_level(GPIO_NUM_2, 1);
    gpio_set_direction(GPIO_NUM_2, GPIO_MODE_OUTPUT);
    printf("GPIO initialized\\n");
}""",
    "error": """main.c:4:5: error: implicit declaration of function 'gpio_set_level'
main.c:4:20: error: 'GPIO_NUM_2' undeclared
main.c:5:5: error: implicit declaration of function 'gpio_set_direction'""",
    "expected": "driver/gpio.h"
}


def test_llm(provider: LLMProvider, model: str, test_case: dict) -> dict:
    """Test a single LLM provider"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing: {provider.value} - {model}")
    print(f"{'='*80}\n")
    
    # Create config
    config = LLMConfig(
        provider=provider,
        model=model,
        temperature=0.0,
    )
    
    # Initialize LLM
    print("📡 Connecting to LLM...")
    try:
        start_init = time.time()
        llm = get_llm(config)
        init_time = time.time() - start_init
        print(f"✅ Connected in {init_time:.2f}s\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}\n")
        return {
            "provider": provider.value,
            "model": model,
            "success": False,
            "error": str(e)
        }
    
    # Create prompt
    prompt = f"""You are an expert ESP32 firmware developer. Fix this code with compilation errors.

**Original Code:**
```c
{test_case['code']}
```

**Compilation Errors:**
```
{test_case['error']}
```

**Instructions:**
1. Add ALL necessary #include statements at the top
2. Fix all undefined functions and constants
3. Use proper ESP-IDF APIs (not Arduino)
4. Return ONLY the corrected code, no explanations

**Fixed Code:**
"""
    
    # Invoke LLM
    print("🤖 Generating fix...")
    try:
        start_gen = time.time()
        response = llm.invoke(prompt)
        gen_time = time.time() - start_gen
        
        # Extract code
        fixed_code = str(response)
        if "```c" in fixed_code:
            fixed_code = fixed_code.split("```c")[1].split("```")[0].strip()
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
        
        # Estimate tokens
        tokens = len(fixed_code.split())
        tokens_per_sec = tokens / gen_time if gen_time > 0 else 0
        
        # Validate fix
        has_include = test_case['expected'] in fixed_code
        has_main = "app_main" in fixed_code
        success = has_include and has_main
        
        print(f"\n{'✅' if success else '⚠️ '} Generated in {gen_time:.2f}s")
        print(f"📊 Tokens: ~{tokens} ({tokens_per_sec:.1f} tok/s)")
        print(f"{'✅' if has_include else '❌'} Has required include: {test_case['expected']}")
        print(f"{'✅' if has_main else '❌'} Has app_main function")
        
        # Display code
        print(f"\n📝 Fixed code:")
        print("```c")
        print(fixed_code[:500] + ("..." if len(fixed_code) > 500 else ""))
        print("```")
        
        return {
            "provider": provider.value,
            "model": model,
            "success": success,
            "generation_time": gen_time,
            "tokens": tokens,
            "tokens_per_second": tokens_per_sec,
            "has_include": has_include,
            "code_length": len(fixed_code)
        }
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        return {
            "provider": provider.value,
            "model": model,
            "success": False,
            "error": str(e)
        }


def estimate_cost(provider: str, tokens: int) -> float:
    """Estimate cost in USD for the request"""
    # Pricing as of October 2025 (per 1M tokens, average input+output)
    pricing = {
        "ollama": 0.0,  # Free
        "openai-gpt-4o": 6.25,  # ($2.50 input + $10.00 output) / 2
        "openai-gpt-4o-mini": 0.375,  # ($0.15 + $0.60) / 2
        "anthropic-sonnet": 9.0,  # ($3.00 + $15.00) / 2
        "anthropic-haiku": 2.4,  # ($0.80 + $4.00) / 2
    }
    
    key = f"{provider.split('-')[0]}-{provider.split('/')[-1] if '/' in provider else provider.split('-')[-1]}"
    rate = pricing.get(key, 0)
    return (tokens / 1_000_000) * rate


def main():
    """Run comparison"""
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "LLM PROVIDER COMPARISON TEST" + " "*30 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    # Define providers to test
    providers_to_test = []
    
    # Always test local (Ollama)
    if os.path.exists(os.path.expanduser("~/.ollama")):
        providers_to_test.append((LLMProvider.OLLAMA, "qwen2.5-coder:14b"))
        print("✅ Ollama detected - will test local model")
    else:
        print("⚠️  Ollama not found - skipping local test")
    
    # Test OpenAI if API key available
    if os.getenv("OPENAI_API_KEY"):
        providers_to_test.append((LLMProvider.OPENAI, "gpt-4o-mini"))
        print("✅ OpenAI API key found - will test GPT-4o-mini")
    else:
        print("⚠️  No OpenAI API key - skipping OpenAI test")
    
    # Test Anthropic if API key available
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_to_test.append((LLMProvider.ANTHROPIC, "claude-3-5-haiku-20241022"))
        print("✅ Anthropic API key found - will test Claude Haiku")
    else:
        print("⚠️  No Anthropic API key - skipping Anthropic test")
    
    if not providers_to_test:
        print("\n❌ No providers available to test!")
        print("\n💡 Setup options:")
        print("   1. Install Ollama: brew install ollama")
        print("   2. Add OpenAI key: export OPENAI_API_KEY='sk-...'")
        print("   3. Add Anthropic key: export ANTHROPIC_API_KEY='sk-ant-...'")
        return
    
    print(f"\n🎯 Will test {len(providers_to_test)} provider(s)\n")
    input("Press Enter to start comparison...")
    
    # Run tests
    results = []
    for provider, model in providers_to_test:
        try:
            result = test_llm(provider, model, TEST_CASE)
            results.append(result)
            time.sleep(1)  # Small delay between tests
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            continue
    
    # Display comparison
    print("\n" + "═"*80)
    print("📊 COMPARISON RESULTS")
    print("═"*80 + "\n")
    
    if not results:
        print("❌ No results to compare")
        return
    
    # Filter successful results
    successful = [r for r in results if r.get('success')]
    
    if not successful:
        print("❌ No successful tests to compare")
        return
    
    # Sort by speed
    successful.sort(key=lambda x: x.get('tokens_per_second', 0), reverse=True)
    
    # Display table
    print(f"{'Provider':<25} {'Speed':<15} {'Cost':<12} {'Quality':<10}")
    print("-"*80)
    
    for result in successful:
        provider_name = f"{result['provider']} ({result['model'].split(':')[-1] if ':' in result['model'] else result['model'].split('-')[-1]})"
        speed = f"{result['tokens_per_second']:.1f} tok/s"
        
        # Calculate cost
        cost = estimate_cost(result['provider'], result['tokens'])
        cost_str = "FREE" if cost == 0 else f"${cost:.4f}"
        
        quality = "✅ Pass" if result.get('has_include') else "⚠️  Partial"
        
        print(f"{provider_name:<25} {speed:<15} {cost_str:<12} {quality:<10}")
    
    # Winner analysis
    print("\n🏆 Analysis:")
    
    fastest = max(successful, key=lambda x: x['tokens_per_second'])
    print(f"   Fastest: {fastest['provider']} ({fastest['tokens_per_second']:.1f} tok/s)")
    
    free_results = [r for r in successful if r['provider'] == 'ollama']
    if free_results:
        print(f"   Free option: Ollama (0 cost, {free_results[0]['tokens_per_second']:.1f} tok/s)")
    
    cheapest_paid = min([r for r in successful if r['provider'] != 'ollama'], 
                        key=lambda x: estimate_cost(x['provider'], x['tokens']),
                        default=None)
    if cheapest_paid:
        cost = estimate_cost(cheapest_paid['provider'], cheapest_paid['tokens'])
        print(f"   Cheapest paid: {cheapest_paid['provider']} (${cost:.4f} per fix)")
    
    # Recommendation
    print("\n💡 Recommendation:")
    if free_results and free_results[0]['tokens_per_second'] > 2.0:
        print("   Use Ollama (local) for daily development - it's FREE and fast enough!")
    
    if cheapest_paid:
        cost_per_month = estimate_cost(cheapest_paid['provider'], cheapest_paid['tokens']) * 1000
        print(f"   Use {cheapest_paid['provider']} for CI/CD - only ${cost_per_month:.2f}/month for 1000 fixes")
    
    print("\n" + "═"*80)
    print("✨ Test Complete!")
    print("═"*80 + "\n")


if __name__ == "__main__":
    main()
