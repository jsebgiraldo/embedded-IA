#!/usr/bin/env python3
"""
Run QEMU and display Hello World output in real-time
"""
import sys
import time
sys.path.insert(0, '/mcp-server/src')

from mcp_idf.tools import IDFTools

def main():
    tools = IDFTools()
    
    print("🎮 Starting QEMU Simulation...")
    print("=" * 60)
    
    # Start QEMU
    result = tools.run_qemu(target='esp32')
    if not result['success']:
        print(f"❌ Failed to start QEMU: {result['stderr']}")
        return 1
    
    print(f"✅ QEMU started (PID: {result['qemu_info']['pid']})")
    print()
    
    # Monitor output for 15 seconds
    print("📺 Live Output (15 seconds):")
    print("=" * 60)
    
    for i in range(15):
        time.sleep(1)
        result = tools.qemu_output(lines=100)
        
        if result['success'] and result['stdout']:
            # Clear screen and show output
            print("\033[2J\033[H", end="")  # Clear screen
            print("🎮 QEMU Simulation Running")
            print("=" * 60)
            
            # Show status
            status = tools.qemu_status()
            if status['status']['running']:
                s = status['status']
                print(f"PID: {s['pid']} | CPU: {s['cpu_percent']:.1f}% | Memory: {s['memory_mb']:.1f}MB | Runtime: {s['runtime_seconds']:.1f}s")
                print("=" * 60)
            
            # Show output
            print(result['stdout'])
            print("=" * 60)
            print(f"⏱️  Time: {i+1}s / 15s | Press Ctrl+C to stop")
    
    print()
    print("🛑 Stopping QEMU...")
    result = tools.stop_qemu()
    print(result['stdout'])
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        tools = IDFTools()
        tools.stop_qemu()
        sys.exit(0)
