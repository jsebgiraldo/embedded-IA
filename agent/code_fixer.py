"""
Code analyzer and fixer using LLM
Connects Developer Agent with LLM provider
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from agent.llm_provider import get_llm, LLMConfig, LLMProvider
from agent.prompts import (
    ESP32_DEVELOPER_SYSTEM_PROMPT,
    get_fix_prompt,
    get_simple_fix_prompt,
)


class CodeFixResult:
    """Result of a code fix attempt"""
    def __init__(
        self,
        success: bool,
        original_code: str,
        fixed_code: Optional[str] = None,
        diagnosis: Optional[str] = None,
        changes_made: Optional[List[str]] = None,
        confidence: str = "unknown",
        error: Optional[str] = None
    ):
        self.success = success
        self.original_code = original_code
        self.fixed_code = fixed_code
        self.diagnosis = diagnosis
        self.changes_made = changes_made or []
        self.confidence = confidence
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "diagnosis": self.diagnosis,
            "changes_made": self.changes_made,
            "confidence": self.confidence,
            "error": self.error
        }


class ESP32CodeFixer:
    """
    Analyzes ESP32 code errors and generates fixes using LLM
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """
        Initialize code fixer with LLM
        
        Args:
            llm_config: LLM configuration (None = use default Ollama)
        """
        self.llm_config = llm_config or LLMConfig()
        self.llm = None
        self._initialize_llm()
    
    @property
    def model(self) -> str:
        """Get the model name being used"""
        return self.llm_config.model
    
    def _initialize_llm(self):
        """Initialize LLM connection"""
        try:
            self.llm = get_llm(self.llm_config)
            print(f"✅ Code fixer initialized with {self.llm_config.provider.value}")
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            raise
    
    def fix_code(
        self,
        buggy_code: str,
        error_message: str,
        error_type: str = "compilation_error",
        filename: str = "main.c",
        component: str = "main",
        use_simple_prompt: bool = False
    ) -> CodeFixResult:
        """
        Fix buggy ESP32 code using LLM
        
        Args:
            buggy_code: The code with errors
            error_message: Error message from compiler
            error_type: Type of error (missing_include, wrong_type, etc.)
            filename: Name of the file with error
            component: ESP-IDF component name
            use_simple_prompt: Use simple prompt for faster fixes
        
        Returns:
            CodeFixResult with fixed code and analysis
        """
        print(f"\n🔍 Analyzing error: {error_type}")
        print(f"   File: {filename}")
        print(f"   Error: {error_message[:100]}...")
        
        try:
            # Generate prompt
            if use_simple_prompt:
                prompt = get_simple_fix_prompt(error_message, buggy_code)
                return self._simple_fix(prompt, buggy_code)
            else:
                prompt = get_fix_prompt(
                    error_type=error_type,
                    error_message=error_message,
                    code=buggy_code,
                    filename=filename,
                    component=component
                )
                return self._structured_fix(prompt, buggy_code)
        
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            return CodeFixResult(
                success=False,
                original_code=buggy_code,
                error=str(e)
            )
    
    def _simple_fix(self, prompt: str, original_code: str) -> CodeFixResult:
        """
        Simple fix - just return the fixed code
        """
        # Use system prompt + user prompt
        messages = [
            ("system", ESP32_DEVELOPER_SYSTEM_PROMPT),
            ("user", prompt)
        ]
        
        response = self.llm.invoke(messages)
        # Handle both string and object responses
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        fixed_code = self._extract_code_from_response(response_text)
        
        if fixed_code and fixed_code != original_code:
            print("✅ Code fixed successfully (simple mode)")
            return CodeFixResult(
                success=True,
                original_code=original_code,
                fixed_code=fixed_code,
                diagnosis="Simple fix applied",
                changes_made=["Code modified"],
                confidence="medium"
            )
        else:
            return CodeFixResult(
                success=False,
                original_code=original_code,
                error="No valid fix generated"
            )
    
    def _structured_fix(self, prompt: str, original_code: str) -> CodeFixResult:
        """
        Structured fix - parse JSON response with full analysis
        """
        # Use system prompt + user prompt
        messages = [
            ("system", ESP32_DEVELOPER_SYSTEM_PROMPT),
            ("user", prompt)
        ]
        
        response = self.llm.invoke(messages)
        # Handle both string and object responses
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response (might be wrapped in markdown code blocks)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group(0))
                
                return CodeFixResult(
                    success=True,
                    original_code=original_code,
                    fixed_code=fix_data.get("fixed_code"),
                    diagnosis=fix_data.get("diagnosis"),
                    changes_made=fix_data.get("changes_made", []),
                    confidence=fix_data.get("confidence", "unknown")
                )
            else:
                # Fallback: treat whole response as fixed code
                fixed_code = self._extract_code_from_response(response_text)
                return CodeFixResult(
                    success=bool(fixed_code),
                    original_code=original_code,
                    fixed_code=fixed_code,
                    diagnosis="Auto-extracted from response",
                    confidence="low"
                )
        
        except json.JSONDecodeError:
            # Fallback: extract code from response
            fixed_code = self._extract_code_from_response(response_text)
            return CodeFixResult(
                success=bool(fixed_code),
                original_code=original_code,
                fixed_code=fixed_code,
                diagnosis="Extracted from non-JSON response",
                confidence="low"
            )
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """
        Extract C code from LLM response (handles markdown code blocks)
        """
        # Try to extract code from markdown code blocks
        code_patterns = [
            r'```c\n(.*?)\n```',      # ```c ... ```
            r'```cpp\n(.*?)\n```',    # ```cpp ... ```
            r'```\n(.*?)\n```',       # ``` ... ```
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no code blocks, check if response looks like C code
        if '#include' in response or 'void app_main' in response:
            # Clean up the response
            lines = response.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                if '#include' in line or 'void ' in line:
                    in_code = True
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                return '\n'.join(code_lines).strip()
        
        return None
    
    def batch_fix(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[Tuple[str, CodeFixResult]]:
        """
        Fix multiple test cases
        
        Args:
            test_cases: List of test case dictionaries
        
        Returns:
            List of (test_name, CodeFixResult) tuples
        """
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*70}")
            print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
            print(f"{'='*70}")
            
            result = self.fix_code(
                buggy_code=test_case['buggy_code'],
                error_message=test_case.get('expected_error', 'Unknown error'),
                error_type=test_case.get('error_type', 'compilation_error'),
                filename=f"{test_case['name']}.c"
            )
            
            results.append((test_case['name'], result))
            
            # Show result summary
            if result.success:
                print(f"✅ FIXED - Confidence: {result.confidence}")
                if result.diagnosis:
                    print(f"   Diagnosis: {result.diagnosis}")
                if result.changes_made:
                    print(f"   Changes: {', '.join(result.changes_made[:3])}")
            else:
                print(f"❌ FAILED - {result.error}")
        
        return results
    
    def validate_fix(
        self,
        original_code: str,
        fixed_code: str,
        expected_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate that the fix is correct
        
        Args:
            original_code: Original buggy code
            fixed_code: Fixed code from LLM
            expected_code: Expected correct code (optional)
        
        Returns:
            Validation results
        """
        validation = {
            "code_changed": fixed_code != original_code,
            "has_includes": "#include" in fixed_code,
            "has_app_main": "void app_main" in fixed_code,
            "matches_expected": False,
            "similarity_score": 0.0
        }
        
        if expected_code:
            # Simple similarity check
            fixed_lines = set(fixed_code.strip().split('\n'))
            expected_lines = set(expected_code.strip().split('\n'))
            
            common_lines = fixed_lines & expected_lines
            total_lines = len(expected_lines)
            
            validation["matches_expected"] = fixed_lines == expected_lines
            validation["similarity_score"] = len(common_lines) / total_lines if total_lines > 0 else 0.0
        
        return validation


DEFAULT_MODELS = {
    LLMProvider.OLLAMA: "qwen2.5-coder:14b",
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.ANTHROPIC: "claude-3-5-haiku-20241022",
    LLMProvider.AZURE: "gpt-4o-mini",
    LLMProvider.DEEPSEEK: "deepseek-coder-v2",
}


def _env_flag(var: str, default: bool) -> bool:
    value = os.getenv(var)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_code_fixer(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> ESP32CodeFixer:
    """Factory function that builds the LLM config using .env overrides."""

    provider_name = provider or os.getenv("LLM_PROVIDER", LLMProvider.OLLAMA.value)
    provider_enum = LLMProvider(provider_name.lower())

    # Model selection with env override
    resolved_model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider_enum, "qwen2.5-coder:14b")

    # Base URL customization (useful for dockerized Ollama or custom gateways)
    base_url = None
    if provider_enum == LLMProvider.OLLAMA:
        base_url = os.getenv("OLLAMA_BASE_URL")
    elif provider_enum == LLMProvider.DEEPSEEK:
        base_url = os.getenv("DEEPSEEK_BASE_URL")

    max_tokens_env = os.getenv("LLM_MAX_TOKENS")
    max_tokens = int(max_tokens_env) if max_tokens_env and max_tokens_env.isdigit() else None

    config = LLMConfig(
        provider=provider_enum,
        model=resolved_model,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        max_tokens=max_tokens,
        base_url=base_url,
        fallback_to_local=_env_flag("LLM_FALLBACK_TO_LOCAL", True),
    )
    
    return ESP32CodeFixer(config)


if __name__ == "__main__":
    """Test the code fixer"""
    from agent.test_cases import CASE_1_MISSING_INCLUDE
    
    print("🧪 Testing ESP32 Code Fixer\n")
    
    # Create fixer
    fixer = create_code_fixer("ollama")
    
    # Test simple case
    test_case = CASE_1_MISSING_INCLUDE
    result = fixer.fix_code(
        buggy_code=test_case['buggy_code'],
        error_message=test_case['expected_error'],
        error_type=test_case['error_type']
    )
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    if result.success:
        print("✅ Fix successful!")
        print(f"\nDiagnosis: {result.diagnosis}")
        print(f"Confidence: {result.confidence}")
        print(f"\nFixed code:\n{result.fixed_code[:200]}...")
        
        # Validate
        validation = fixer.validate_fix(
            result.original_code,
            result.fixed_code,
            test_case['correct_code']
        )
        print(f"\nValidation:")
        print(f"  Code changed: {validation['code_changed']}")
        print(f"  Has includes: {validation['has_includes']}")
        print(f"  Similarity: {validation['similarity_score']*100:.1f}%")
    else:
        print(f"❌ Fix failed: {result.error}")
