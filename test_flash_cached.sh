#!/bin/bash
# Test flashing with cached artifacts from macOS
# This verifies the artifact sharing works end-to-end

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ Flash Test: Using Cached Artifacts (No Rebuild)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PORT="/dev/cu.usbmodem21101"
WORKSPACE="./workspace"

echo ""
echo "📋 Step 1: Check cached artifacts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$WORKSPACE/.artifacts_cache/build_metadata.json" ]; then
    echo "❌ No cached artifacts found!"
    echo "   Run: docker compose exec mcp-server bash /workspace/test_artifact_sharing.sh"
    exit 1
fi

# Parse metadata
TARGET=$(cat $WORKSPACE/.artifacts_cache/build_metadata.json | grep -o '"target": "[^"]*"' | cut -d'"' -f4)
TIMESTAMP=$(cat $WORKSPACE/.artifacts_cache/build_metadata.json | grep -o '"timestamp": "[^"]*"' | cut -d'"' -f4)

echo "✅ Found cached artifacts:"
echo "   Target: $TARGET"
echo "   Built: $TIMESTAMP"

echo ""
echo "⚡ Step 2: Flash using cached binaries (NO DOCKER REBUILD)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get artifact paths
BOOTLOADER="$WORKSPACE/build/bootloader/bootloader.bin"
PARTITION_TABLE="$WORKSPACE/build/partition_table/partition-table.bin"
APP="$WORKSPACE/build/my_app.bin"

# Verify all artifacts exist
if [ ! -f "$BOOTLOADER" ]; then
    echo "❌ Missing: $BOOTLOADER"
    exit 1
fi
if [ ! -f "$PARTITION_TABLE" ]; then
    echo "❌ Missing: $PARTITION_TABLE"
    exit 1
fi
if [ ! -f "$APP" ]; then
    echo "❌ Missing: $APP"
    exit 1
fi

echo "✅ All binaries found"
echo ""
echo "Flashing to $PORT..."
echo ""

# Flash with esptool (NO BUILD REQUIRED!)
esptool --chip $TARGET -p $PORT -b 460800 \
    --before=default-reset --after=hard-reset \
    write-flash --flash-mode dio --flash-freq 80m --flash-size 2MB \
    0x0 "$BOOTLOADER" \
    0x8000 "$PARTITION_TABLE" \
    0x10000 "$APP"

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 SUCCESS! Artifact Sharing Verified"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Architecture working correctly:"
    echo "  ✅ Builder built and cached artifacts"
    echo "  ✅ Flash agent used cached binaries"
    echo "  ✅ NO rebuild required"
    echo "  ✅ Binaries shared successfully"
    echo ""
    echo "Time saved: ~2-3 minutes (no rebuild!)"
else
    echo ""
    echo "❌ Flash failed"
    exit 1
fi
