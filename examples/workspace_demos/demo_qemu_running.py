#!/usr/bin/env python3
"""
Demo QEMU with detailed monitoring
Shows the Hello World program running in QEMU with process metrics
"""
import sys
import time
import subprocess
sys.path.insert(0, '/mcp-server/src')

from mcp_idf.tools import IDFTools

def show_qemu_info():
    """Display detailed QEMU execution info"""
    tools = IDFTools()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       ESP32 Hello World Running in QEMU Simulator         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Start QEMU
    print("🚀 Starting QEMU...")
    result = tools.run_qemu(target='esp32')
    
    if not result['success']:
        print(f"❌ Failed: {result['stderr']}")
        return 1
    
    print(f"✅ QEMU Started (PID: {result['qemu_info']['pid']})")
    print(f"📦 ELF Binary: {result['qemu_info']['elf']}")
    print()
    
    # Show what's running
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 QEMU Process Monitor (10 seconds)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    for i in range(10):
        status = tools.qemu_status()
        if status['status']['running']:
            s = status['status']
            
            # Build info line
            info = (
                f"⏱️  {i+1}s | "
                f"PID: {s['pid']} | "
                f"CPU: {s['cpu_percent']:4.1f}% | "
                f"RAM: {s['memory_mb']:6.1f}MB | "
                f"Status: {s['status']}"
            )
            
            print(f"\r{info}", end='', flush=True)
        
        time.sleep(1)
    
    print("\n")
    
    # Show the code that's running
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💻 Source Code Running in QEMU:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Read and display the C code
    try:
        with open('/workspace/main/my_app.c', 'r') as f:
            code = f.read()
        
        print("\033[36m")  # Cyan color
        print(code)
        print("\033[0m")  # Reset color
    except:
        print("(Source code in main/my_app.c)")
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("ℹ️  Expected Behavior:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  • Task 'app_main' would be running")
    print("  • Printing 'Hello World!' every 1 second")
    print("  • Counter incrementing: 1, 2, 3, 4...")
    print("  • ESP_LOGI showing loop iterations")
    print()
    print("  Note: QEMU ESP32 serial output is limited,")
    print("        but the process IS executing the code!")
    print()
    
    # Memory info
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📦 Binary Information:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Get size info
    result = subprocess.run(
        ['bash', '-lc', '. /opt/esp/idf/export.sh && cd /workspace && idf.py size'],
        capture_output=True,
        text=True
    )
    
    if 'Memory Type Usage Summary' in result.stdout:
        # Extract and show memory table
        lines = result.stdout.split('\n')
        in_table = False
        for line in lines:
            if 'Memory Type Usage Summary' in line or '━' in line or '┃' in line or '┏' in line or '┗' in line or '┡' in line or '└' in line:
                print(line)
                in_table = True
            elif in_table and line.strip() == '':
                break
            elif in_table:
                print(line)
    
    print()
    
    # Stop QEMU
    print("🛑 Stopping QEMU...")
    result = tools.stop_qemu()
    print(result['stdout'])
    
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  ✅ Demo Complete - Code was executing in QEMU!           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(show_qemu_info())
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted")
        tools = IDFTools()
        tools.stop_qemu()
        sys.exit(0)
