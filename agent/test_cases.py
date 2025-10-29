"""
Test cases with intentional errors for Developer Agent validation
Each case contains buggy ESP32 code that should be auto-fixed by LLM
"""

from typing import Dict, List, Any


# Test Case 1: Missing GPIO header
CASE_1_MISSING_INCLUDE = {
    "name": "missing_gpio_include",
    "description": "Missing driver/gpio.h include",
    "difficulty": "easy",
    "error_type": "missing_include",
    "buggy_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define LED_PIN GPIO_NUM_2

void app_main(void)
{
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
    
    while(1) {
        gpio_set_level(LED_PIN, 1);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        gpio_set_level(LED_PIN, 0);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}
""",
    "expected_error": "implicit declaration of function 'gpio_set_direction'",
    "expected_fix": "Add #include \"driver/gpio.h\"",
    "correct_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"

#define LED_PIN GPIO_NUM_2

void app_main(void)
{
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
    
    while(1) {
        gpio_set_level(LED_PIN, 1);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        gpio_set_level(LED_PIN, 0);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}
""",
}

# Test Case 2: Wrong GPIO type
CASE_2_WRONG_TYPE = {
    "name": "wrong_gpio_type",
    "description": "Using int instead of gpio_num_t",
    "difficulty": "medium",
    "error_type": "wrong_type",
    "buggy_code": """#include <stdio.h>
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void configure_led(int pin)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << pin),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
}

void app_main(void)
{
    int led = 2;  // Should be gpio_num_t
    configure_led(led);
    
    while(1) {
        gpio_set_level(led, 1);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        gpio_set_level(led, 0);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}
""",
    "expected_error": "incompatible integer to pointer conversion",
    "expected_fix": "Change 'int led' to 'gpio_num_t led' and 'int pin' to 'gpio_num_t pin'",
    "correct_code": """#include <stdio.h>
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void configure_led(gpio_num_t pin)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << pin),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
}

void app_main(void)
{
    gpio_num_t led = GPIO_NUM_2;
    configure_led(led);
    
    while(1) {
        gpio_set_level(led, 1);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        gpio_set_level(led, 0);
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}
""",
}

# Test Case 3: Missing WiFi headers
CASE_3_WIFI_MISSING_HEADERS = {
    "name": "wifi_missing_headers",
    "description": "Missing ESP WiFi headers",
    "difficulty": "medium",
    "error_type": "missing_include",
    "buggy_code": """#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

#define WIFI_SSID "MyNetwork"
#define WIFI_PASS "password123"

static EventGroupHandle_t wifi_event_group;
const int WIFI_CONNECTED_BIT = BIT0;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                              int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    }
}

void wifi_init(void)
{
    wifi_event_group = xEventGroupCreate();
    
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
}

void app_main(void)
{
    wifi_init();
}
""",
    "expected_error": "unknown type name 'esp_event_base_t'",
    "expected_fix": "Add #include \"esp_wifi.h\", \"esp_event.h\", \"esp_netif.h\"",
    "correct_code": """#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"

#define WIFI_SSID "MyNetwork"
#define WIFI_PASS "password123"

static EventGroupHandle_t wifi_event_group;
const int WIFI_CONNECTED_BIT = BIT0;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                              int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    }
}

void wifi_init(void)
{
    wifi_event_group = xEventGroupCreate();
    
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
}

void app_main(void)
{
    wifi_init();
}
""",
}

# Test Case 4: FreeRTOS wrong task handle
CASE_4_FREERTOS_TASK_HANDLE = {
    "name": "freertos_task_handle",
    "description": "Wrong type for FreeRTOS task handle",
    "difficulty": "medium",
    "error_type": "wrong_type",
    "buggy_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "MAIN";

void task_a(void *pvParameters)
{
    while(1) {
        ESP_LOGI(TAG, "Task A running");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}

void task_b(void *pvParameters)
{
    while(1) {
        ESP_LOGI(TAG, "Task B running");
        vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
}

void app_main(void)
{
    void *handle_a = NULL;  // Wrong type!
    void *handle_b = NULL;  // Wrong type!
    
    xTaskCreate(task_a, "task_a", 2048, NULL, 5, &handle_a);
    xTaskCreate(task_b, "task_b", 2048, NULL, 5, &handle_b);
    
    ESP_LOGI(TAG, "Tasks created");
}
""",
    "expected_error": "incompatible pointer types passing",
    "expected_fix": "Change 'void *handle_a' to 'TaskHandle_t handle_a'",
    "correct_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "MAIN";

void task_a(void *pvParameters)
{
    while(1) {
        ESP_LOGI(TAG, "Task A running");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}

void task_b(void *pvParameters)
{
    while(1) {
        ESP_LOGI(TAG, "Task B running");
        vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
}

void app_main(void)
{
    TaskHandle_t handle_a = NULL;
    TaskHandle_t handle_b = NULL;
    
    xTaskCreate(task_a, "task_a", 2048, NULL, 5, &handle_a);
    xTaskCreate(task_b, "task_b", 2048, NULL, 5, &handle_b);
    
    ESP_LOGI(TAG, "Tasks created");
}
""",
}

# Test Case 5: I2C missing header and wrong config
CASE_5_I2C_CONFIG = {
    "name": "i2c_missing_config",
    "description": "Missing I2C header and incomplete config",
    "difficulty": "hard",
    "error_type": "missing_include",
    "buggy_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

#define I2C_MASTER_NUM I2C_NUM_0
#define I2C_MASTER_SDA_IO 21
#define I2C_MASTER_SCL_IO 22
#define I2C_MASTER_FREQ_HZ 100000

static const char *TAG = "I2C";

void i2c_master_init(void)
{
    i2c_config_t conf;
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = I2C_MASTER_SDA_IO;
    conf.scl_io_num = I2C_MASTER_SCL_IO;
    conf.master.clk_speed = I2C_MASTER_FREQ_HZ;
    
    i2c_param_config(I2C_MASTER_NUM, &conf);
    i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
    
    ESP_LOGI(TAG, "I2C initialized");
}

void app_main(void)
{
    i2c_master_init();
}
""",
    "expected_error": "unknown type name 'i2c_config_t'",
    "expected_fix": "Add #include \"driver/i2c.h\" and complete i2c_config_t initialization",
    "correct_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/i2c.h"

#define I2C_MASTER_NUM I2C_NUM_0
#define I2C_MASTER_SDA_IO 21
#define I2C_MASTER_SCL_IO 22
#define I2C_MASTER_FREQ_HZ 100000

static const char *TAG = "I2C";

void i2c_master_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    
    i2c_param_config(I2C_MASTER_NUM, &conf);
    i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
    
    ESP_LOGI(TAG, "I2C initialized");
}

void app_main(void)
{
    i2c_master_init();
}
""",
}

# Test Case 6: NVS Storage missing init
CASE_6_NVS_MISSING_INIT = {
    "name": "nvs_missing_init_and_header",
    "description": "Missing NVS header and nvs_flash_init() call",
    "difficulty": "medium",
    "error_type": "missing_include",
    "buggy_code": """#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "NVS";

void save_wifi_config(const char *ssid, const char *password)
{
    nvs_handle_t nvs_handle;
    esp_err_t err;
    
    err = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error opening NVS");
        return;
    }
    
    nvs_set_str(nvs_handle, "ssid", ssid);
    nvs_set_str(nvs_handle, "password", password);
    nvs_commit(nvs_handle);
    nvs_close(nvs_handle);
    
    ESP_LOGI(TAG, "WiFi config saved");
}

void app_main(void)
{
    save_wifi_config("MyWiFi", "password123");
}
""",
    "expected_error": "unknown type name 'nvs_handle_t'",
    "expected_fix": "Add #include \"nvs_flash.h\" and call nvs_flash_init()",
    "correct_code": """#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "nvs_flash.h"

static const char *TAG = "NVS";

void save_wifi_config(const char *ssid, const char *password)
{
    nvs_handle_t nvs_handle;
    esp_err_t err;
    
    err = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error opening NVS");
        return;
    }
    
    nvs_set_str(nvs_handle, "ssid", ssid);
    nvs_set_str(nvs_handle, "password", password);
    nvs_commit(nvs_handle);
    nvs_close(nvs_handle);
    
    ESP_LOGI(TAG, "WiFi config saved");
}

void app_main(void)
{
    // Initialize NVS
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        err = nvs_flash_init();
    }
    
    save_wifi_config("MyWiFi", "password123");
}
""",
}

# Test Case 7: HTTP Server missing headers
CASE_7_HTTP_SERVER = {
    "name": "http_server_missing_headers",
    "description": "Missing HTTP server headers",
    "difficulty": "hard",
    "error_type": "missing_include",
    "buggy_code": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "HTTP";

esp_err_t hello_get_handler(httpd_req_t *req)
{
    const char* resp_str = "Hello World!";
    httpd_resp_send(req, resp_str, strlen(resp_str));
    return ESP_OK;
}

void start_webserver(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_handle_t server = NULL;
    
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t hello = {
            .uri       = "/hello",
            .method    = HTTP_GET,
            .handler   = hello_get_handler,
            .user_ctx  = NULL
        };
        httpd_register_uri_handler(server, &hello);
        ESP_LOGI(TAG, "HTTP server started");
    }
}

void app_main(void)
{
    start_webserver();
}
""",
    "expected_error": "unknown type name 'httpd_req_t'",
    "expected_fix": "Add #include \"esp_http_server.h\"",
    "correct_code": """#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_http_server.h"

static const char *TAG = "HTTP";

esp_err_t hello_get_handler(httpd_req_t *req)
{
    const char* resp_str = "Hello World!";
    httpd_resp_send(req, resp_str, strlen(resp_str));
    return ESP_OK;
}

void start_webserver(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_handle_t server = NULL;
    
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t hello = {
            .uri       = "/hello",
            .method    = HTTP_GET,
            .handler   = hello_get_handler,
            .user_ctx  = NULL
        };
        httpd_register_uri_handler(server, &hello);
        ESP_LOGI(TAG, "HTTP server started");
    }
}

void app_main(void)
{
    start_webserver();
}
""",
}

# All test cases collection
ALL_TEST_CASES = [
    CASE_1_MISSING_INCLUDE,
    CASE_2_WRONG_TYPE,
    CASE_3_WIFI_MISSING_HEADERS,
    CASE_4_FREERTOS_TASK_HANDLE,
    CASE_5_I2C_CONFIG,
    CASE_6_NVS_MISSING_INIT,
    CASE_7_HTTP_SERVER,
]


def get_test_case(name: str) -> Dict[str, Any]:
    """Get a specific test case by name"""
    for case in ALL_TEST_CASES:
        if case["name"] == name:
            return case
    return None


def get_test_cases_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get all test cases of a specific difficulty"""
    return [case for case in ALL_TEST_CASES if case["difficulty"] == difficulty]


def get_test_cases_by_error_type(error_type: str) -> List[Dict[str, Any]]:
    """Get all test cases of a specific error type"""
    return [case for case in ALL_TEST_CASES if case["error_type"] == error_type]
