"""
Model Selector - Selección inteligente de modelos LLM según la tarea

Este módulo implementa la estrategia multi-modelo para optimizar:
- Velocidad: Usar modelos pequeños para tareas simples
- Calidad: Usar modelos especializados para código
- RAM: Alternar modelos según necesidad
"""

from typing import Dict, Optional, Literal
from dataclasses import dataclass
import os

TaskType = Literal["analyze", "fix", "validate", "document", "test"]


@dataclass
class ModelConfig:
    """Configuración de un modelo"""
    name: str
    size_gb: float
    speed_tokens_per_sec: float
    specialization: str
    best_for: list[str]
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar"""
        return f"{self.name} ({self.size_gb}GB, {self.speed_tokens_per_sec} tok/s)"


class ModelSelector:
    """
    Selector inteligente de modelos según la tarea.
    
    Estrategia:
    1. Análisis inicial: Modelo rápido y ligero (gemma2:2b, llama3.2:3b)
    2. Fix de código: Modelo especialista (qwen2.5-coder:14b)
    3. Validación: Modelo rápido (gemma2:2b)
    4. Documentación: Modelo balanceado (llama3.2:3b)
    5. Testing: Modelo especialista (qwen2.5-coder:14b)
    
    Ejemplos:
        >>> selector = ModelSelector()
        >>> model = selector.get_model_for_task("fix")
        >>> print(model)  # "qwen2.5-coder:14b"
        
        >>> selector = ModelSelector(strategy="fast")
        >>> model = selector.get_model_for_task("fix")
        >>> print(model)  # "gemma2:2b"
    """
    
    # Catálogo de modelos disponibles
    AVAILABLE_MODELS: Dict[str, ModelConfig] = {
        # Modelos especializados en código
        "qwen2.5-coder:14b": ModelConfig(
            name="qwen2.5-coder:14b",
            size_gb=8.5,
            speed_tokens_per_sec=3.0,
            specialization="code",
            best_for=["fix", "test", "refactor"]
        ),
        "deepseek-coder:16b": ModelConfig(
            name="deepseek-coder:16b",
            size_gb=9.2,
            speed_tokens_per_sec=2.5,
            specialization="code",
            best_for=["fix", "refactor", "complex"]
        ),
        "codellama:13b": ModelConfig(
            name="codellama:13b",
            size_gb=7.4,
            speed_tokens_per_sec=3.5,
            specialization="code",
            best_for=["completion", "snippets"]
        ),
        
        # Modelos balanceados
        "gemma2:9b": ModelConfig(
            name="gemma2:9b",
            size_gb=5.5,
            speed_tokens_per_sec=5.0,
            specialization="general",
            best_for=["analyze", "document", "explain"]
        ),
        
        # Modelos rápidos y ligeros
        "gemma2:2b": ModelConfig(
            name="gemma2:2b",
            size_gb=1.6,
            speed_tokens_per_sec=15.0,
            specialization="general",
            best_for=["analyze", "validate", "classify"]
        ),
        "llama3.2:3b": ModelConfig(
            name="llama3.2:3b",
            size_gb=2.0,
            speed_tokens_per_sec=12.0,
            specialization="general",
            best_for=["document", "explain", "simple"]
        ),
        "llama3.2:1b": ModelConfig(
            name="llama3.2:1b",
            size_gb=1.3,
            speed_tokens_per_sec=20.0,
            specialization="general",
            best_for=["classify", "simple"]
        ),
    }
    
    # Mapeo de tareas a modelos (estrategia optimizada)
    TASK_MODEL_MAPPING: Dict[str, Dict[str, str]] = {
        # Estrategia balanceada (default)
        "balanced": {
            "analyze": "gemma2:2b",        # Rápido para analizar errores
            "fix": "qwen2.5-coder:14b",    # Especialista para fix
            "validate": "gemma2:2b",       # Rápido para validar
            "document": "llama3.2:3b",     # Bueno para explicar
            "test": "qwen2.5-coder:14b",   # Especialista para tests
        },
        
        # Estrategia de máxima calidad
        "quality": {
            "analyze": "gemma2:9b",
            "fix": "qwen2.5-coder:14b",
            "validate": "gemma2:9b",
            "document": "gemma2:9b",
            "test": "qwen2.5-coder:14b",
        },
        
        # Estrategia de máxima velocidad
        "fast": {
            "analyze": "gemma2:2b",
            "fix": "gemma2:2b",
            "validate": "gemma2:2b",
            "document": "llama3.2:1b",
            "test": "gemma2:2b",
        },
        
        # Estrategia de mínimo RAM
        "low_ram": {
            "analyze": "llama3.2:1b",
            "fix": "gemma2:2b",
            "validate": "llama3.2:1b",
            "document": "llama3.2:1b",
            "test": "gemma2:2b",
        },
        
        # Estrategia modelo único (actual)
        "single": {
            "analyze": "qwen2.5-coder:14b",
            "fix": "qwen2.5-coder:14b",
            "validate": "qwen2.5-coder:14b",
            "document": "qwen2.5-coder:14b",
            "test": "qwen2.5-coder:14b",
        },
    }
    
    def __init__(
        self,
        strategy: str = "balanced",
        fallback_model: Optional[str] = None,
        override_model: Optional[str] = None
    ):
        """
        Inicializa el selector de modelos.
        
        Args:
            strategy: Estrategia a usar ("balanced", "quality", "fast", "low_ram", "single")
            fallback_model: Modelo de respaldo si el primario falla
            override_model: Modelo a usar para todas las tareas (útil para testing)
        """
        self.strategy = strategy
        self.fallback_model = fallback_model or "qwen2.5-coder:14b"
        self.override_model = override_model or os.getenv("LLM_MODEL_OVERRIDE")
        
        # Validar estrategia
        if strategy not in self.TASK_MODEL_MAPPING:
            raise ValueError(
                f"Estrategia inválida: {strategy}. "
                f"Opciones: {list(self.TASK_MODEL_MAPPING.keys())}"
            )
    
    def get_model_for_task(self, task_type: TaskType) -> str:
        """
        Obtiene el modelo óptimo para una tarea.
        
        Args:
            task_type: Tipo de tarea ("analyze", "fix", "validate", "document", "test")
            
        Returns:
            Nombre del modelo a usar
            
        Examples:
            >>> selector = ModelSelector()
            >>> selector.get_model_for_task("fix")
            'qwen2.5-coder:14b'
            
            >>> selector.get_model_for_task("analyze")
            'gemma2:2b'
        """
        # Si hay override, usar ese modelo para todo
        if self.override_model:
            return self.override_model
        
        # Obtener modelo según estrategia y tarea
        mapping = self.TASK_MODEL_MAPPING[self.strategy]
        return mapping.get(task_type, self.fallback_model)
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        Obtiene la configuración de un modelo.
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Configuración del modelo o None si no existe
        """
        return self.AVAILABLE_MODELS.get(model_name)
    
    def estimate_memory_usage(self, task_sequence: list[TaskType]) -> float:
        """
        Estima el uso máximo de RAM para una secuencia de tareas.
        
        Args:
            task_sequence: Lista de tareas a ejecutar
            
        Returns:
            RAM estimada en GB
            
        Examples:
            >>> selector = ModelSelector()
            >>> tasks = ["analyze", "fix", "validate"]
            >>> ram = selector.estimate_memory_usage(tasks)
            >>> print(f"{ram:.1f}GB")  # "8.5GB" (peak por fix)
        """
        models_needed = set(
            self.get_model_for_task(task) for task in task_sequence
        )
        
        # El peak será el modelo más grande (no se cargan simultáneos)
        max_ram = 0.0
        for model_name in models_needed:
            config = self.get_model_config(model_name)
            if config:
                max_ram = max(max_ram, config.size_gb)
        
        return max_ram
    
    def estimate_total_time(self, task_sequence: list[TaskType], tokens_per_task: int = 500) -> float:
        """
        Estima el tiempo total para una secuencia de tareas.
        
        Args:
            task_sequence: Lista de tareas a ejecutar
            tokens_per_task: Tokens promedio por tarea
            
        Returns:
            Tiempo estimado en segundos
        """
        total_time = 0.0
        
        for task in task_sequence:
            model_name = self.get_model_for_task(task)
            config = self.get_model_config(model_name)
            
            if config:
                # Tiempo = tokens / velocidad
                task_time = tokens_per_task / config.speed_tokens_per_sec
                total_time += task_time
        
        return total_time
    
    def list_available_models(self, specialization: Optional[str] = None) -> list[str]:
        """
        Lista los modelos disponibles.
        
        Args:
            specialization: Filtrar por especialización ("code", "general")
            
        Returns:
            Lista de nombres de modelos
        """
        if specialization:
            return [
                name for name, config in self.AVAILABLE_MODELS.items()
                if config.specialization == specialization
            ]
        return list(self.AVAILABLE_MODELS.keys())
    
    def get_strategy_info(self) -> Dict[str, str]:
        """
        Obtiene información sobre la estrategia actual.
        
        Returns:
            Diccionario con mapeo tarea -> modelo
        """
        return self.TASK_MODEL_MAPPING[self.strategy].copy()
    
    def compare_strategies(self, task_sequence: list[TaskType]) -> Dict[str, Dict[str, float]]:
        """
        Compara todas las estrategias para una secuencia de tareas.
        
        Args:
            task_sequence: Lista de tareas a ejecutar
            
        Returns:
            Diccionario con métricas por estrategia
            
        Examples:
            >>> selector = ModelSelector()
            >>> tasks = ["analyze", "fix", "validate"]
            >>> comparison = selector.compare_strategies(tasks)
            >>> for strategy, metrics in comparison.items():
            ...     print(f"{strategy}: {metrics['time']:.1f}s, {metrics['ram']:.1f}GB")
        """
        results = {}
        
        for strategy_name in self.TASK_MODEL_MAPPING.keys():
            # Crear selector temporal con esta estrategia
            temp_selector = ModelSelector(strategy=strategy_name)
            
            # Calcular métricas
            ram = temp_selector.estimate_memory_usage(task_sequence)
            time = temp_selector.estimate_total_time(task_sequence)
            
            results[strategy_name] = {
                "ram_gb": ram,
                "time_seconds": time,
                "models_used": len(set(
                    temp_selector.get_model_for_task(task) 
                    for task in task_sequence
                ))
            }
        
        return results


# Factory functions para casos comunes
def create_default_selector() -> ModelSelector:
    """Crea un selector con estrategia balanceada (recomendado)"""
    return ModelSelector(strategy="balanced")


def create_fast_selector() -> ModelSelector:
    """Crea un selector optimizado para velocidad"""
    return ModelSelector(strategy="fast")


def create_quality_selector() -> ModelSelector:
    """Crea un selector optimizado para calidad"""
    return ModelSelector(strategy="quality")


def create_low_ram_selector() -> ModelSelector:
    """Crea un selector optimizado para bajo uso de RAM"""
    return ModelSelector(strategy="low_ram")


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo 1: Uso básico
    print("=" * 80)
    print("EJEMPLO 1: Uso básico")
    print("=" * 80)
    
    selector = create_default_selector()
    
    print(f"\nEstrategia: {selector.strategy}")
    print(f"\nModelo para cada tarea:")
    for task in ["analyze", "fix", "validate", "document"]:
        model = selector.get_model_for_task(task)
        config = selector.get_model_config(model)
        print(f"  {task:12s} → {config.display_name if config else model}")
    
    # Ejemplo 2: Estimaciones
    print("\n" + "=" * 80)
    print("EJEMPLO 2: Estimaciones de recursos")
    print("=" * 80)
    
    task_sequence = ["analyze", "fix", "validate"]
    ram = selector.estimate_memory_usage(task_sequence)
    time = selector.estimate_total_time(task_sequence)
    
    print(f"\nSecuencia: {' → '.join(task_sequence)}")
    print(f"RAM estimada: {ram:.1f}GB")
    print(f"Tiempo estimado: {time:.1f}s")
    
    # Ejemplo 3: Comparación de estrategias
    print("\n" + "=" * 80)
    print("EJEMPLO 3: Comparación de estrategias")
    print("=" * 80)
    
    comparison = selector.compare_strategies(task_sequence)
    
    print(f"\n{'Estrategia':<15} {'RAM (GB)':<12} {'Tiempo (s)':<15} {'Modelos':<10}")
    print("-" * 60)
    for strategy, metrics in comparison.items():
        print(
            f"{strategy:<15} "
            f"{metrics['ram_gb']:<12.1f} "
            f"{metrics['time_seconds']:<15.1f} "
            f"{metrics['models_used']:<10}"
        )
