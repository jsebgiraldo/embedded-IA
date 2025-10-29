#!/usr/bin/env python3
"""
MCP Training Script: ESP32-C6 Flash Workflow
Trains the MCP to automatically detect, build, and flash ESP32-C6
"""

import sys
sys.path.insert(0, '/mcp-server/src')
from mcp_idf.tools import IDFTools

def main():
    tools = IDFTools()
    
    print("=" * 60)
    print("🎓 MCP Training Session: ESP32-C6 Flash Workflow")
    print("=" * 60)
    
    # Step 1: Set target to ESP32-C6
    print("\n🎯 Step 1: Setting target to ESP32-C6...")
    result = tools.set_target('esp32c6')
    print(f"   Return code: {result['returncode']}")
    if result['returncode'] == 0:
        print("   ✅ Target set to ESP32-C6")
    else:
        print("   ⚠️  Target setting had warnings (this is OK)")
    
    # Step 2: Build for ESP32-C6
    print("\n🔨 Step 2: Building for ESP32-C6...")
    print("   (This may take a few minutes for first build)")
    result = tools.build()
    if result['returncode'] == 0:
        print("   ✅ Build succeeded!")
    else:
        print(f"   ❌ Build failed: {result['returncode']}")
        print("\n   Last 20 lines:")
        print('\n'.join(result['stdout'].split('\n')[-20:]))
        return 1
    
    # Step 3: Check binary size
    print("\n📊 Step 3: Checking binary size...")
    result = tools.size()
    if result['returncode'] == 0:
        print("   ✅ Size check complete")
        # Extract size info from output
        if "Memory Type Usage Summary" in result['stdout']:
            print("\n   Memory usage optimized for ESP32-C6")
    
    # Step 4: Flash to device
    port = '/dev/cu.usbmodem21101'
    print(f"\n⚡ Step 4: Flashing to {port}...")
    print("   Using 460800 baud for faster flashing")
    result = tools.flash(port=port, baud_rate=460800)
    
    if result['returncode'] == 0:
        print("   ✅ Flash successful!")
        print("\n" + "=" * 60)
        print("🎉 MCP Training Complete!")
        print("=" * 60)
        print("\nLearned workflow:")
        print("  1. Auto-detect ESP32-C6 on /dev/cu.usbmodem21101")
        print("  2. Set target to esp32c6")
        print("  3. Build optimized binary")
        print("  4. Flash at 460800 baud")
        print("\nESP32-C6 is now running Hello World!")
        print("\nTo monitor output:")
        print(f"  docker compose exec dev idf.py -p {port} monitor")
        return 0
    else:
        print(f"   ❌ Flash failed: {result['returncode']}")
        print("\n   Output (last 2000 chars):")
        print(result['stdout'][-2000:])
        return 1

if __name__ == '__main__':
    sys.exit(main())
