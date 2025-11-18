# Dependency Resolver - Documentation

## 📦 Overview

El **Dependency Resolver** es un servicio que automatiza la detección, parseo y gestión de dependencias de componentes ESP-IDF en proyectos importados desde GitHub.

---

## 🎯 Características

### ✅ Implementado

1. **Auto-scan al crear proyectos**: Cuando se clona un proyecto, automáticamente escanea las dependencias
2. **Re-scan al sincronizar**: Actualiza dependencias cuando se hace `git pull`
3. **Parser de idf_component.yml**: Lee y parsea archivos de manifiesto estándar de ESP-IDF
4. **Múltiples fuentes**: Soporta dependencias de registry, git y path
5. **Versionado semántico**: Maneja constraints de versión (`*`, `^1.0.0`, `~2.3.0`)
6. **API REST completa**: Endpoints para escanear, listar y visualizar dependencias
7. **Almacenamiento en DB**: Guarda dependencias con timestamps y estados

### ⏳ Pendiente

- Instalación automática de componentes usando `idf.py add-dependency`
- Validación de dependencias y detección de conflictos
- Dependencias transitivas (árbol completo)
- Cache de componentes descargados

---

## 📋 Formato soportado: idf_component.yml

### Estructura básica

```yaml
version: "1.0.0"
description: "Mi componente ESP32"
dependencies:
  # Versión simple
  component_name: "*"
  
  # Versión específica
  espressif/led_strip: "^2.0.0"
  
  # Desde Git
  custom/component:
    version: "1.0.0"
    git: "https://github.com/user/repo.git"
  
  # Desde path local
  local/component:
    path: "../components/local"
```

### Versiones soportadas

- `*` - Cualquier versión
- `^1.2.3` - Compatible con 1.x.x (>=1.2.3 <2.0.0)
- `~1.2.3` - Compatible con 1.2.x (>=1.2.3 <1.3.0)
- `1.2.3` - Versión exacta

---

## 🔧 Servicio: DependencyResolver

### Ubicación
`/web-server/services/dependency_resolver.py`

### Métodos principales

#### `scan_project_dependencies(project_id, project_path)`
Escanea un proyecto completo en busca de archivos `idf_component.yml`.

**Proceso:**
1. Recorre el árbol de directorios del proyecto
2. Encuentra todos los archivos `idf_component.yml`
3. Parsea cada archivo con PyYAML
4. Extrae dependencias con sus metadatos
5. Elimina dependencias antiguas del proyecto
6. Guarda nuevas dependencias en la base de datos

**Returns:** `(total_found, newly_added)`

**Ejemplo:**
```python
resolver = DependencyResolver(db)
total, added = resolver.scan_project_dependencies(
    project_id="uuid-here",
    project_path="/app/projects/my-project"
)
# (3, 3) - Encontró 3, agregó 3
```

#### `find_component_manifests(project_path)`
Busca recursivamente archivos `idf_component.yml`.

**Ignora:**
- Directorios ocultos (`.git`, `.vscode`)
- Build folders (`build/`, `dist/`)
- Python cache (`__pycache__/`)

**Returns:** `List[str]` - Paths absolutos a manifiestos

#### `parse_component_manifest(manifest_path)`
Parsea un archivo YAML y retorna su contenido.

**Returns:** `Dict` o `None` si falla

#### `extract_dependencies(manifest_data)`
Extrae dependencias del YAML parseado.

**Returns:** `List[Dict]` con keys: `name`, `version`, `source`

**Ejemplo de salida:**
```python
[
    {
        'name': 'espressif/led_strip',
        'version': '^2.0.0',
        'source': 'component-registry'
    },
    {
        'name': 'custom/component',
        'version': '1.0.0',
        'source': 'git:https://github.com/user/repo.git'
    }
]
```

#### `get_project_dependencies(project_id)`
Obtiene todas las dependencias de la BD.

**Returns:** `List[Dependency]` - Objetos SQLAlchemy

#### `get_dependency_tree(project_id)`
Construye un árbol de dependencias.

**Returns:**
```python
{
    'project_id': 'uuid',
    'direct_dependencies': [...],
    'total_count': 3
}
```

#### `install_dependencies(project_id, project_path)` ⚠️ Placeholder
**TODO:** Implementar instalación real usando ESP-IDF component manager.

**Returns:** `(successful, failed, errors)`

#### `validate_dependencies(project_path)` ⚠️ Placeholder
**TODO:** Validar compatibilidad y detectar conflictos.

**Returns:**
```python
{
    'valid': bool,
    'missing': List[str],
    'conflicts': List[str],
    'warnings': List[str]
}
```

---

## 🌐 API Endpoints

### 1. Escanear dependencias
```http
POST /api/projects/{project_id}/scan-dependencies
```

**Descripción:** Escanea el proyecto en busca de `idf_component.yml` y actualiza la base de datos.

**Response:**
```json
{
  "project_id": "uuid",
  "project_name": "my-project",
  "total_found": 3,
  "newly_added": 3,
  "dependencies": [
    {
      "id": "1",
      "component_name": "espressif/led_strip",
      "version": "^2.0.0",
      "source": "component-registry",
      "installed": false
    }
  ]
}
```

**Errores:**
- `404` - Proyecto no encontrado
- `400` - Repositorio no clonado
- `500` - Error al escanear

### 2. Listar dependencias
```http
GET /api/projects/{project_id}/dependencies
```

**Descripción:** Obtiene todas las dependencias guardadas en la base de datos.

**Response:**
```json
{
  "project_id": "uuid",
  "project_name": "my-project",
  "total_dependencies": 3,
  "dependencies": [
    {
      "id": "1",
      "component_name": "espressif/led_strip",
      "version": "^2.0.0",
      "source": "component-registry",
      "installed": false,
      "created_at": "2025-11-17T17:50:34.048326"
    }
  ]
}
```

### 3. Árbol de dependencias
```http
GET /api/projects/{project_id}/dependency-tree
```

**Descripción:** Visualiza dependencias en formato de árbol.

**Response:**
```json
{
  "project_id": "uuid",
  "project_name": "my-project",
  "direct_dependencies": [
    {
      "name": "espressif/led_strip",
      "version": "^2.0.0",
      "source": "component-registry",
      "installed": false
    }
  ],
  "total_count": 3
}
```

### 4. Instalar dependencias ⚠️ Placeholder
```http
POST /api/projects/{project_id}/install-dependencies
```

**Descripción:** Instala componentes usando ESP-IDF component manager (no implementado).

**Response:**
```json
{
  "project_id": "uuid",
  "project_name": "my-project",
  "successful_installs": 0,
  "failed_installs": 0,
  "errors": ["Dependency installation feature is not yet implemented"],
  "message": "Dependency installation feature is not yet implemented"
}
```

---

## 🗄️ Modelo de Base de Datos

### Tabla: `dependencies`

```sql
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    component_name TEXT NOT NULL,
    version TEXT,
    source TEXT,  -- 'component-registry', 'git:url', 'path:path'
    installed BOOLEAN DEFAULT 0,
    installed_at DATETIME,
    install_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### Campos

- **component_name**: Nombre del componente (ej: `espressif/led_strip`)
- **version**: Constraint de versión (`*`, `^2.0.0`, `1.0.0`)
- **source**: Origen del componente
  - `component-registry` - Registry oficial de ESP-IDF
  - `git:https://github.com/...` - Repositorio Git
  - `path:../components/...` - Path local
- **installed**: Flag de instalación
- **installed_at**: Timestamp de instalación exitosa
- **install_error**: Mensaje de error si falla instalación

---

## 🔄 Integración con Workflow

### Flujo automático

```
1. Usuario crea proyecto (POST /api/projects)
   ↓
2. Sistema clona repositorio
   ↓
3. ✅ AUTO: Escanea dependencias
   ↓
4. Guarda en DB con status installed=false
   ↓
5. Usuario sincroniza (PUT /api/projects/{id}/sync)
   ↓
6. Sistema hace git pull
   ↓
7. ✅ AUTO: Re-escanea dependencias
   ↓
8. Actualiza cambios en DB
```

### Flujo manual

```
1. Usuario consulta dependencias
   GET /api/projects/{id}/dependencies
   ↓
2. Usuario dispara escaneo manual
   POST /api/projects/{id}/scan-dependencies
   ↓
3. Usuario visualiza árbol
   GET /api/projects/{id}/dependency-tree
   ↓
4. (Futuro) Usuario instala dependencias
   POST /api/projects/{id}/install-dependencies
```

---

## 🧪 Testing

### Test manual con curl

```bash
# 1. Listar proyectos
curl http://localhost:8000/api/projects | jq '.projects[] | {id, name}'

# 2. Escanear dependencias
curl -X POST http://localhost:8000/api/projects/{PROJECT_ID}/scan-dependencies | jq '.'

# 3. Listar dependencias
curl http://localhost:8000/api/projects/{PROJECT_ID}/dependencies | jq '.'

# 4. Ver árbol
curl http://localhost:8000/api/projects/{PROJECT_ID}/dependency-tree | jq '.'
```

### Crear archivo de test

```bash
# Dentro del contenedor
docker exec esp32-web-dashboard bash -c 'cat > /app/projects/my-project/idf_component.yml << EOF
dependencies:
  espressif/led_strip: "^2.0.0"
  espressif/button: "*"
EOF'

# Escanear
curl -X POST http://localhost:8000/api/projects/{ID}/scan-dependencies
```

---

## 📊 Logs

El servicio genera logs detallados:

```
INFO: Found component manifest: /app/projects/my-project/idf_component.yml
INFO: Successfully parsed manifest: /app/projects/...
DEBUG: Extracted dependency: {'name': 'espressif/led_strip', 'version': '^2.0.0', ...}
INFO: Project uuid: Found 3 dependencies, added 3 to database
INFO: ✅ Auto-scanned dependencies: 3 found, 3 stored
```

---

## 🔮 Roadmap

### Fase 1: ✅ Parser y Storage (Completado)
- [x] Buscar archivos idf_component.yml
- [x] Parsear YAML
- [x] Extraer dependencias
- [x] Guardar en base de datos
- [x] Auto-scan en create/sync
- [x] API endpoints

### Fase 2: ⏳ Instalación (Siguiente)
- [ ] Integración con ESP-IDF component manager
- [ ] Comando `idf.py add-dependency`
- [ ] Download de componentes
- [ ] Actualizar flag `installed`
- [ ] Manejo de errores de instalación

### Fase 3: ⏳ Validación
- [ ] Detectar dependencias faltantes
- [ ] Resolver conflictos de versión
- [ ] Validar compatibilidad con ESP-IDF
- [ ] Detectar circular dependencies

### Fase 4: ⏳ UI Integration
- [ ] Mostrar dependencias en Project Detail modal
- [ ] Badges de cantidad de dependencias
- [ ] Botón "Install Dependencies"
- [ ] Progress bar de instalación

---

## 🛠️ Dependencias

**Python Packages:**
- `PyYAML>=6.0.1` - Parser YAML
- `SQLAlchemy>=2.0.36` - ORM base de datos
- `FastAPI>=0.115.0` - Framework API

**Archivos:**
- `/web-server/services/dependency_resolver.py` - Servicio
- `/web-server/api/routes/projects.py` - Endpoints
- `/web-server/requirements.txt` - Dependencias Python
- `/web-server/database/db.py` - Modelo Dependency

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Proyecto simple

```yaml
# idf_component.yml
dependencies:
  espressif/led_strip: "*"
```

**Resultado:**
- 1 dependencia detectada
- Source: `component-registry`
- Version: `*` (any)

### Ejemplo 2: Proyecto con Git

```yaml
dependencies:
  custom/driver:
    version: "1.0.0"
    git: "https://github.com/user/esp32-driver.git"
```

**Resultado:**
- 1 dependencia detectada
- Source: `git:https://github.com/user/esp32-driver.git`
- Version: `1.0.0`

### Ejemplo 3: Mix de fuentes

```yaml
dependencies:
  espressif/button: "^1.0.0"
  espressif/led_strip:
    version: "2.0.0"
    git: "https://github.com/espressif/idf-extra-components.git"
  local/hal:
    path: "../hal"
```

**Resultado:**
- 3 dependencias
- 2 de registry, 1 de git, 0 de path local
- Diferentes constraints de versión

---

## 🐛 Troubleshooting

### "No component manifests found"
- El proyecto no tiene archivos `idf_component.yml`
- Crear manualmente o usar proyecto con dependencias

### "YAML parsing error"
- Sintaxis YAML inválida
- Verificar indentación (usar espacios, no tabs)
- Validar con yamllint

### "Error storing dependency"
- Problema de base de datos
- Verificar logs del servidor
- Revisar modelo Dependency en db.py

### Auto-scan no funciona
- Verificar que el proyecto tenga `status=active`
- Check logs: `docker logs esp32-web-dashboard`
- Ejecutar scan manual: `POST /scan-dependencies`

---

## 📚 Referencias

- [ESP-IDF Component Manager](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/tools/idf-component-manager.html)
- [idf_component.yml Schema](https://docs.espressif.com/projects/idf-component-manager/en/latest/reference/manifest_file.html)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
