#!/usr/bin/env python3
"""
Test Real Workflow - Simple Version
Workflow real ESP32 sin dependencias de LangChain
"""

import asyncio
import sys
from pathlib import Path

# Solo importar lo necesario
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from event_emitter import EventEmitter, EventType, Event

# Crear instancia global
event_emitter = EventEmitter()


async def emit_log(level: str, message: str, agent_id: str, job_id: int = None):
    """Helper para emitir logs"""
    event = Event(
        event_type=EventType.LOG_ENTRY,
        data={
            "level": level,
            "message": message,
        },
        agent_id=agent_id,
        job_id=job_id
    )
    await event_emitter.emit(event)


async def emit_job_progress(job_id: int, phase: str, progress: int, message: str):
    """Helper para emitir progreso de job"""
    event = Event(
        event_type=EventType.JOB_PROGRESS,
        data={
            "phase": phase,
            "progress": progress,
            "message": message
        },
        job_id=job_id
    )
    await event_emitter.emit(event)


async def emit_agent_status(agent_id: str, status: str):
    """Helper para emitir cambios de status de agente"""
    event = Event(
        event_type=EventType.AGENT_STATUS_CHANGED,
        data={
            "status": status
        },
        agent_id=agent_id
    )
    await event_emitter.emit(event)


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
    
    # Start event emitter
    await event_emitter.start()
    print("\n✅ Event emitter started\n")
    
    job_id = 200
    
    # ========================================================================
    # FASE 1: INTENTAR BUILD - FALLA POR ERROR
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 1: BUILD INICIAL - Detectando errores")
    print("="*80 + "\n")
    
    await emit_agent_status("build", "active")
    await emit_log("INFO", "🔨 Iniciando compilación del proyecto...", "build", job_id)
    await emit_job_progress(job_id, "BUILD", 0, "Configurando entorno de compilación")
    await asyncio.sleep(1.5)
    
    await emit_job_progress(job_id, "BUILD", 20, "Analizando dependencias")
    await asyncio.sleep(1)
    
    await emit_job_progress(job_id, "BUILD", 40, "Compilando archivos fuente...")
    await asyncio.sleep(2)
    
    # Error encontrado
    await emit_log("ERROR", "❌ Error de compilación detectado!", "build", job_id)
    await asyncio.sleep(0.5)
    
    error_detail = """main/main.c:45:5: error: 'led_state' undeclared (first use in this function)
     led_state = !led_state;
     ^~~~~~~~~
main/main.c:45:5: note: each undeclared identifier is reported only once"""
    
    await emit_log("ERROR", f"Detalles del error: {error_detail}", "build", job_id)
    await emit_job_progress(job_id, "BUILD", 50, "Compilación falló - Error detectado")
    
    await emit_agent_status("build", "error")
    print("❌ Build falló - Error en código fuente")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 2: ANÁLISIS DEL DESARROLLADOR
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 2: ANÁLISIS - Developer Agent investigando el error")
    print("="*80 + "\n")
    
    await emit_agent_status("build", "idle")
    await emit_agent_status("developer", "active")
    
    await emit_log("INFO", "👨‍💻 Developer Agent: Analizando error de compilación", "developer", job_id)
    await emit_job_progress(job_id, "ANALYZE", 0, "Leyendo logs de compilación")
    await asyncio.sleep(1.5)
    
    await emit_log("INFO", "🔍 Identificando línea problemática: main.c:45", "developer", job_id)
    await emit_job_progress(job_id, "ANALYZE", 30, "Buscando contexto del código")
    await asyncio.sleep(1.5)
    
    await emit_log("WARNING", "⚠️  Variable 'led_state' usada pero no declarada", "developer", job_id)
    await emit_job_progress(job_id, "ANALYZE", 60, "Generando diagnóstico")
    await asyncio.sleep(1)
    
    await emit_log("SUCCESS", "✅ Causa raíz identificada: Falta declaración de variable", "developer", job_id)
    await emit_job_progress(job_id, "ANALYZE", 100, "Análisis completado")
    print("✅ Developer: Error analizado - Variable no declarada")
    await asyncio.sleep(1.5)
    
    # ========================================================================
    # FASE 3: APLICAR FIX AUTOMÁTICO
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 3: FIX - Aplicando corrección automática")
    print("="*80 + "\n")
    
    await emit_log("INFO", "🔧 Generando fix con LLM (qwen3-coder:latest)", "developer", job_id)
    await emit_job_progress(job_id, "FIX", 0, "Conectando con modelo LLM")
    await asyncio.sleep(2)
    
    await emit_log("INFO", "🤖 LLM: Analizando código y generando solución...", "developer", job_id)
    await emit_job_progress(job_id, "FIX", 25, "Generando código corregido")
    await asyncio.sleep(3)
    
    fix_msg = "✨ Fix generado: Agregada declaración 'static bool led_state = false;'"
    await emit_log("SUCCESS", fix_msg, "developer", job_id)
    await emit_job_progress(job_id, "FIX", 60, "Aplicando cambios al código")
    await asyncio.sleep(1.5)
    
    await emit_log("SUCCESS", "💾 Cambios aplicados a main/main.c", "developer", job_id)
    await emit_job_progress(job_id, "FIX", 90, "Verificando sintaxis")
    await asyncio.sleep(1)
    
    await emit_log("SUCCESS", "✅ Fix aplicado correctamente (Confianza: 98%)", "developer", job_id)
    await emit_job_progress(job_id, "FIX", 100, "Fix completado")
    
    await emit_agent_status("developer", "idle")
    print("✅ Developer: Fix aplicado exitosamente")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 4: REBUILD - VERIFICAR FIX
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 4: REBUILD - Verificando que el fix funcionó")
    print("="*80 + "\n")
    
    await emit_agent_status("build", "active")
    await emit_log("INFO", "🔨 Recompilando proyecto con fix aplicado...", "build", job_id)
    await emit_job_progress(job_id, "REBUILD", 0, "Limpiando build anterior")
    await asyncio.sleep(1)
    
    await emit_job_progress(job_id, "REBUILD", 25, "Recompilando archivos modificados")
    await asyncio.sleep(2)
    
    await emit_job_progress(job_id, "REBUILD", 50, "Enlazando bibliotecas")
    await asyncio.sleep(1.5)
    
    await emit_job_progress(job_id, "REBUILD", 75, "Generando binario")
    await asyncio.sleep(1.5)
    
    await emit_log("SUCCESS", "✅ Compilación exitosa!", "build", job_id)
    await emit_log("INFO", "📦 Binario generado: build/esp32_app.bin (245 KB)", "build", job_id)
    await emit_job_progress(job_id, "REBUILD", 100, "Build completado exitosamente")
    
    await emit_agent_status("build", "idle")
    print("✅ Build: Compilación exitosa después del fix")
    await asyncio.sleep(2)
    
    # ========================================================================
    # FASE 5: VALIDACIÓN Y TESTING
    # ========================================================================
    print("\n" + "="*80)
    print("FASE 5: VALIDACIÓN - Test Agent verificando el resultado")
    print("="*80 + "\n")
    
    await emit_agent_status("test", "active")
    await emit_log("INFO", "🧪 Iniciando validación del código corregido", "test", job_id)
    await emit_job_progress(job_id, "VALIDATE", 0, "Preparando ambiente de test")
    await asyncio.sleep(1)
    
    await emit_log("INFO", "📋 Verificando declaraciones de variables", "test", job_id)
    await emit_job_progress(job_id, "VALIDATE", 25, "Análisis estático")
    await asyncio.sleep(1.5)
    
    await emit_log("SUCCESS", "✅ Todas las variables están declaradas correctamente", "test", job_id)
    await emit_job_progress(job_id, "VALIDATE", 50, "Verificando lógica del código")
    await asyncio.sleep(1)
    
    await emit_log("INFO", "🔬 Ejecutando test de sintaxis ESP-IDF", "test", job_id)
    await emit_job_progress(job_id, "VALIDATE", 75, "Tests de sintaxis")
    await asyncio.sleep(1.5)
    
    await emit_log("SUCCESS", "✅ Todos los tests pasaron exitosamente", "test", job_id)
    await emit_log("INFO", "📊 Cobertura: Variables (100%), Sintaxis (100%)", "test", job_id)
    await emit_job_progress(job_id, "VALIDATE", 100, "Validación completada")
    
    await emit_agent_status("test", "idle")
    print("✅ Test: Validación completada - Código listo para flash")
    await asyncio.sleep(2)
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("✨ WORKFLOW COMPLETADO EXITOSAMENTE")
    print("="*80 + "\n")
    
    await emit_log("SUCCESS", "🎉 Workflow completado exitosamente!", "system", job_id)
    
    summary = """📊 RESUMEN: Error detectado y corregido | Build exitoso (245 KB) | Tests: 100% | Tiempo: ~2 min"""
    await emit_log("INFO", summary, "system", job_id)
    
    print(summary)
    print("\n" + "="*80)
    print("📊 Revisa el dashboard para ver:")
    print("   • Timeline completo del workflow")
    print("   • Logs detallados por agente  ")
    print("   • Métricas de tiempo y éxito")
    print("="*80 + "\n")
    
    # Keep emitter running
    await asyncio.sleep(5)
    print("⏳ Deteniendo event emitter en 5 segundos...")
    await asyncio.sleep(5)
    
    await event_emitter.stop()
    print("✅ Event emitter stopped\n")


if __name__ == "__main__":
    try:
        asyncio.run(simulate_real_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrumpido por el usuario")
        print("✅ Event emitter stopped\n")
