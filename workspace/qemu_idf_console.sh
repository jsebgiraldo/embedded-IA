#!/bin/bash
# Run ESP32 Hello World in QEMU with console output using idf.py qemu

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    ESP32 Hello World - QEMU Console (idf.py qemu)         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Load ESP-IDF environment
. /opt/esp/idf/export.sh > /dev/null 2>&1

cd /workspace

echo "🎯 Setting target to ESP32..."
idf.py set-target esp32 > /dev/null 2>&1

echo "🔨 Building project..."
idf.py build > /dev/null 2>&1

if [ ! -f build/my_app.elf ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""
echo "🎮 Starting QEMU with console..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📺 Console Output (press Ctrl+C to stop):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run QEMU using idf.py (this has proper console support)
timeout 15 idf.py qemu 2>&1 || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ QEMU session finished"
echo ""
echo "💡 Tip: Run 'idf.py qemu' directly for interactive session"
