#!/usr/bin/env python3
"""
Test Orchestrator with LLM Integration
Demonstrates Developer Agent using Ollama to fix real ESP32 code issues
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.orchestrator import AgentOrchestrator, AgentRole
from agent.test_cases import get_test_case


class MockLangChainTool:
    """Mock LangChain tool for testing without MCP server"""
    def __init__(self, name: str):
        self.name = name
    
    async def ainvoke(self, *args, **kwargs):
        return {"success": True, "data": f"Mock result from {self.name}"}


async def test_developer_fix_with_llm():
    """
    Test the Developer Agent's ability to fix code using LLM.
    
    This creates a temporary buggy file, runs the orchestrator's
    _developer_fix() method, and validates the fix.
    """
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║          ORCHESTRATOR + LLM INTEGRATION TEST                             ║
║          Testing Developer Agent with Real Code Fixes                    ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    # Initialize orchestrator with LLM
    print("\n1️⃣  Initializing Orchestrator with Ollama...")
    mock_tools = [MockLangChainTool(name) for name in [
        "list_files", "read_source_file", "idf_set_target",
        "idf_build", "idf_clean", "idf_flash"
    ]]
    
    orchestrator = AgentOrchestrator(
        langchain_tools=mock_tools,
        llm_provider="ollama",
        llm_model="qwen2.5-coder:14b"
    )
    
    # Get a test case (missing GPIO include)
    print("\n2️⃣  Loading test case: Missing GPIO header...")
    test_case = get_test_case("missing_gpio_include")
    
    # Create temporary file with buggy code
    temp_dir = Path("/tmp/orchestrator_test")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "buggy_gpio.c"
    
    print(f"   📝 Creating temp file: {temp_file}")
    with open(temp_file, 'w') as f:
        f.write(test_case["buggy_code"])
    
    # Simulate QA reporting an issue
    print("\n3️⃣  Simulating QA Agent reporting issue...")
    issues = [{
        "severity": "error",
        "message": test_case["expected_error"],
        "file": str(temp_file),
        "component": "main",
        "line": 10
    }]
    
    print(f"\n   🔍 Issue detected:")
    print(f"   File: {temp_file.name}")
    print(f"   Error: {test_case['expected_error']}")
    
    # Call Developer Agent to fix
    print("\n4️⃣  Calling Developer Agent to fix issue...")
    print("   (This uses Ollama Qwen2.5-Coder locally)\n")
    
    result = await orchestrator._developer_fix(issues)
    
    # Display results
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)
    
    if result["success"]:
        print("\n✅ Developer Agent successfully fixed the code!")
        
        if result["fixes"]:
            fix = result["fixes"][0]
            print(f"\n📝 Fix Details:")
            print(f"   Component: {fix['component']}")
            print(f"   Confidence: {fix['confidence']}")
            print(f"   Diagnosis: {fix['diagnosis']}")
            print(f"   Changes: {fix['changes_made']}")
            
            # Show the fixed code
            print(f"\n📄 Fixed Code:")
            with open(temp_file, 'r') as f:
                fixed_code = f.read()
            
            print("\n" + "-"*80)
            print(fixed_code)
            print("-"*80)
            
            # Validate fix
            print(f"\n🔍 Validation:")
            if "driver/gpio.h" in fixed_code:
                print("   ✅ GPIO header included")
            else:
                print("   ❌ GPIO header still missing")
            
            if "gpio_set_level" in fixed_code:
                print("   ✅ GPIO function present")
            else:
                print("   ❌ GPIO function missing")
        
        if result["failures"]:
            print(f"\n⚠️  Some fixes failed:")
            for failure in result["failures"]:
                print(f"   - {failure['reason']}")
    else:
        print("\n❌ Developer Agent could not fix the issues")
        if result["failures"]:
            for failure in result["failures"]:
                print(f"   - {failure['reason']}")
    
    # Cleanup
    print(f"\n5️⃣  Cleaning up temp files...")
    if temp_file.exists():
        temp_file.unlink()
    if temp_dir.exists():
        temp_dir.rmdir()
    
    print("\n✅ Test completed!")
    print("\n" + "="*80)
    
    return result


async def test_multiple_fixes():
    """
    Test fixing multiple issues in parallel.
    
    This demonstrates the orchestrator handling multiple QA issues
    and applying fixes to different files.
    """
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║          BATCH FIX TEST - Multiple Issues                                ║
║          Testing Developer Agent with 3 Simultaneous Fixes               ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    # Initialize orchestrator
    print("\n1️⃣  Initializing Orchestrator...")
    mock_tools = [MockLangChainTool(name) for name in ["list_files", "idf_build"]]
    orchestrator = AgentOrchestrator(
        langchain_tools=mock_tools,
        llm_provider="ollama",
        llm_model="qwen2.5-coder:14b"
    )
    
    # Create temp directory
    temp_dir = Path("/tmp/orchestrator_batch_test")
    temp_dir.mkdir(exist_ok=True)
    
    # Load multiple test cases
    print("\n2️⃣  Loading 3 test cases...")
    test_cases = [
        ("missing_gpio_include", "gpio_test.c"),
        ("wrong_gpio_type", "gpio_type.c"),
        ("nvs_missing_init", "nvs_test.c")
    ]
    
    issues = []
    temp_files = []
    
    for case_name, filename in test_cases:
        test_case = get_test_case(case_name)
        temp_file = temp_dir / filename
        
        # Write buggy code
        with open(temp_file, 'w') as f:
            f.write(test_case["buggy_code"])
        
        temp_files.append(temp_file)
        
        issues.append({
            "severity": "error",
            "message": test_case["expected_error"],
            "file": str(temp_file),
            "component": "main",
            "line": 10
        })
        
        print(f"   📝 {filename}: {test_case['expected_error'][:50]}...")
    
    # Call Developer Agent to fix all issues
    print("\n3️⃣  Fixing all issues with Developer Agent...")
    print("   (Processing 3 files with Ollama)\n")
    
    result = await orchestrator._developer_fix(issues)
    
    # Display results
    print("\n" + "="*80)
    print("📊 BATCH RESULTS")
    print("="*80)
    
    print(f"\n✅ Fixed: {len(result['fixes'])}")
    print(f"❌ Failed: {len(result['failures'])}")
    print(f"📈 Success Rate: {len(result['fixes'])/len(issues)*100:.1f}%")
    
    if result["fixes"]:
        print(f"\n📝 Successfully Fixed:")
        for fix in result["fixes"]:
            filename = Path(fix["file"]).name
            print(f"\n   {filename}:")
            print(f"   └─ {fix['changes_made']}")
            print(f"   └─ Confidence: {fix['confidence']}")
    
    if result["failures"]:
        print(f"\n⚠️  Failed Fixes:")
        for failure in result["failures"]:
            print(f"   - {failure['reason']}")
    
    # Cleanup
    print(f"\n4️⃣  Cleaning up...")
    for temp_file in temp_files:
        if temp_file.exists():
            temp_file.unlink()
    if temp_dir.exists():
        temp_dir.rmdir()
    
    print("\n✅ Batch test completed!")
    print("="*80)
    
    return result


async def main():
    """Run orchestrator tests"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Orchestrator with LLM Integration")
    parser.add_argument(
        "--mode",
        choices=["single", "batch", "both"],
        default="single",
        help="Test mode: single fix, batch fixes, or both"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "single" or args.mode == "both":
            result = await test_developer_fix_with_llm()
            
            if args.mode == "both":
                print("\n\n" + "🔄 "*30 + "\n")
                await asyncio.sleep(1)
        
        if args.mode == "batch" or args.mode == "both":
            result = await test_multiple_fixes()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
