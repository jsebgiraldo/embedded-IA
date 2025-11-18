# Projects Tab - User Guide

## 📦 Tab de Projects - Gestión Visual de Proyectos GitHub

### 🎯 Descripción

El tab **Projects** proporciona una interfaz visual completa para gestionar proyectos ESP32 importados desde GitHub. Permite crear, monitorear, sincronizar y construir proyectos directamente desde el dashboard.

---

## 🚀 Características Principales

### 1. **Dashboard de Estadísticas**
Muestra métricas globales de todos tus proyectos:
- 📦 Total de proyectos
- ✅ Proyectos activos
- 🔨 Total de builds
- 📈 Tasa de éxito de builds

### 2. **Lista de Proyectos**
Visualización en tarjetas con información clave:
- Nombre del proyecto
- Estado (active/pending/error)
- Repositorio GitHub
- Branch activo
- Target ESP32
- Último commit
- Métricas individuales (builds, success rate, avg time)

### 3. **Acciones por Proyecto**
Cada proyecto tiene botones de acción rápida:
- 🔄 **Sync**: Actualiza el código desde GitHub (git pull)
- 🔨 **Build**: Inicia un nuevo build del proyecto
- 🗑️ **Delete**: Elimina el proyecto (con confirmación)

### 4. **Modal de Nuevo Proyecto**
Formulario para importar proyectos desde GitHub:
- **Project Name**: Nombre identificador del proyecto
- **Repository URL**: URL HTTPS del repositorio (ej: `https://github.com/user/repo.git`)
- **Branch**: Branch a usar (default: `main`)
- **Build Target**: Chip ESP32 objetivo (esp32, esp32s2, esp32s3, esp32c3, etc.)
- **Webhook Secret**: (Opcional) Secret para validar webhooks de GitHub

### 5. **Modal de Detalles del Proyecto**
Vista detallada que incluye:
- Información completa del proyecto
- Configuración de webhooks (si está configurado)
- Estadísticas de builds
- Lista de builds recientes con:
  - Estado (pending, running, success, failed)
  - Commit SHA
  - Trigger source (manual, webhook)
  - Timestamps

### 6. **Filtrado y Búsqueda**
- Filtro por estado (All/Active/Pending/Error)
- Botón de refresh manual
- Auto-refresh cada 30 segundos

---

## 🎨 Interfaz de Usuario

### Paleta de Estados

**Project Status:**
- 🟢 **Active**: Proyecto clonado y listo
- 🟡 **Pending**: En proceso de clonación
- 🔴 **Error**: Error en clonación o configuración

**Build Status:**
- ⏳ **Pending**: Build en cola
- 🔄 **Running**: Build en ejecución
- ✅ **Success**: Build exitoso
- ❌ **Failed**: Build falló

### Interacciones

1. **Click en tarjeta de proyecto**: Abre modal de detalles
2. **Click en botones de acción**: Ejecuta acción específica (con confirmación para delete)
3. **Botón "New Project"**: Abre modal de creación
4. **Filtros**: Actualiza vista instantáneamente

---

## 🔧 Uso Típico

### Crear un Nuevo Proyecto

```
1. Click en "➕ New Project"
2. Llenar formulario:
   - Name: "my-esp32-blinky"
   - Repo URL: "https://github.com/espressif/esp-idf-template.git"
   - Branch: "master"
   - Target: "esp32"
3. Click en "Create Project"
4. El sistema automáticamente:
   - Valida la URL
   - Clona el repositorio
   - Guarda configuración en DB
   - Muestra el proyecto en la lista
```

### Sincronizar Cambios de GitHub

```
1. Click en botón "🔄 Sync" en la tarjeta del proyecto
2. El sistema:
   - Ejecuta git pull
   - Calcula diff de archivos
   - Actualiza last_commit_sha
   - Muestra cantidad de archivos modificados
```

### Iniciar un Build

```
1. Click en botón "🔨 Build" en la tarjeta del proyecto
2. El sistema:
   - Crea registro de Build en DB
   - Obtiene commit SHA actual
   - Marca triggered_by: "manual"
   - Status: "pending"
3. (Futuro) Se conectará con AgentOrchestrator para ejecutar workflow completo
```

### Ver Detalles y Builds

```
1. Click en cualquier parte de la tarjeta del proyecto
2. Se abre modal con:
   - Información del proyecto
   - Configuración de webhook
   - Estadísticas de builds
   - Lista de todos los builds con detalles
```

---

## 🔐 Integración con GitHub Webhooks

### Configuración en GitHub

Una vez creado el proyecto con webhook_secret, configurar en GitHub:

```
Repository Settings > Webhooks > Add webhook

Payload URL: http://your-server.com/api/github/webhook
Content type: application/json
Secret: [copiar del modal de detalles]
Events: 
  ✅ Push events
  ✅ Pull requests
```

### Flujo Automático

```
GitHub → Webhook → API → Background Task → Build Record → (Futuro) Orchestrator
```

---

## 📊 Métricas Calculadas

### Success Rate
```
success_rate = (builds exitosos / total builds) × 100
```

### Average Build Time
```
avg_build_time = Σ(build durations) / total completed builds
```

---

## 🎯 Estados de Proyecto

| Estado | Descripción | Causa |
|--------|-------------|-------|
| `active` | Funcionando correctamente | Clone exitoso, código actualizado |
| `pending` | En proceso | Clone en progreso |
| `error` | Error de configuración | URL inválida, branch no existe, permisos |

---

## 🔄 Real-Time Updates

El tab se actualiza automáticamente:
- ⏱️ Polling cada 30 segundos
- 📡 WebSocket notifications para eventos de builds
- 🔄 Refresh manual disponible

---

## 🎨 Archivos Creados

### HTML
- `/web-server/static/index.html` (modificado)
  - Nuevo tab navigation button
  - Sección completa del tab Projects
  - 2 modales: New Project y Project Detail

### CSS
- `/web-server/static/css/projects.css` (nuevo)
  - Estilos para tarjetas de proyectos
  - Modales y formularios
  - Estados visuales y badges
  - Responsive grid layout

### JavaScript
- `/web-server/static/js/projects.js` (nuevo)
  - `loadProjects()`: Carga lista de proyectos
  - `loadProjectsStats()`: Carga métricas globales
  - `createProject()`: Crea nuevo proyecto
  - `syncProject()`: Sincroniza con GitHub
  - `triggerBuild()`: Inicia build
  - `deleteProject()`: Elimina proyecto
  - `showProjectDetail()`: Muestra detalles en modal
  - Auto-refresh y WebSocket integration

- `/web-server/static/js/main.js` (modificado)
  - `switchTab()`: Función para cambiar entre tabs

---

## 🐛 Troubleshooting

### "No Projects Yet"
- Estado normal si no has creado proyectos
- Click en "Create Project" para comenzar

### Error al Crear Proyecto
- Verificar URL del repositorio (debe ser HTTPS clone URL)
- Verificar que el branch existe
- Verificar acceso al repositorio (público o con credenciales)

### Sync Falla
- Verificar conexión a internet
- Verificar que el repositorio sigue existiendo
- Revisar logs del dashboard

### Build No Inicia
- Actualmente solo crea el registro
- Integración con Orchestrator pendiente

---

## 🚀 Próximos Pasos

### Funcionalidades Pendientes:
1. ✅ UI Tab completado
2. ⏳ Dependency Resolver (parser `idf_component.yml`)
3. ⏳ Integración con AgentOrchestrator
4. ⏳ Real-time build logs en UI
5. ⏳ Build artifacts download
6. ⏳ Test results visualization

---

## 📚 Referencias

- API Endpoints: Ver `/docs/GITHUB_IMPORT_DESIGN.md`
- Backend Services: `/web-server/services/`
- Database Models: `/web-server/database/db.py`
- API Routes: `/web-server/api/routes/projects.py`
