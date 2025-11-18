"""
Test script to verify event emission from orchestrator to dashboard.
This script simulates a simple workflow and emits events.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent and agent directory to path
parent_dir = Path(__file__).parent.parent
agent_dir = parent_dir / "agent"
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(agent_dir))

# Import only event_emitter to avoid loading langchain dependencies
from event_emitter import event_emitter, EventType, Event, emit_log, emit_job_progress, emit_agent_status


async def test_event_emission():
    """Test event emission without running full orchestrator."""
    
    print("🧪 Testing Event Emission System\n")
    print("=" * 60)
    
    # Start event emitter
    await event_emitter.start()
    print("✅ Event emitter started\n")
    
    # Simulate a job workflow
    job_id = 1
    
    try:
        # 1. Job started
        print("📝 Phase 1: Job Start")
        await emit_log("INFO", "🚀 Starting test job", job_id=job_id)
        await asyncio.sleep(1)
        
        # 2. Developer agent activated
        print("📝 Phase 2: Developer Agent")
        await emit_agent_status("developer", "active")
        await emit_log("INFO", "👨‍💻 Developer agent activated", agent_id="developer", job_id=job_id)
        await emit_job_progress(job_id, "analyze", 0, "Starting code analysis", agent_id="developer")
        await asyncio.sleep(1)
        
        # 3. Progress updates
        for i in range(25, 101, 25):
            await emit_job_progress(job_id, "analyze", i, f"Analyzing code... {i}%", agent_id="developer")
            await asyncio.sleep(0.5)
        
        await emit_log("SUCCESS", "✅ Code analysis complete", agent_id="developer", job_id=job_id)
        await emit_agent_status("developer", "idle")
        await asyncio.sleep(1)
        
        # 4. Build agent activated
        print("📝 Phase 3: Build Agent")
        await emit_agent_status("build", "active")
        await emit_log("INFO", "🔨 Build agent activated", agent_id="build", job_id=job_id)
        await emit_job_progress(job_id, "build", 0, "Starting compilation", agent_id="build")
        await asyncio.sleep(1)
        
        # 5. Build progress
        for i in range(33, 101, 33):
            await emit_job_progress(job_id, "build", min(i, 100), f"Compiling... {min(i, 100)}%", agent_id="build")
            await asyncio.sleep(0.5)
        
        await emit_log("SUCCESS", "✅ Build successful", agent_id="build", job_id=job_id)
        await emit_agent_status("build", "idle")
        await asyncio.sleep(1)
        
        # 6. Test agent activated
        print("📝 Phase 4: Test Agent")
        await emit_agent_status("test", "active")
        await emit_log("INFO", "🧪 Test agent activated", agent_id="test", job_id=job_id)
        await emit_job_progress(job_id, "validate", 0, "Running tests", agent_id="test")
        await asyncio.sleep(1)
        
        # 7. Test progress
        for i in range(50, 101, 50):
            await emit_job_progress(job_id, "validate", i, f"Testing... {i}%", agent_id="test")
            await asyncio.sleep(0.5)
        
        await emit_log("SUCCESS", "✅ All tests passed", agent_id="test", job_id=job_id)
        await emit_agent_status("test", "idle")
        await asyncio.sleep(1)
        
        # 8. Job completed
        print("📝 Phase 5: Job Complete")
        await emit_log("SUCCESS", "🎉 Job completed successfully", job_id=job_id)
        
        print("\n" + "=" * 60)
        print("✅ Event emission test completed!")
        print("\nCheck the dashboard at http://localhost:8000 to see:")
        print("  - Real-time logs in the Live Logs section")
        print("  - Agent status changes (developer, build, test)")
        print("  - Job progress updates")
        print("  - Workflow phases visualization")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Keep running for a bit to ensure events are processed
        print("\n⏳ Waiting 5 seconds for events to be processed...")
        await asyncio.sleep(5)
        
        # Stop event emitter
        await event_emitter.stop()
        print("✅ Event emitter stopped")


async def test_workflow_phases():
    """Test workflow phase events."""
    
    print("\n🧪 Testing Workflow Phase Events\n")
    print("=" * 60)
    
    await event_emitter.start()
    
    job_id = 2
    phases = ["detect", "analyze", "fix", "validate"]
    
    try:
        for phase in phases:
            print(f"📝 Starting phase: {phase}")
            
            # Phase started
            event = Event(
                event_type=EventType.WORKFLOW_PHASE_STARTED,
                data={
                    "job_id": job_id,
                    "phase": phase,
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            await event_emitter.emit(event)
            
            await asyncio.sleep(2)
            
            # Phase completed
            event = Event(
                event_type=EventType.WORKFLOW_PHASE_COMPLETED,
                data={
                    "job_id": job_id,
                    "phase": phase,
                    "success": True,
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            await event_emitter.emit(event)
            
            await asyncio.sleep(1)
        
        print("\n" + "=" * 60)
        print("✅ Workflow phase test completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await asyncio.sleep(3)
        await event_emitter.stop()


async def main():
    """Run all tests."""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Event Emission Test Suite                           ║
║                                                               ║
║  Make sure the web server is running at:                     ║
║  http://localhost:8000                                        ║
║                                                               ║
║  Open the dashboard in your browser to see real-time         ║
║  updates as events are emitted.                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start tests... ")
    
    # Run tests
    await test_event_emission()
    
    print("\n" + "=" * 60)
    input("\nPress Enter to test workflow phases... ")
    
    await test_workflow_phases()
    
    print("\n" + "=" * 60)
    print("\n✨ All tests completed!")
    print("\nYou should have seen in the dashboard:")
    print("  ✓ Agent status changes (active/idle)")
    print("  ✓ Log entries appearing in real-time")
    print("  ✓ Job progress bars updating")
    print("  ✓ Workflow phases changing")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
