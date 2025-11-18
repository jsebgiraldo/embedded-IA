#!/usr/bin/env python3
"""
Test Real Workflow - API Version
Envía eventos directamente a la API del dashboard usando requests
"""

import asyncio
import requests
import time
from datetime import datetime


class DashboardClient:
    """Cliente para enviar eventos al dashboard"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def emit_log(self, level: str, message: str, agent_id: str, job_id: int = None):
        """Emitir log al dashboard"""
        try:
            response = requests.post(f"{self.base_url}/api/logs", json={
                "level": level,
                "message": message,
                "agent_id": agent_id,
                "job_id": job_id,
                "meta_data": None
            }, timeout=5)
            response.raise_for_status()
        except Exception as e:
            print(f"  ✗ Error enviando log: {e}")
    
    async def update_agent_status(self, agent_id: str, status: str):
        """Actualizar estado de agente"""
        try:
            response = requests.put(
                f"{self.base_url}/api/agents/{agent_id}/status", 
                json={"status": status}, 
                timeout=5
            )
            response.raise_for_status()
            print(f"  ✓ Agent {agent_id}: {status}")
        except Exception as e:
            print(f"  ✗ Error actualizando agente {agent_id}: {e}")
    
    async def create_job(self, job_type: str, agent_id: str, status: str = "running"):
        """Crear un nuevo job"""
        try:
            response = requests.post(f"{self.base_url}/api/jobs", json={
                "job_type": job_type,
                "status": status,
                "agent_id": agent_id,
                "model_used": "qwen3-coder:latest"
            }, timeout=5)
            job_id = response.json()["id"]
            # Iniciar el job automáticamente
            await self.update_job(job_id, "running")
            return job_id
        except Exception as e:
            print(f"Error creando job: {e}")
            return None
    
    async def update_job(self, job_id: int, status: str, duration: float = None):
        """Actualizar estado de job"""
        try:
            if status == "completed":
                requests.post(f"{self.base_url}/api/jobs/{job_id}/complete", json={
                    "success": True
                }, timeout=5)
            elif status == "running":
                requests.post(f"{self.base_url}/api/jobs/{job_id}/start", timeout=5)
        except Exception as e:
            print(f"Error actualizando job: {e}")
    
    async def close(self):
        """Cerrar cliente"""
        pass  # requests no necesita cerrar conexión


async def simulate_real_workflow():
    """Simula un workflow real de desarrollo ESP32"""
    
    print("\n" + "="*80)
    print("🚀 ESP32 REAL WORKFLOW TEST - Ciclo Completo de Desarrollo")
    print("="*80)
    print("\n📌 Escenario: Proyecto ESP32 con error de compilación real")
    print("   - Error: Variable no declarada")
    print("   - Agentes: Build → Developer → Build → Test")
    print("   - Tiempo estimado: ~2 minutos")
    print("\n🌐 Dashboard: http://localhost:8000")
    print("   Verás los eventos en tiempo real mientras se ejecuta el workflow\n")
    
    input("Presiona Enter para iniciar el workflow real... ")
    
    client = DashboardClient()
    start_time = time.time()
    
    # Crear job
    job_id = await client.create_job("esp32_fix_workflow", "build", "running")
    if not job_id:
        print("❌ Error creando job")
        return
    
    print(f"\n✅ Job creado: {job_id}\n")
    
    # ========================================================================
    # FASE 1: INTENTAR BUILD - FALLA POR ERROR
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 1: BUILD INICIAL - Detectando errores")
    print("="*80 + "\n")
    
    await client.update_agent_status("build", "active")
    await client.emit_log("INFO", "🔨 Iniciando compilación del proyecto...", "build", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("INFO", "📦 Configurando entorno de compilación ESP-IDF", "build", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "🔍 Analizando dependencias del proyecto", "build", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "⚙️  Compilando archivos fuente (main.c, wifi.c, gpio.c)", "build", job_id)
    await asyncio.sleep(2)
    
    # Error encontrado
    await client.emit_log("ERROR", "❌ Error de compilación detectado!", "build", job_id)
    await asyncio.sleep(0.5)
    
    error_detail = """main/main.c:45:5: error: 'led_state' undeclared (first use in this function)
     led_state = !led_state;
     ^~~~~~~~~
main/main.c:45:5: note: each undeclared identifier is reported only once"""
    
    await client.emit_log("ERROR", error_detail, "build", job_id)
    await client.update_agent_status("build", "error")
    print("❌ Build falló - Error en código fuente")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 2: ANÁLISIS DEL DESARROLLADOR
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 2: ANÁLISIS - Developer Agent investigando el error")
    print("="*80 + "\n")
    
    await client.update_agent_status("build", "idle")
    await client.update_agent_status("developer", "active")
    
    await client.emit_log("INFO", "👨‍💻 Developer Agent: Analizando error de compilación", "developer", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("INFO", "🔍 Identificando línea problemática: main.c:45", "developer", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("WARNING", "⚠️  Variable 'led_state' usada pero no declarada", "developer", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("SUCCESS", "✅ Causa raíz identificada: Falta declaración de variable", "developer", job_id)
    print("✅ Developer: Error analizado - Variable no declarada")
    await asyncio.sleep(1.5)
    
    # ========================================================================
    # FASE 3: APLICAR FIX AUTOMÁTICO
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 3: FIX - Aplicando corrección automática con LLM")
    print("="*80 + "\n")
    
    await client.emit_log("INFO", "🔧 Generando fix con LLM (qwen3-coder:latest)", "developer", job_id)
    await asyncio.sleep(2)
    
    await client.emit_log("INFO", "🤖 LLM: Analizando código y generando solución...", "developer", job_id)
    await asyncio.sleep(3)
    
    fix_code = """// Fix generado por LLM:
static bool led_state = false;  // Estado del LED (on/off)

// Código corregido:
led_state = !led_state;
gpio_set_level(LED_PIN, led_state);"""
    
    await client.emit_log("SUCCESS", f"✨ Fix generado:\n{fix_code}", "developer", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("SUCCESS", "💾 Cambios aplicados a main/main.c", "developer", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("SUCCESS", "✅ Fix aplicado correctamente (Confianza: 98%)", "developer", job_id)
    await client.update_agent_status("developer", "idle")
    print("✅ Developer: Fix aplicado exitosamente")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 4: REBUILD - VERIFICAR FIX
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 4: REBUILD - Verificando que el fix funcionó")
    print("="*80 + "\n")
    
    await client.update_agent_status("build", "active")
    await client.emit_log("INFO", "🔨 Recompilando proyecto con fix aplicado...", "build", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "🧹 Limpiando build anterior (idf.py clean)", "build", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "⚙️  Recompilando archivos modificados", "build", job_id)
    await asyncio.sleep(2)
    
    await client.emit_log("INFO", "🔗 Enlazando bibliotecas (esp-idf, newlib, freertos)", "build", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("INFO", "📦 Generando binario final", "build", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("SUCCESS", "✅ Compilación exitosa!", "build", job_id)
    await client.emit_log("INFO", "📦 Binario generado: build/esp32_app.bin (245 KB)", "build", job_id)
    await client.update_agent_status("build", "idle")
    print("✅ Build: Compilación exitosa después del fix")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 5: VALIDACIÓN Y TESTING
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 5: VALIDACIÓN - Test Agent verificando el resultado")
    print("="*80 + "\n")
    
    await client.update_agent_status("test", "active")
    await client.emit_log("INFO", "🧪 Iniciando validación del código corregido", "test", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "📋 Verificando declaraciones de variables", "test", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("SUCCESS", "✅ Todas las variables están declaradas correctamente", "test", job_id)
    await asyncio.sleep(1)
    
    await client.emit_log("INFO", "🔬 Ejecutando test de sintaxis ESP-IDF", "test", job_id)
    await asyncio.sleep(1.5)
    
    await client.emit_log("SUCCESS", "✅ Todos los tests pasaron exitosamente", "test", job_id)
    await client.emit_log("INFO", "📊 Cobertura: Variables (100%), Sintaxis (100%)", "test", job_id)
    await client.update_agent_status("test", "idle")
    print("✅ Test: Validación completada - Código listo para flash")
    await asyncio.sleep(2)
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("✨ WORKFLOW COMPLETADO EXITOSAMENTE")
    print("="*80 + "\n")
    
    duration = time.time() - start_time
    await client.update_job(job_id, "completed", duration)
    await client.emit_log("SUCCESS", "🎉 Workflow completado exitosamente!", "system", job_id)
    
    summary = f"""📊 RESUMEN DEL WORKFLOW:

✅ Error detectado:     Variable 'led_state' no declarada
✅ Análisis:           Causa raíz identificada
✅ Fix generado:       Declaración agregada con LLM (qwen3-coder)
✅ Build:              Compilación exitosa (245 KB)
✅ Validación:         Todos los tests pasaron

⏱️  Tiempo total:       {duration:.1f} segundos
🤖 Agentes usados:     Build, Developer, Test
💾 Archivos modificados: main/main.c
📈 Tasa de éxito:      100%"""
    
    await client.emit_log("INFO", summary, "system", job_id)
    
    print(summary)
    print("\n" + "="*80)
    print("📊 Revisa el dashboard para ver:")
    print("   • Timeline completo del workflow")
    print("   • Logs detallados por agente")
    print("   • Métricas de tiempo y éxito")
    print("   • Cambios de estado en tiempo real")
    print("="*80 + "\n")
    
    await asyncio.sleep(2)
    await client.close()
    print("✅ Cliente cerrado\n")


if __name__ == "__main__":
    try:
        asyncio.run(simulate_real_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrumpido por el usuario\n")
