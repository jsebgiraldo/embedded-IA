"""
ESP32/ESP-IDF specific prompts for LLM-powered code fixing
"""

# System prompt for ESP32 Developer Agent
ESP32_DEVELOPER_SYSTEM_PROMPT = """You are an expert ESP32 firmware developer specializing in ESP-IDF (Espressif IoT Development Framework).

Your role is to analyze compilation errors and runtime issues in ESP32 C/C++ code and provide precise, working fixes.

**Your expertise includes:**
- ESP-IDF APIs (GPIO, WiFi, Bluetooth, FreeRTOS, NVS, etc.)
- Common ESP32 hardware peripherals (I2C, SPI, UART, ADC, PWM)
- ESP-IDF build system (CMakeLists.txt, sdkconfig)
- FreeRTOS task management and synchronization
- Memory management (heap, PSRAM, stack)
- ESP32 variants (ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6)

**When fixing code, you must:**
1. Identify the root cause of the error
2. Provide the EXACT fixed code (complete, not snippets)
3. Explain what was wrong and how you fixed it
4. Include all necessary #include statements
5. Ensure code follows ESP-IDF best practices
6. Preserve existing code structure and style

**Output format:**
Respond with a JSON object containing:
{
    "diagnosis": "Brief explanation of the error",
    "root_cause": "Root cause analysis",
    "fixed_code": "Complete fixed code (all lines)",
    "changes_made": ["List of specific changes"],
    "includes_added": ["List of any #include statements added"],
    "confidence": "high|medium|low"
}

**Important:**
- Always provide COMPLETE code, not partial snippets
- Do not use placeholders like "// rest of code"
- Include ALL necessary headers
- Test your fixes mentally before responding
- If unsure, set confidence to "low"
"""

# User prompt template for code fixing
ESP32_CODE_FIX_PROMPT = """**Error Context:**
{error_type}: {error_message}

**File:** {filename}
**Component:** {component}

**Original Code:**
```c
{original_code}
```

**Compilation Output:**
```
{compilation_output}
```

**Additional Context:**
- ESP-IDF Target: {target}
- ESP-IDF Version: {idf_version}

Please analyze this error and provide a complete fix in JSON format as specified in your system prompt.
"""

# Prompt for analyzing build errors
BUILD_ERROR_ANALYSIS_PROMPT = """Analyze the following ESP-IDF build error and categorize it:

**Build Output:**
```
{build_output}
```

**Project Structure:**
{project_structure}

Provide a JSON response with:
{
    "error_category": "missing_include|wrong_type|undefined_reference|syntax_error|config_error|other",
    "severity": "critical|high|medium|low",
    "affected_files": ["list of files with errors"],
    "suggested_fixes": ["high-level fix suggestions"],
    "can_auto_fix": true|false,
    "requires_manual_review": true|false
}
"""

# Simple code fix prompt (for quick fixes)
SIMPLE_FIX_PROMPT = """Fix this ESP32 code error:

**Error:** {error_message}

**Code:**
```c
{code}
```

Provide ONLY the fixed code, nothing else. Include all necessary #include statements at the top.
"""

# Prompt for validating a fix
VALIDATE_FIX_PROMPT = """You previously provided a fix for ESP32 code. The build result is:

**Original Error:**
{original_error}

**Your Fix:**
{applied_fix}

**New Build Result:**
{new_build_output}

Did your fix work? Respond with JSON:
{
    "fix_successful": true|false,
    "remaining_errors": ["list of any new errors"],
    "next_steps": "what to do next",
    "needs_different_approach": true|false
}
"""

# Prompt templates for common ESP32 errors
COMMON_ERROR_PROMPTS = {
    "missing_include": """The code is missing an #include statement.

Error: {error}
File: {filename}

Add the correct #include at the top of the file. Common ESP32 includes:
- driver/gpio.h - GPIO operations
- driver/i2c.h - I2C operations  
- driver/spi_master.h - SPI operations
- esp_wifi.h - WiFi functions
- esp_log.h - Logging
- freertos/FreeRTOS.h, freertos/task.h - FreeRTOS
- nvs_flash.h - Non-volatile storage

Code:
```c
{code}
```

Provide the complete fixed code with the correct #include.
""",
    
    "undefined_function": """The function '{function_name}' is not defined or declared.

This usually means:
1. Missing #include for the header that declares it
2. Function not linked (missing in CMakeLists.txt)
3. Typo in function name

Code:
```c
{code}
```

Provide the complete fixed code.
""",
    
    "wrong_type": """Type mismatch error: {error}

Common ESP32 type issues:
- GPIO pin: gpio_num_t (not int)
- Task handle: TaskHandle_t
- Queue handle: QueueHandle_t
- esp_err_t for ESP-IDF function returns

Code:
```c
{code}
```

Fix all type errors and provide complete code.
""",
    
    "gpio_config": """GPIO configuration error.

Correct ESP32 GPIO setup:
```c
gpio_config_t io_conf = {
    .pin_bit_mask = (1ULL << GPIO_NUM_X),
    .mode = GPIO_MODE_OUTPUT,  // or INPUT
    .pull_up_en = GPIO_PULLUP_DISABLE,
    .pull_down_en = GPIO_PULLDOWN_DISABLE,
    .intr_type = GPIO_INTR_DISABLE
};
gpio_config(&io_conf);
```

Your code:
```c
{code}
```

Fix the GPIO configuration.
""",
}


def get_fix_prompt(
    error_type: str,
    error_message: str,
    code: str,
    filename: str = "main.c",
    component: str = "main",
    target: str = "esp32c6",
    idf_version: str = "6.1",
    compilation_output: str = ""
) -> str:
    """
    Generate a complete prompt for fixing ESP32 code
    
    Args:
        error_type: Type of error (syntax, missing_include, etc.)
        error_message: The error message from compiler
        code: The original code with error
        filename: Name of the file with error
        component: ESP-IDF component name
        target: ESP32 target (esp32, esp32c6, etc.)
        idf_version: ESP-IDF version
        compilation_output: Full compilation output
    
    Returns:
        Complete prompt string
    """
    # Use specialized prompt for common errors
    if error_type in COMMON_ERROR_PROMPTS:
        template = COMMON_ERROR_PROMPTS[error_type]
        return template.format(
            error=error_message,
            code=code,
            filename=filename,
            function_name=error_message.split("'")[1] if "'" in error_message else "unknown"
        )
    
    # Use general prompt
    return ESP32_CODE_FIX_PROMPT.format(
        error_type=error_type,
        error_message=error_message,
        original_code=code,
        filename=filename,
        component=component,
        target=target,
        idf_version=idf_version,
        compilation_output=compilation_output or "Not available"
    )


def get_simple_fix_prompt(error_message: str, code: str) -> str:
    """Get a simple fix prompt for quick fixes"""
    return SIMPLE_FIX_PROMPT.format(
        error_message=error_message,
        code=code
    )
