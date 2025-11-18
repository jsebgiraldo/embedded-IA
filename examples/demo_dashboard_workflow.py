"""
Simple test to demonstrate dashboard integration with a mock workflow.
This simulates what would happen during a real ESP32 code fix workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).parent.parent / "agent"
sys.path.insert(0, str(agent_dir))

from event_emitter import event_emitter, emit_log, emit_job_progress, emit_agent_status


async def simulate_esp32_workflow():
    """Simulate an ESP32 code fix workflow with realistic timing."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     ESP32 Developer Agent - Dashboard Integration Demo      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print("🌐 Make sure the dashboard is open at: http://localhost:8000\n")
    input("Press Enter to start the demo workflow... ")
    
    # Start event emitter
    await event_emitter.start()
    print("✅ Event emitter started\n")
    
    job_id = 100
    
    try:
        # ============================================================
        # PHASE 1: DETECT - Build and detect errors
        # ============================================================
        print("\n" + "="*60)
        print("PHASE 1: DETECT - Building project to find errors")
        print("="*60)
        
        await emit_log("INFO", "🚀 Starting ESP32 code fix workflow", job_id=job_id)
        await emit_log("INFO", "📂 Project: hello_world_esp32", job_id=job_id)
        await asyncio.sleep(1)
        
        # Build agent activates
        await emit_agent_status("build", "active")
        await emit_log("INFO", "🔨 Build agent: Compiling project...", agent_id="build", job_id=job_id)
        await emit_job_progress(job_id, "detect", 10, "Compiling project", agent_id="build")
        await asyncio.sleep(2)
        
        # Simulate build error detection
        await emit_job_progress(job_id, "detect", 30, "Build failed - analyzing errors", agent_id="build")
        await emit_log("WARNING", "⚠️  Build failed with 1 error", agent_id="build", job_id=job_id)
        await asyncio.sleep(1)
        
        await emit_log("ERROR", "❌ Error: implicit declaration of function 'gpio_set_direction'", 
                      agent_id="build", job_id=job_id)
        await emit_log("INFO", "📄 File: main/hello_world_main.c:15", agent_id="build", job_id=job_id)
        await asyncio.sleep(1)
        
        await emit_job_progress(job_id, "detect", 50, "1 error detected", agent_id="build")
        await emit_log("INFO", "🔍 Detected 1 build error to fix", agent_id="build", job_id=job_id)
        await emit_agent_status("build", "idle")
        await asyncio.sleep(2)
        
        # ============================================================
        # PHASE 2: ANALYZE - Analyze the error
        # ============================================================
        print("\n" + "="*60)
        print("PHASE 2: ANALYZE - Understanding the error")
        print("="*60)
        
        await emit_log("INFO", "🔍 Analyzing error patterns...", job_id=job_id)
        await emit_job_progress(job_id, "analyze", 10, "Analyzing error context", agent_id="developer")
        await asyncio.sleep(2)
        
        await emit_log("INFO", "💡 Diagnosis: Missing header file", job_id=job_id)
        await emit_log("INFO", "📋 Root cause: driver/gpio.h not included", job_id=job_id)
        await emit_job_progress(job_id, "analyze", 50, "Error analyzed successfully", agent_id="developer")
        await asyncio.sleep(2)
        
        # ============================================================
        # PHASE 3: FIX - Apply the fix using LLM
        # ============================================================
        print("\n" + "="*60)
        print("PHASE 3: FIX - Applying code fixes")
        print("="*60)
        
        await emit_agent_status("developer", "active")
        await emit_log("INFO", "🔧 Developer agent: Starting code fixes", agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "fix", 0, "Reading buggy code", agent_id="developer")
        await asyncio.sleep(1)
        
        await emit_log("INFO", "📖 Reading main/hello_world_main.c...", agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "fix", 20, "Analyzing code structure", agent_id="developer")
        await asyncio.sleep(2)
        
        await emit_log("INFO", "🤖 Calling LLM (qwen3-coder:latest)...", agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "fix", 40, "LLM generating fix", agent_id="developer")
        await asyncio.sleep(3)  # Simulate LLM thinking time
        
        await emit_log("SUCCESS", "✅ LLM fix generated with 95% confidence", agent_id="developer", job_id=job_id)
        await emit_log("INFO", "📝 Fix: Add #include \"driver/gpio.h\" at line 4", agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "fix", 70, "Applying fix to file", agent_id="developer")
        await asyncio.sleep(1)
        
        await emit_log("SUCCESS", "💾 Fixed code written to main/hello_world_main.c", 
                      agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "fix", 100, "Fix applied successfully", agent_id="developer")
        await emit_log("SUCCESS", "🎉 1 fix applied successfully", agent_id="developer", job_id=job_id)
        await emit_agent_status("developer", "idle")
        await asyncio.sleep(2)
        
        # ============================================================
        # PHASE 4: VALIDATE - Rebuild to verify fix
        # ============================================================
        print("\n" + "="*60)
        print("PHASE 4: VALIDATE - Verifying the fix")
        print("="*60)
        
        await emit_agent_status("test", "active")
        await emit_log("INFO", "🧪 Test agent: Validating fixes", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 0, "Starting validation", agent_id="test")
        await asyncio.sleep(1)
        
        await emit_log("INFO", "🔨 Rebuilding project...", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 30, "Recompiling with fixes", agent_id="test")
        await asyncio.sleep(3)  # Simulate rebuild time
        
        await emit_log("SUCCESS", "✅ Build successful - no errors!", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 70, "Build passed", agent_id="test")
        await asyncio.sleep(1)
        
        await emit_log("INFO", "🎯 Running validation checks...", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 90, "Running tests", agent_id="test")
        await asyncio.sleep(2)
        
        await emit_log("SUCCESS", "✅ All validation checks passed", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 100, "Validation complete", agent_id="test")
        await emit_agent_status("test", "idle")
        await asyncio.sleep(1)
        
        # ============================================================
        # WORKFLOW COMPLETE
        # ============================================================
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        
        await emit_log("SUCCESS", "🎉 Workflow completed successfully!", job_id=job_id)
        await emit_log("INFO", "📊 Summary: 1 error detected, 1 fix applied, build passed", job_id=job_id)
        
        print("\n✨ Demo workflow completed!")
        print("\n📊 Check the dashboard for:")
        print("  ✓ Real-time logs in chronological order")
        print("  ✓ Agent status changes (build → developer → test)")
        print("  ✓ Progress bars for each phase")
        print("  ✓ Workflow visualization showing all 4 phases")
        print("  ✓ Job entry in Recent Jobs with success status")
        
    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
        await emit_log("ERROR", f"Workflow failed: {str(e)}", job_id=job_id)
    
    finally:
        # Keep running to allow events to be processed
        print("\n⏳ Keeping event emitter running for 10 seconds...")
        await asyncio.sleep(10)
        
        await event_emitter.stop()
        print("✅ Event emitter stopped")


async def main():
    """Main entry point."""
    try:
        await simulate_esp32_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
