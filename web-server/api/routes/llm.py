"""
LLM API Routes
Endpoints for interacting with the LLM (code generation, chat, analysis)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent.llm_provider import LLMConfig, get_llm, LLMProvider
from agent.code_fixer import create_code_fixer

router = APIRouter(prefix="/api/llm", tags=["llm"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User message to send to LLM")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for response generation")
    system_prompt: Optional[str] = Field(default=None, description="Optional system prompt to set context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="LLM response")
    model: str = Field(..., description="Model used for generation")
    timestamp: str = Field(..., description="Response timestamp")


class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""
    description: str = Field(..., description="Natural language description of code to generate")
    language: str = Field(default="c", description="Programming language (c, cpp, python)")
    framework: str = Field(default="esp-idf", description="Framework context (esp-idf, arduino)")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Temperature for generation")


class CodeGenerationResponse(BaseModel):
    """Response model for code generation"""
    code: str = Field(..., description="Generated code")
    explanation: str = Field(..., description="Explanation of the generated code")
    model: str = Field(..., description="Model used")
    timestamp: str = Field(..., description="Generation timestamp")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    code: str = Field(..., description="Code to analyze")
    error_message: Optional[str] = Field(default=None, description="Optional error message to analyze")
    analysis_type: str = Field(default="general", description="Type of analysis (general, error, optimization)")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis"""
    analysis: str = Field(..., description="Analysis result")
    suggestions: List[str] = Field(default=[], description="List of suggestions")
    severity: str = Field(default="info", description="Severity level (info, warning, error)")
    model: str = Field(..., description="Model used")


class CodeFixRequest(BaseModel):
    """Request model for code fixing"""
    buggy_code: str = Field(..., description="Code with bugs")
    error_message: str = Field(..., description="Error message from compiler")
    filename: str = Field(default="main.c", description="Filename")
    component: str = Field(default="main", description="ESP-IDF component name")


class CodeFixResponse(BaseModel):
    """Response model for code fixing"""
    success: bool = Field(..., description="Whether fix was successful")
    fixed_code: Optional[str] = Field(default=None, description="Fixed code")
    changes_made: List[str] = Field(default=[], description="List of changes made")
    confidence: str = Field(..., description="Confidence level (low, medium, high)")
    diagnosis: str = Field(..., description="Problem diagnosis")


class LLMStatusResponse(BaseModel):
    """Response model for LLM status"""
    available: bool = Field(..., description="Whether LLM is available")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Current model")
    base_url: str = Field(..., description="LLM service URL")


# ============================================================================
# Helper Functions
# ============================================================================

def get_llm_config(temperature: float = 0.7) -> LLMConfig:
    """Get LLM configuration from environment"""
    return LLMConfig(
        provider=LLMProvider(os.getenv("LLM_PROVIDER", "ollama")),
        temperature=temperature,
    )


async def call_llm_async(prompt: str, temperature: float = 0.7, system_prompt: Optional[str] = None) -> str:
    """Call LLM asynchronously"""
    config = get_llm_config(temperature)
    llm = get_llm(config)
    
    # Add system prompt if provided
    if system_prompt:
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
    else:
        full_prompt = prompt
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, llm.invoke, full_prompt)
    
    return response


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """
    Get LLM service status
    
    Returns information about the current LLM configuration and availability.
    """
    try:
        config = get_llm_config()
        
        # Try to ping the LLM
        try:
            llm = get_llm(config)
            available = True
        except Exception:
            available = False
        
        return LLMStatusResponse(
            available=available,
            provider=config.provider.value,
            model=config.model,
            base_url=config.base_url or "default"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLM status: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the LLM
    
    Send a message to the LLM and get a response. Useful for asking questions
    about ESP32 development, getting explanations, or general assistance.
    """
    try:
        config = get_llm_config(request.temperature)
        
        # Add ESP32 context to system prompt if not provided
        system_prompt = request.system_prompt or (
            "You are an expert ESP32 embedded systems developer. "
            "Provide clear, concise, and accurate answers about ESP32 development, "
            "ESP-IDF framework, hardware interfacing, and embedded C programming."
        )
        
        response = await call_llm_async(
            request.message,
            temperature=request.temperature,
            system_prompt=system_prompt
        )
        
        return ChatResponse(
            response=response,
            model=config.model,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate ESP32 code from natural language description
    
    Provide a description of what you want the code to do, and the LLM will
    generate complete, working ESP32 code with explanations.
    """
    try:
        # Create prompt for code generation
        prompt = f"""Generate complete {request.language.upper()} code for ESP32 using {request.framework}.

Description: {request.description}

Requirements:
- Include all necessary headers
- Add comments explaining key sections
- Follow ESP-IDF best practices
- Make it production-ready

Provide the code first, then a brief explanation."""

        system_prompt = (
            "You are an expert ESP32 developer. Generate clean, well-documented, "
            "production-ready code following ESP-IDF conventions."
        )
        
        response = await call_llm_async(
            prompt,
            temperature=request.temperature,
            system_prompt=system_prompt
        )
        
        # Try to split code and explanation
        parts = response.split("\n\nExplanation:")
        if len(parts) == 2:
            code = parts[0].strip()
            explanation = parts[1].strip()
        else:
            # If no clear separation, use the whole response as code
            code = response
            explanation = "Generated code based on your description."
        
        # Clean up code block markers
        if "```" in code:
            code = code.split("```")[1]
            if code.startswith("c\n") or code.startswith("cpp\n"):
                code = "\n".join(code.split("\n")[1:])
        
        config = get_llm_config(request.temperature)
        
        return CodeGenerationResponse(
            code=code.strip(),
            explanation=explanation,
            model=config.model,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze code for issues, improvements, or errors
    
    Submit code for analysis. The LLM will review it and provide suggestions
    for improvements, identify potential issues, or help debug errors.
    """
    try:
        # Build analysis prompt based on type
        if request.analysis_type == "error" and request.error_message:
            prompt = f"""Analyze this ESP32 code that has an error:

```c
{request.code}
```

Error message:
{request.error_message}

Provide:
1. Root cause of the error
2. Specific fix suggestions
3. Why this error occurred"""
            
        elif request.analysis_type == "optimization":
            prompt = f"""Review this ESP32 code for optimization opportunities:

```c
{request.code}
```

Analyze for:
1. Performance improvements
2. Memory optimization
3. Power consumption
4. Code quality and maintainability"""
            
        else:  # general
            prompt = f"""Analyze this ESP32 code:

```c
{request.code}
```

Provide:
1. Code quality assessment
2. Potential issues or bugs
3. Best practices recommendations
4. Security considerations"""
        
        system_prompt = (
            "You are an expert code reviewer specializing in ESP32 embedded systems. "
            "Provide actionable, specific feedback."
        )
        
        response = await call_llm_async(
            prompt,
            temperature=0.3,  # Lower for more focused analysis
            system_prompt=system_prompt
        )
        
        # Extract suggestions (lines starting with numbers or bullets)
        suggestions = []
        severity = "info"
        
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "-", "•")):
                suggestions.append(line)
            if any(word in line.lower() for word in ["critical", "error", "bug"]):
                severity = "error"
            elif severity != "error" and any(word in line.lower() for word in ["warning", "issue"]):
                severity = "warning"
        
        config = get_llm_config()
        
        return CodeAnalysisResponse(
            analysis=response,
            suggestions=suggestions,
            severity=severity,
            model=config.model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code analysis failed: {str(e)}")


@router.post("/fix", response_model=CodeFixResponse)
async def fix_code(request: CodeFixRequest):
    """
    Automatically fix buggy code
    
    Submit code with a compilation error, and the LLM will attempt to fix it.
    This uses the same code fixer that the Developer Agent uses.
    """
    try:
        # Use the code fixer (same as Developer Agent)
        fixer = create_code_fixer()
        
        # Run fix in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            fixer.fix_code,
            request.buggy_code,
            request.error_message,
            "compilation_error",
            request.filename,
            request.component
        )
        
        return CodeFixResponse(
            success=result.success,
            fixed_code=result.fixed_code if result.success else None,
            changes_made=result.changes_made if hasattr(result, 'changes_made') else [],
            confidence=result.confidence,
            diagnosis=result.diagnosis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code fix failed: {str(e)}")


@router.post("/explain")
async def explain_code(code: str):
    """
    Get an explanation of what code does
    
    Submit code and get a detailed explanation of its functionality.
    """
    try:
        prompt = f"""Explain what this ESP32 code does in detail:

```c
{code}
```

Provide:
1. High-level overview
2. Step-by-step explanation
3. Key concepts used
4. Potential use cases"""

        system_prompt = "You are an ESP32 expert teacher. Explain code clearly and thoroughly."
        
        response = await call_llm_async(
            prompt,
            temperature=0.5,
            system_prompt=system_prompt
        )
        
        return {"explanation": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code explanation failed: {str(e)}")
