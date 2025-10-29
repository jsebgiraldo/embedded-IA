#!/bin/bash
# Run ESP32 in QEMU with visible console output

echo "🎮 ESP32 Hello World en QEMU con Consola Visible"
echo "=================================================="
echo ""

# Load ESP-IDF
. /opt/esp/idf/export.sh > /dev/null 2>&1

cd /workspace

# Kill any existing QEMU
pkill -9 qemu-system-xtensa 2>/dev/null

echo "🔨 Building for ESP32..."
# Backup original
if [ ! -f main/my_app.c.bak ]; then
    cp main/my_app.c main/my_app.c.bak
fi

# Use QEMU-optimized version
cp main/qemu_demo.c main/my_app.c

idf.py set-target esp32 > /dev/null 2>&1
idf.py build > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""
echo "🚀 Starting QEMU with console output..."
echo "=================================================="
echo ""
echo "📺 Console Output (Ctrl+C to stop):"
echo "=================================================="

# Run QEMU with stdout redirected
qemu-system-xtensa \
    -nographic \
    -machine esp32 \
    -drive file=build/my_app.bin,if=mtd,format=raw \
    -serial mon:stdio \
    2>&1 | grep --line-buffered -v "Warning:" | head -50

echo ""
echo "=================================================="
echo "✅ QEMU stopped"
echo ""

# Restore original
if [ -f main/my_app.c.bak ]; then
    mv main/my_app.c.bak main/my_app.c
fi
