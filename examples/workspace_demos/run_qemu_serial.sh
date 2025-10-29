#!/bin/bash
# Run QEMU with proper serial output redirection

echo "🎮 Starting ESP32 Hello World in QEMU"
echo "======================================"

# Load ESP-IDF
. /opt/esp/idf/export.sh > /dev/null 2>&1

cd /workspace

# Kill any existing QEMU
pkill -9 qemu-system-xtensa 2>/dev/null

echo ""
echo "🔨 Building for ESP32..."
idf.py set-target esp32 > /dev/null 2>&1
idf.py build > /dev/null 2>&1

if [ ! -f build/my_app.elf ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""
echo "🚀 Starting QEMU simulation..."
echo "======================================"

# Create named pipe for serial output
SERIAL_PIPE="/tmp/qemu_serial_$$"
rm -f "$SERIAL_PIPE"
mkfifo "$SERIAL_PIPE"

# Start QEMU with serial output to pipe
qemu-system-xtensa \
    -M esp32 \
    -nographic \
    -serial pipe:"$SERIAL_PIPE" \
    -kernel build/my_app.elf \
    > /dev/null 2>&1 &

QEMU_PID=$!
echo "✅ QEMU started (PID: $QEMU_PID)"

# Read from pipe with timeout
echo ""
echo "📺 Program Output:"
echo "======================================"

timeout 10s cat "$SERIAL_PIPE" 2>/dev/null || true

echo ""
echo "======================================"

# Cleanup
kill $QEMU_PID 2>/dev/null
rm -f "$SERIAL_PIPE"

echo "✅ QEMU stopped"
