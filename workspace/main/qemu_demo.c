#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"

void app_main(void)
{
    // Usar stdout directamente para QEMU
    printf("\n\n");
    printf("========================================\n");
    printf("   ESP32 Hello World in QEMU!         \n");
    printf("========================================\n");
    printf("\n");
    
    // Información del sistema
    printf("Chip: ESP32\n");
    printf("Free heap: %lu bytes\n", (unsigned long)esp_get_free_heap_size());
    printf("\n");
    printf("Starting counter loop...\n");
    printf("========================================\n");
    
    int counter = 0;
    while(1) {
        // Usar printf simple para QEMU
        printf("[%d] Hello World! Counter: %d\n", 
               (int)(xTaskGetTickCount() * portTICK_PERIOD_MS), 
               counter);
        
        counter++;
        
        // Hacer algo de trabajo para generar actividad
        volatile int dummy = 0;
        for(int i = 0; i < 100000; i++) {
            dummy += i;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));
        
        // Flush para asegurar salida en QEMU
        fflush(stdout);
    }
}
