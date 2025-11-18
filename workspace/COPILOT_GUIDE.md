# Copilot Prompts Guide (ESP-IDF)

## Context
- ESP-IDF project at `/workspace`
- Target: `${ESP_IDF_TARGET}` (adjust in `.env`)
- Build: `idf.py build`
- Flash: `idf.py -p /dev/ttyUSB0 flash`
- Monitor: `idf.py -p /dev/ttyUSB0 monitor`

## Useful prompts

### 1. Fix compilation errors
```
Review this `idf.py build` error and suggest the minimal change in `main/main.c` 
or `CMakeLists.txt` to fix it. Explain why.
```

### 2. Add driver/peripheral
```
Add I2C support to `main/main.c`, initialize the bus at 400kHz on GPIO pins 8/9 
(adjust for your board), and write an `i2c_scan()` function that prints found addresses.
```

### 3. Migrate to another target
```
Migrate the project to `${ESP_IDF_TARGET}` by updating `idf.py set-target` and 
any necessary configuration macros.
```

### 4. Optimization
```
Review `sdkconfig` to reduce firmware size: disable verbose logs, unused components, 
and enable `CONFIG_COMPILER_OPTIMIZATION_SIZE`.
```

### 5. Log capture
```
Suggest how to structure logs (ESP_LOGI/W/E) with tags per module and levels 
controlled by `sdkconfig`.
```

## Available agents

### Firmware Agent
- Driver and firmware functionality development
- Code and resource optimization
- ESP-IDF component integration

### QA Agent
- Unit tests with Unity
- Functionality validation
- Static analysis with clang-tidy, cppcheck

### DevOps Agent
- CI/CD with GitHub Actions
- Build automation
- Release and artifact management
