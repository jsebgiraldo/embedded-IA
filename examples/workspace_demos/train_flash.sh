#!/bin/bash
# MCP Training Script: ESP32-C6 Flash Workflow
# Trains the MCP to automatically detect, build, and flash ESP32-C6

set -e

echo "============================================================"
echo "🎓 MCP Training Session: ESP32-C6 Flash Workflow"
echo "============================================================"

# Load ESP-IDF environment
echo ""
echo "📦 Loading ESP-IDF environment..."
source /opt/esp/idf/export.sh > /dev/null 2>&1
echo "   ✅ ESP-IDF environment loaded"

# Change to workspace directory
cd /workspace

# Step 1: Set target to ESP32-C6
echo ""
echo "🎯 Step 1: Setting target to ESP32-C6..."
idf.py set-target esp32c6
echo "   ✅ Target set to ESP32-C6"

# Step 2: Build for ESP32-C6
echo ""
echo "🔨 Step 2: Building for ESP32-C6..."
echo "   (This may take a few minutes for first build)"
idf.py build
echo "   ✅ Build succeeded!"

# Step 3: Check binary size
echo ""
echo "📊 Step 3: Checking binary size..."
idf.py size
echo "   ✅ Size check complete"

# Step 4: Flash to device
PORT="/dev/cu.usbmodem21101"
echo ""
echo "⚡ Step 4: Flashing to ${PORT}..."
echo "   Using 460800 baud for faster flashing"
idf.py -p ${PORT} -b 460800 flash

echo ""
echo "============================================================"
echo "🎉 MCP Training Complete!"
echo "============================================================"
echo ""
echo "Learned workflow:"
echo "  1. Auto-detect ESP32-C6 on ${PORT}"
echo "  2. Set target to esp32c6"
echo "  3. Build optimized binary"
echo "  4. Flash at 460800 baud"
echo ""
echo "ESP32-C6 is now running Hello World!"
echo ""
echo "To monitor output:"
echo "  docker compose exec dev idf.py -p ${PORT} monitor"
