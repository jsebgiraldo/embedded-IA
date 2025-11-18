#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"

static const char *TAG = "HelloWorld";

void app_main(void)
{
    printf("\n");
    printf("====================================\n");
    printf("   ESP32 - Hello World Program!    \n");
    printf("====================================\n");
    printf("\n");
    
    ESP_LOGI(TAG, "Hello from ESP32!");
    ESP_LOGI(TAG, "Free heap: %lu bytes", esp_get_free_heap_size());
    ESP_LOGI(TAG, "Chip model: %s", CONFIG_IDF_TARGET);
    
    int counter = 0;
    while(1) {
        printf("Hello World! Counter: %d\n", counter++);
        ESP_LOGI(TAG, "Loop iteration: %d", counter);
        vTaskDelay(pdMS_TO_TICKS(1000)); // Wait 1 second
    }
}
