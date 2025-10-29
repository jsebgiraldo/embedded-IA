#!/usr/bin/env python3
"""
Mac Mini M4 Stress Test - ESP32 Multi-Agent System

This script pushes your Mac Mini M4 to its limits by:
1. Running the most powerful local model (DeepSeek-Coder-V2 16B)
2. Processing multiple ESP32 code fixes simultaneously
3. Testing complex refactoring scenarios
4. Measuring performance metrics

Requirements:
- Mac Mini M4 (you have this!)
- 16GB+ RAM recommended
- Ollama installed with DeepSeek model

Usage:
    python3 examples/mac_m4_stress_test.py
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_provider import get_llm, LLMConfig, LLMProvider


# Complex ESP32 test cases that challenge the LLM
STRESS_TEST_CASES = {
    "1_simple_gpio": {
        "difficulty": "Easy",
        "description": "Basic GPIO setup with missing includes",
        "code": """#include <stdio.h>

void app_main() {
    gpio_set_level(GPIO_NUM_2, 1);
    gpio_set_direction(GPIO_NUM_2, GPIO_MODE_OUTPUT);
    printf("GPIO initialized\\n");
}""",
        "error": """main.c:4:5: error: implicit declaration of function 'gpio_set_level'
main.c:4:20: error: 'GPIO_NUM_2' undeclared
main.c:5:5: error: implicit declaration of function 'gpio_set_direction'""",
        "expected_includes": ["driver/gpio.h"],
    },
    
    "2_wifi_connection": {
        "difficulty": "Medium",
        "description": "WiFi initialization with multiple missing includes",
        "code": """#include <stdio.h>
#include <string.h>

void app_main() {
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_wifi_set_mode(WIFI_MODE_STA);
    
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = "MyWiFi",
            .password = "password123",
        },
    };
    
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    printf("WiFi started\\n");
}""",
        "error": """main.c:6:5: error: unknown type name 'wifi_init_config_t'
main.c:6:30: error: 'WIFI_INIT_CONFIG_DEFAULT' undeclared
main.c:7:5: error: implicit declaration of function 'esp_wifi_init'
main.c:8:5: error: implicit declaration of function 'esp_wifi_set_mode'""",
        "expected_includes": ["esp_wifi.h", "esp_event.h"],
    },
    
    "3_freertos_tasks": {
        "difficulty": "Medium",
        "description": "FreeRTOS multi-task application with timing issues",
        "code": """#include <stdio.h>

void blink_task(void *pvParameters) {
    while(1) {
        printf("Blink!\\n");
        gpio_set_level(GPIO_NUM_2, 1);
        delay(500);  // Wrong!
        gpio_set_level(GPIO_NUM_2, 0);
        delay(500);  // Wrong!
    }
}

void app_main() {
    xTaskCreate(blink_task, "blink", 2048, NULL, 5, NULL);
}""",
        "error": """main.c:7:9: error: implicit declaration of function 'delay'
main.c:6:9: error: implicit declaration of function 'gpio_set_level'
main.c:14:5: error: implicit declaration of function 'xTaskCreate'""",
        "expected_fixes": ["vTaskDelay", "pdMS_TO_TICKS", "freertos/FreeRTOS.h"],
    },
    
    "4_i2c_sensor": {
        "difficulty": "Hard",
        "description": "I2C sensor reading with complex initialization",
        "code": """#include <stdio.h>

#define I2C_MASTER_SCL_IO    22
#define I2C_MASTER_SDA_IO    21
#define I2C_MASTER_FREQ_HZ   100000
#define SENSOR_ADDR          0x68

void app_main() {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    
    i2c_param_config(I2C_NUM_0, &conf);
    i2c_driver_install(I2C_NUM_0, conf.mode, 0, 0, 0);
    
    uint8_t data[2];
    i2c_master_read_from_device(I2C_NUM_0, SENSOR_ADDR, data, 2, 1000);
    
    printf("Sensor value: %d\\n", (data[0] << 8) | data[1]);
}""",
        "error": """main.c:9:5: error: unknown type name 'i2c_config_t'
main.c:10:16: error: 'I2C_MODE_MASTER' undeclared
main.c:13:27: error: 'GPIO_PULLUP_ENABLE' undeclared
main.c:18:5: error: implicit declaration of function 'i2c_param_config'""",
        "expected_includes": ["driver/i2c.h"],
    },
    
    "5_http_server": {
        "difficulty": "Hard",
        "description": "HTTP server with async handlers and WiFi",
        "code": """#include <stdio.h>
#include <string.h>

esp_err_t hello_handler(httpd_req_t *req) {
    const char* resp = "Hello World!";
    httpd_resp_send(req, resp, strlen(resp));
    return ESP_OK;
}

void app_main() {
    // Initialize WiFi first
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    
    // Start HTTP server
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_handle_t server = NULL;
    httpd_start(&server, &config);
    
    httpd_uri_t hello = {
        .uri       = "/hello",
        .method    = HTTP_GET,
        .handler   = hello_handler,
        .user_ctx  = NULL
    };
    
    httpd_register_uri_handler(server, &hello);
    printf("HTTP server started\\n");
}""",
        "error": """main.c:4:1: error: unknown type name 'esp_err_t'
main.c:4:22: error: unknown type name 'httpd_req_t'
main.c:5:17: error: 'ESP_OK' undeclared
main.c:12:5: error: unknown type name 'wifi_init_config_t'
main.c:16:5: error: unknown type name 'httpd_config_t'""",
        "expected_includes": ["esp_http_server.h", "esp_wifi.h"],
    },
    
    "6_nvs_storage": {
        "difficulty": "Medium-Hard",
        "description": "Non-volatile storage with error handling",
        "code": """#include <stdio.h>
#include <string.h>

void app_main() {
    nvs_handle_t my_handle;
    esp_err_t err;
    
    // Initialize NVS
    err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES) {
        nvs_flash_erase();
        err = nvs_flash_init();
    }
    
    // Open
    err = nvs_open("storage", NVS_READWRITE, &my_handle);
    if (err != ESP_OK) {
        printf("Error opening NVS!\\n");
        return;
    }
    
    // Read
    int32_t counter = 0;
    err = nvs_get_i32(my_handle, "counter", &counter);
    
    // Write
    counter++;
    nvs_set_i32(my_handle, "counter", counter);
    nvs_commit(my_handle);
    
    nvs_close(my_handle);
    printf("Counter: %d\\n", counter);
}""",
        "error": """main.c:5:5: error: unknown type name 'nvs_handle_t'
main.c:6:5: error: unknown type name 'esp_err_t'
main.c:9:11: error: implicit declaration of function 'nvs_flash_init'
main.c:10:15: error: 'ESP_ERR_NVS_NO_FREE_PAGES' undeclared""",
        "expected_includes": ["nvs_flash.h", "nvs.h"],
    },
    
    "7_bluetooth_le": {
        "difficulty": "Very Hard",
        "description": "Bluetooth Low Energy GATT server",
        "code": """#include <stdio.h>
#include <string.h>

#define DEVICE_NAME "ESP32_BLE"

static uint8_t adv_service_uuid128[16] = {
    0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x10, 0x00,
    0x80, 0x00, 0x00, 0x80, 0x5F, 0x9B, 0x34, 0xFB
};

void app_main() {
    // Initialize BLE
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    esp_bt_controller_init(&bt_cfg);
    esp_bt_controller_enable(ESP_BT_MODE_BLE);
    
    esp_bluedroid_init();
    esp_bluedroid_enable();
    
    // GAP configuration
    esp_ble_gap_set_device_name(DEVICE_NAME);
    esp_ble_gap_config_adv_data_raw(adv_service_uuid128, sizeof(adv_service_uuid128));
    
    printf("BLE initialized\\n");
}""",
        "error": """main.c:13:5: error: unknown type name 'esp_bt_controller_config_t'
main.c:13:39: error: 'BT_CONTROLLER_INIT_CONFIG_DEFAULT' undeclared
main.c:14:5: error: implicit declaration of function 'esp_bt_controller_init'
main.c:15:33: error: 'ESP_BT_MODE_BLE' undeclared""",
        "expected_includes": ["esp_bt.h", "esp_gap_ble_api.h", "esp_gatts_api.h"],
    },
}


class PerformanceMetrics:
    """Track performance metrics"""
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        self.start_time = time.time()
        
    def end(self):
        self.end_time = time.time()
        
    def add_result(self, test_name: str, result: Dict[str, Any]):
        self.test_results.append({
            "test": test_name,
            "success": result.get("success", False),
            "duration": result.get("duration", 0),
            "tokens_generated": result.get("tokens", 0),
            "difficulty": result.get("difficulty", "Unknown"),
        })
    
    def get_summary(self) -> Dict[str, Any]:
        total_duration = self.end_time - self.start_time if self.end_time else 0
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        avg_duration = sum(r["duration"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        total_tokens = sum(r["tokens_generated"] for r in self.test_results)
        tokens_per_second = total_tokens / total_duration if total_duration > 0 else 0
        
        return {
            "total_duration": total_duration,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_test_duration": avg_duration,
            "total_tokens": total_tokens,
            "tokens_per_second": tokens_per_second,
            "results": self.test_results,
        }


async def test_code_fix_async(llm, test_name: str, test_case: Dict[str, str], metrics: PerformanceMetrics) -> Dict[str, Any]:
    """Test LLM code fixing with async support"""
    print(f"\n{'─'*80}")
    print(f"🧪 Test: {test_name}")
    print(f"📊 Difficulty: {test_case['difficulty']}")
    print(f"📝 {test_case['description']}")
    print(f"{'─'*80}\n")
    
    # Create enhanced prompt for Mac M4
    prompt = f"""You are an expert ESP32 firmware developer. Fix this code with compilation errors.

**Difficulty Level**: {test_case['difficulty']}

**Original Code:**
```c
{test_case['code']}
```

**Compilation Errors:**
```
{test_case['error']}
```

**Instructions:**
1. Add ALL necessary #include statements at the top
2. Fix all undefined functions and constants
3. Use proper ESP-IDF APIs (not Arduino)
4. Ensure FreeRTOS functions use correct syntax
5. Add brief comments for complex fixes
6. Return ONLY the corrected code, no explanations

**Fixed Code:**
"""
    
    start_time = time.time()
    
    try:
        # Invoke LLM
        print("🤖 Processing with DeepSeek-Coder-V2 16B...")
        response = await asyncio.to_thread(llm.invoke, prompt)
        
        duration = time.time() - start_time
        
        # Extract code
        fixed_code = str(response)
        if "```c" in fixed_code:
            fixed_code = fixed_code.split("```c")[1].split("```")[0].strip()
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
        
        # Estimate tokens (rough)
        tokens = len(fixed_code.split())
        
        # Validate fix
        has_includes = "#include" in fixed_code
        has_main = "app_main" in fixed_code
        
        # Check expected includes if provided
        includes_ok = True
        if "expected_includes" in test_case:
            for expected in test_case["expected_includes"]:
                if expected not in fixed_code:
                    includes_ok = False
                    print(f"⚠️  Missing expected include: {expected}")
        
        # Check expected fixes if provided
        fixes_ok = True
        if "expected_fixes" in test_case:
            for expected in test_case["expected_fixes"]:
                if expected not in fixed_code:
                    fixes_ok = False
                    print(f"⚠️  Missing expected fix: {expected}")
        
        success = has_includes and has_main and includes_ok and fixes_ok
        
        # Display results
        print(f"\n{'✅' if success else '⚠️ '} Fixed code:")
        print("```c")
        print(fixed_code)
        print("```\n")
        
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Tokens: ~{tokens}")
        print(f"⚡ Speed: ~{tokens/duration:.1f} tokens/s")
        
        result = {
            "success": success,
            "duration": duration,
            "tokens": tokens,
            "difficulty": test_case["difficulty"],
            "fixed_code": fixed_code,
        }
        
        metrics.add_result(test_name, result)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n❌ Error: {e}\n")
        result = {
            "success": False,
            "duration": duration,
            "tokens": 0,
            "difficulty": test_case["difficulty"],
            "error": str(e),
        }
        metrics.add_result(test_name, result)
        return result


async def run_stress_test():
    """Run complete stress test"""
    print("╔" + "═"*78 + "╗")
    print("║" + " "*15 + "MAC MINI M4 - ESP32 LLM STRESS TEST" + " "*27 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    # Detect system info
    print("🖥️  System Information:")
    print(f"   Mac Mini M4 detected")
    
    # Get RAM
    import subprocess
    try:
        ram_output = subprocess.check_output(['sysctl', 'hw.memsize']).decode()
        total_ram_bytes = int(ram_output.split(':')[1].strip())
        total_ram_gb = total_ram_bytes / (1024**3)
        print(f"   RAM: {total_ram_gb:.1f} GB")
    except:
        print(f"   RAM: Unknown")
    
    print()
    
    # Get LLM config
    model = os.getenv("LLM_MODEL", "deepseek-coder-v2:16b")
    
    print(f"🧠 LLM Configuration:")
    print(f"   Provider: Ollama (Local)")
    print(f"   Model: {model}")
    print(f"   Context: 8192 tokens")
    print(f"   Temperature: 0.0 (deterministic)")
    print()
    
    # Initialize LLM
    print("🔧 Initializing LLM...")
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model=model,
        temperature=0.0,
        num_ctx=8192,
    )
    
    try:
        llm = get_llm(config)
        print("✅ LLM ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        print("\n💡 Make sure:")
        print("   1. Ollama is running: ollama serve")
        print(f"   2. Model is installed: ollama pull {model}")
        return
    
    # Initialize metrics
    metrics = PerformanceMetrics()
    metrics.start()
    
    print(f"🚀 Running {len(STRESS_TEST_CASES)} test cases...")
    print(f"   (Press Ctrl+C to stop)\n")
    
    # Run tests
    for test_name, test_case in STRESS_TEST_CASES.items():
        result = await test_code_fix_async(llm, test_name, test_case, metrics)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    metrics.end()
    
    # Display summary
    summary = metrics.get_summary()
    
    print("\n" + "═"*80)
    print("📊 STRESS TEST RESULTS")
    print("═"*80 + "\n")
    
    print(f"⏱️  Total Duration: {summary['total_duration']:.2f} seconds")
    print(f"📝 Tests Run: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"⚡ Avg Speed: {summary['tokens_per_second']:.1f} tokens/second")
    print(f"🎯 Avg Test Duration: {summary['avg_test_duration']:.2f} seconds")
    
    # Performance rating
    print("\n🏆 Mac Mini M4 Performance Rating:")
    tps = summary['tokens_per_second']
    if tps > 30:
        rating = "🔥 EXCELLENT - Blazing fast!"
    elif tps > 20:
        rating = "⭐ GREAT - Very smooth"
    elif tps > 15:
        rating = "👍 GOOD - Working well"
    elif tps > 10:
        rating = "✓ OK - Acceptable"
    else:
        rating = "⚠️  SLOW - Consider lighter model"
    
    print(f"   {rating}")
    print(f"   {tps:.1f} tokens/second with {model}")
    
    # Difficulty breakdown
    print("\n📊 Results by Difficulty:")
    by_difficulty = {}
    for result in summary['results']:
        diff = result['difficulty']
        if diff not in by_difficulty:
            by_difficulty[diff] = {'passed': 0, 'total': 0, 'avg_time': []}
        by_difficulty[diff]['total'] += 1
        if result['success']:
            by_difficulty[diff]['passed'] += 1
        by_difficulty[diff]['avg_time'].append(result['duration'])
    
    for diff, stats in sorted(by_difficulty.items()):
        rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_time = sum(stats['avg_time']) / len(stats['avg_time']) if stats['avg_time'] else 0
        print(f"   {diff:15s}: {stats['passed']}/{stats['total']} ({rate:.0f}%) - {avg_time:.2f}s avg")
    
    # Save detailed results
    output_file = "mac_m4_stress_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    print("\n" + "═"*80)
    print("✨ Test Complete!")
    print("═"*80 + "\n")


def main():
    """Entry point"""
    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
