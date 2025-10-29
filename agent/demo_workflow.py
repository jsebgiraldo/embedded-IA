#!/usr/bin/env python3
"""
ESP32 Multi-Agent Workflow Demo
Demonstrates complete development lifecycle with parallel execution
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_idf.client import MCPClient
from agent.orchestrator import AgentOrchestrator


async def main():
    """Run complete workflow demonstration"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     ESP32 Multi-Agent Development Workflow Demo                  ║
║     Parallel Execution | QA Feedback Loop | Role-Based Agents    ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Initialize MCP client and get LangChain tools
    print("🔧 Initializing MCP Client and LangChain tools...")
    mcp_client = MCPClient()
    tools = mcp_client.get_langchain_tools()
    print(f"✅ Loaded {len(tools)} tools")
    
    # Display agent roles
    print("\n📋 Agent Roles:")
    print("   🎯 Project Manager - Import, validate, coordinate")
    print("   👨‍💻 Developer - Write/fix code")
    print("   🔨 Builder - Compile firmware, manage artifacts")
    print("   🧪 Tester - Flash device + QEMU (PARALLEL)")
    print("   🏥 Doctor - Hardware diagnostics")
    print("   ✅ QA - Validate results, report issues")
    
    # Create orchestrator
    print("\n🎭 Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator(tools)
    
    # Display workflow
    print("\n📊 Workflow Phases:")
    print("   1️⃣  Project Setup (sequential)")
    print("       └─ Validate structure → Set target")
    print("   2️⃣  Build (sequential)")
    print("       └─ Compile firmware → Cache artifacts")
    print("   3️⃣  Testing (PARALLEL ⚡)")
    print("       ├─ Flash to hardware")
    print("       └─ QEMU simulation")
    print("   4️⃣  Validation (PARALLEL ⚡)")
    print("       ├─ Doctor diagnostics")
    print("       └─ QA analysis")
    print("   5️⃣  Feedback Loop (if issues found)")
    print("       └─ Developer fix → Rebuild → Retest")
    
    # Execute workflow
    print("\n" + "="*70)
    print("🚀 Starting Workflow Execution...")
    print("="*70 + "\n")
    
    try:
        # Run with both flash and QEMU enabled
        results = await orchestrator.execute_workflow(
            project_path="/workspace",
            target="esp32",
            flash_device=False,  # Set to True to flash real hardware
            run_qemu=True
        )
        
        print("\n" + "="*70)
        print("📈 Workflow Results")
        print("="*70)
        
        # Display summary
        print(orchestrator.get_workflow_summary())
        
        # Display detailed results
        print("\n📊 Phase Results:\n")
        for phase_name, phase_result in results["phases"].items():
            success_icon = "✅" if phase_result.get("success") else "❌"
            print(f"{success_icon} {phase_name}")
            if not phase_result.get("success"):
                print(f"   Error: {phase_result.get('error', 'Unknown error')}")
        
        # Display QA feedback iterations
        if results["qa_iterations"] > 0:
            print(f"\n🔄 QA Feedback Iterations: {results['qa_iterations']}")
        
        # Final status
        print("\n" + "="*70)
        if results["success"]:
            print("✅ Workflow completed successfully!")
        else:
            print("❌ Workflow completed with errors")
        print("="*70)
        
        # Display artifacts
        if results.get("artifacts"):
            print("\n📦 Generated Artifacts:")
            for artifact_name in results["artifacts"].keys():
                print(f"   • {artifact_name}")
        
    except Exception as e:
        print(f"\n❌ Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
