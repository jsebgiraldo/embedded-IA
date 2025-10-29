#!/usr/bin/env python3
"""
Test Developer Agent with Real LLM

This script demonstrates the Developer Agent using real LLM models
to fix ESP32 compilation errors.

Usage:
    # With local Ollama (default)
    python3 examples/test_developer_agent.py
    
    # With specific model
    LLM_MODEL=deepseek-coder-v2:16b python3 examples/test_developer_agent.py
    
    # With OpenAI
    LLM_PROVIDER=openai python3 examples/test_developer_agent.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_provider import get_llm, LLMConfig, LLMProvider
from typing import Dict, Any


# Test cases: ESP32 code with common compilation errors
TEST_CASES = {
    "missing_include": {
        "description": "Missing GPIO driver include",
        "code": """#include <stdio.h>

void app_main() {
    gpio_set_level(GPIO_NUM_2, 1);
    gpio_set_direction(GPIO_NUM_2, GPIO_MODE_OUTPUT);
}""",
        "error": """main.c:4:5: error: implicit declaration of function 'gpio_set_level'
main.c:4:20: error: 'GPIO_NUM_2' undeclared
main.c:5:5: error: implicit declaration of function 'gpio_set_direction'
main.c:5:34: error: 'GPIO_MODE_OUTPUT' undeclared""",
    },
    
    "wrong_delay": {
        "description": "Using delay() instead of vTaskDelay",
        "code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void app_main() {
    while(1) {
        printf("Hello\\n");
        delay(1000);  // Wrong!
    }
}""",
        "error": """main.c:8:9: error: implicit declaration of function 'delay'""",
    },
    
    "missing_config": {
        "description": "Missing WiFi include",
        "code": """#include <stdio.h>

void app_main() {
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
}""",
        "error": """main.c:4:5: error: unknown type name 'wifi_init_config_t'
main.c:4:30: error: 'WIFI_INIT_CONFIG_DEFAULT' undeclared
main.c:5:5: error: implicit declaration of function 'esp_wifi_init'""",
    }
}


def test_fix_code(llm, test_name: str, test_case: Dict[str, str]) -> Dict[str, Any]:
    """
    Test LLM's ability to fix ESP32 code
    
    Args:
        llm: LLM instance
        test_name: Name of test case
        test_case: Dict with code, error, description
    
    Returns:
        Dict with results
    """
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"Description: {test_case['description']}")
    print(f"{'='*70}\n")
    
    print("❌ Original code (with errors):")
    print("```c")
    print(test_case['code'])
    print("```\n")
    
    print("⚠️  Compilation errors:")
    print(test_case['error'])
    print()
    
    # Create prompt for LLM
    prompt = f"""You are an expert ESP32 embedded systems developer. Fix the following C code that has compilation errors.

**Original Code:**
```c
{test_case['code']}
```

**Compilation Errors:**
```
{test_case['error']}
```

**Requirements:**
1. Add all necessary #include statements
2. Fix all function calls and constants
3. Use proper ESP-IDF APIs
4. Return ONLY the corrected code, no explanations
5. Keep the code simple and functional

**Corrected Code:**
"""
    
    print("🤖 Asking LLM to fix the code...")
    
    try:
        # Get fix from LLM
        response = llm.invoke(prompt)
        
        # Extract code from response (remove markdown if present)
        fixed_code = str(response)
        if "```c" in fixed_code:
            fixed_code = fixed_code.split("```c")[1].split("```")[0].strip()
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
        
        print("\n✅ Fixed code:")
        print("```c")
        print(fixed_code)
        print("```\n")
        
        # Basic validation
        has_includes = "#include" in fixed_code
        has_app_main = "app_main" in fixed_code
        
        success = has_includes and has_app_main
        
        return {
            "success": success,
            "original_code": test_case['code'],
            "fixed_code": fixed_code,
            "has_includes": has_includes,
            "has_app_main": has_app_main,
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Run Developer Agent tests"""
    print("🧪 ESP32 Developer Agent - LLM Integration Test\n")
    
    # Get LLM configuration from environment
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv("LLM_MODEL", "qwen2.5-coder:14b")
    
    print(f"Provider: {provider}")
    print(f"Model: {model}\n")
    
    # Initialize LLM
    print("🔧 Initializing LLM...")
    
    config = LLMConfig(
        provider=LLMProvider(provider),
        model=model,
        temperature=0.0,  # Deterministic for code
        fallback_to_local=True
    )
    
    try:
        llm = get_llm(config)
        print("✅ LLM initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}\n")
        print("💡 Tips:")
        print("   - Make sure Ollama is running: ollama serve")
        print("   - Install model: ollama pull qwen2.5-coder:14b")
        print("   - Or set OPENAI_API_KEY for cloud option")
        sys.exit(1)
    
    # Run tests
    results = []
    for test_name, test_case in TEST_CASES.items():
        result = test_fix_code(llm, test_name, test_case)
        results.append((test_name, result))
        
        # Pause between tests
        input("\nPress Enter to continue to next test...")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}\n")
    
    passed = sum(1 for _, r in results if r.get("success", False))
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result.get("success") and "error" in result:
            print(f"      Error: {result['error']}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Developer Agent is ready for Phase 2!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
