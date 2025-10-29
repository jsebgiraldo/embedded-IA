# ESP-IDF + Agent (Docker)

Embedded agent system for ESP-IDF development using Docker containers.

## Basic commands

### Build
```bash
idf.py set-target $ESP_IDF_TARGET
idf.py build
```

### Flash and Monitor
```bash
idf.py -p /dev/ttyUSB0 flash
idf.py -p /dev/ttyUSB0 monitor
```

## Quick start

1. Create base project:
```bash
docker compose run --rm dev bash -lc "idf.py create-project my_app && mv my_app/* . && rmdir my_app"
```

2. Configure target:
```bash
docker compose exec dev bash -lc "idf.py set-target ${ESP_IDF_TARGET:-esp32}"
```

3. Build:
```bash
docker compose exec dev bash -lc "idf.py build"
```

## Project structure

- `main/` - Main firmware source code
- `CMakeLists.txt` - Build configuration
- `sdkconfig` - ESP-IDF configuration (generated)
