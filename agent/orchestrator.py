"""
Multi-Agent Orchestrator for ESP32 Development Workflow
Coordinates specialized agents for parallel and sequential task execution
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import os
from pathlib import Path

# Import LLM-powered code fixer
from .code_fixer import create_code_fixer, ESP32CodeFixer

# Import event emitter for real-time dashboard updates
from .event_emitter import event_emitter, EventType, emit_log, emit_job_progress, emit_agent_status


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentRole(Enum):
    """Agent roles in the development workflow"""
    PROJECT_MANAGER = "project_manager"  # Coordinates workflow, imports projects
    DEVELOPER = "developer"              # Writes/fixes code
    BUILDER = "builder"                  # Compiles firmware
    TESTER = "tester"                    # Runs flash/QEMU tests
    DOCTOR = "doctor"                    # Hardware diagnostics
    QA = "qa"                           # Validates and reports issues


@dataclass
class Task:
    """Individual task in the workflow"""
    id: str
    role: AgentRole
    action: str
    dependencies: List[str]  # Task IDs that must complete first
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    can_parallelize: bool = False


@dataclass
class WorkflowState:
    """Current state of the development workflow"""
    project_path: str
    target: str
    current_phase: str
    tasks: Dict[str, Task]
    artifacts: Dict[str, Any]
    qa_iterations: int = 0
    max_qa_iterations: int = 3


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents for ESP32 development.
    Handles task dependencies, parallelization, and feedback loops.
    """
    
    def __init__(self, langchain_tools: List[Any], llm_provider: str = "ollama", llm_model: Optional[str] = None):
        """
        Initialize orchestrator with LangChain tools and LLM-powered code fixer.
        
        Args:
            langchain_tools: List of LangChain-wrapped MCP tools
            llm_provider: LLM provider for code fixing ("ollama", "openai", "anthropic")
            llm_model: Optional specific model name (defaults per provider)
        """
        self.tools = {tool.name: tool for tool in langchain_tools}
        self.state: Optional[WorkflowState] = None
        self.agent_roles = self._initialize_agents()
        self.current_job_id: Optional[int] = None  # Track current job for event emission
        
        # Initialize LLM-powered code fixer
        self.code_fixer = create_code_fixer(provider=llm_provider, model=llm_model)
        print(f"🤖 Code fixer initialized: {llm_provider} ({self.code_fixer.model})")
    
    async def _emit_event(self, level: str, message: str, agent_id: Optional[str] = None):
        """Emit log event to dashboard."""
        try:
            await emit_log(level, message, agent_id=agent_id, job_id=self.current_job_id)
        except Exception as e:
            print(f"⚠️  Failed to emit event: {e}")
    
    async def _emit_progress(self, phase: str, progress: int, message: str, agent_id: Optional[str] = None):
        """Emit progress event to dashboard."""
        try:
            if self.current_job_id:
                await emit_job_progress(self.current_job_id, phase, progress, message, agent_id=agent_id)
        except Exception as e:
            print(f"⚠️  Failed to emit progress: {e}")
    
    async def _update_agent_status(self, agent_id: str, status: str):
        """Update agent status in dashboard."""
        try:
            await emit_agent_status(agent_id, status)
        except Exception as e:
            print(f"⚠️  Failed to update agent status: {e}")

        
    def _initialize_agents(self) -> Dict[AgentRole, Dict[str, Any]]:
        """Define agent roles and their capabilities"""
        return {
            AgentRole.PROJECT_MANAGER: {
                "tools": ["list_files", "read_source_file", "idf_set_target"],
                "responsibilities": [
                    "Import/validate project structure",
                    "Set target chip",
                    "Coordinate workflow phases"
                ]
            },
            AgentRole.DEVELOPER: {
                "tools": ["read_source_file", "write_source_file", "list_files"],
                "responsibilities": [
                    "Create/modify source code",
                    "Fix bugs reported by QA",
                    "Implement new features"
                ]
            },
            AgentRole.BUILDER: {
                "tools": ["idf_build", "idf_clean", "idf_size", "get_build_artifacts"],
                "responsibilities": [
                    "Compile firmware",
                    "Generate build artifacts",
                    "Report build errors"
                ]
            },
            AgentRole.TESTER: {
                "tools": [
                    "idf_flash", "run_qemu_simulation", "stop_qemu_simulation",
                    "qemu_simulation_status", "qemu_get_output"
                ],
                "responsibilities": [
                    "Flash to hardware (parallel)",
                    "Run QEMU simulation (parallel)",
                    "Collect test outputs"
                ]
            },
            AgentRole.DOCTOR: {
                "tools": ["idf_doctor", "qemu_inspect_state"],
                "responsibilities": [
                    "Validate hardware setup",
                    "Check environment",
                    "Inspect simulation state"
                ]
            },
            AgentRole.QA: {
                "tools": [
                    "qemu_get_output", "read_source_file", "list_files", "idf_size"
                ],
                "responsibilities": [
                    "Analyze test results",
                    "Detect failures/anomalies",
                    "Report issues to Developer",
                    "Validate fixes"
                ]
            }
        }
    
    async def execute_workflow(
        self,
        project_path: str,
        target: str = "esp32",
        flash_device: bool = True,
        run_qemu: bool = True,
        job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute complete development workflow with parallelization.
        
        Args:
            project_path: Path to ESP-IDF project
            target: Target chip (esp32, esp32c6, etc.)
            flash_device: Whether to flash physical device
            run_qemu: Whether to run QEMU simulation
            job_id: Optional job ID for tracking in dashboard
            
        Returns:
            Workflow results with all task outcomes
        """
        # Track job for event emission
        self.current_job_id = job_id
        
        # Emit workflow start
        await self._emit_event("INFO", f"🚀 Starting workflow for project: {project_path}")
        await self._emit_progress("init", 0, "Initializing workflow")
        
        # Initialize workflow state
        self.state = WorkflowState(
            project_path=project_path,
            target=target,
            current_phase="initialization",
            tasks={},
            artifacts={}
        )
        
        await self._emit_event("INFO", f"Target chip: {target}")
        
        # Define workflow phases
        workflow = await self._create_workflow_plan(flash_device, run_qemu)
        
        # Execute workflow with parallelization
        results = await self._execute_tasks(workflow)
        
        return {
            "success": self.state.current_phase == "completed",
            "phases": results,
            "qa_iterations": self.state.qa_iterations,
            "artifacts": self.state.artifacts
        }
    
    async def _create_workflow_plan(
        self, flash_device: bool, run_qemu: bool
    ) -> List[Task]:
        """
        Create workflow task plan with dependencies and parallelization.
        
        Workflow phases:
        1. Project Setup (sequential)
        2. Build (sequential)
        3. Testing (parallel: flash + QEMU)
        4. Validation (parallel: doctor + QA analysis)
        5. Feedback Loop (if QA finds issues)
        """
        tasks = []
        
        # Phase 1: Project Setup (sequential)
        tasks.append(Task(
            id="setup_project",
            role=AgentRole.PROJECT_MANAGER,
            action="validate_project_structure",
            dependencies=[],
            status=TaskStatus.PENDING
        ))
        
        tasks.append(Task(
            id="set_target",
            role=AgentRole.PROJECT_MANAGER,
            action="set_chip_target",
            dependencies=["setup_project"],
            status=TaskStatus.PENDING
        ))
        
        # Phase 2: Build (sequential)
        tasks.append(Task(
            id="build_firmware",
            role=AgentRole.BUILDER,
            action="compile_and_cache",
            dependencies=["set_target"],
            status=TaskStatus.PENDING
        ))
        
        # Phase 3: Testing (PARALLEL)
        if flash_device:
            tasks.append(Task(
                id="flash_device",
                role=AgentRole.TESTER,
                action="flash_to_hardware",
                dependencies=["build_firmware"],
                status=TaskStatus.PENDING,
                can_parallelize=True  # Can run parallel with QEMU
            ))
        
        if run_qemu:
            tasks.append(Task(
                id="run_simulation",
                role=AgentRole.TESTER,
                action="start_qemu",
                dependencies=["build_firmware"],
                status=TaskStatus.PENDING,
                can_parallelize=True  # Can run parallel with flash
            ))
        
        # Phase 4: Validation (PARALLEL)
        validation_deps = []
        if flash_device:
            validation_deps.append("flash_device")
        if run_qemu:
            validation_deps.append("run_simulation")
        
        tasks.append(Task(
            id="hardware_check",
            role=AgentRole.DOCTOR,
            action="run_diagnostics",
            dependencies=validation_deps,
            status=TaskStatus.PENDING,
            can_parallelize=True  # Can run parallel with QA
        ))
        
        tasks.append(Task(
            id="qa_analysis",
            role=AgentRole.QA,
            action="analyze_results",
            dependencies=validation_deps,
            status=TaskStatus.PENDING,
            can_parallelize=True  # Can run parallel with doctor
        ))
        
        return tasks
    
    async def _execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Execute tasks respecting dependencies and parallelizing when possible.
        
        Returns:
            Results organized by phase
        """
        # Build task lookup
        task_map = {task.id: task for task in tasks}
        self.state.tasks = task_map
        
        completed_tasks = set()
        results = {}
        
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = []
            parallel_tasks = []
            
            for task_id, task in task_map.items():
                if task_id in completed_tasks:
                    continue
                    
                # Check if dependencies are met
                deps_met = all(dep in completed_tasks for dep in task.dependencies)
                
                if deps_met and task.status == TaskStatus.PENDING:
                    if task.can_parallelize:
                        parallel_tasks.append(task)
                    else:
                        ready_tasks.append(task)
            
            # Execute sequential tasks first
            for task in ready_tasks:
                result = await self._execute_task(task)
                results[task.id] = result
                completed_tasks.add(task.id)
                
                # Check for QA feedback loop
                if task.id == "qa_analysis" and not result.get("passed", True):
                    if self.state.qa_iterations < self.state.max_qa_iterations:
                        # Add fix and rebuild tasks
                        await self._handle_qa_feedback(task_map, result)
                    else:
                        print(f"⚠️  Max QA iterations reached ({self.state.max_qa_iterations})")
            
            # Execute parallel tasks concurrently
            if parallel_tasks:
                parallel_results = await asyncio.gather(
                    *[self._execute_task(task) for task in parallel_tasks],
                    return_exceptions=True
                )
                
                for task, result in zip(parallel_tasks, parallel_results):
                    if isinstance(result, Exception):
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                        results[task.id] = {"success": False, "error": str(result)}
                    else:
                        results[task.id] = result
                    completed_tasks.add(task.id)
            
            # Break if no progress
            if not ready_tasks and not parallel_tasks:
                break
        
        return results
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task using appropriate agent tools"""
        print(f"🚀 Executing [{task.role.value}] {task.action} (task: {task.id})")
        task.status = TaskStatus.IN_PROGRESS
        task.timestamp = datetime.now()
        
        try:
            # Route task to appropriate handler
            if task.action == "validate_project_structure":
                result = await self._project_manager_validate()
            elif task.action == "set_chip_target":
                result = await self._project_manager_set_target()
            elif task.action == "compile_and_cache":
                result = await self._builder_compile()
            elif task.action == "flash_to_hardware":
                result = await self._tester_flash()
            elif task.action == "start_qemu":
                result = await self._tester_qemu()
            elif task.action == "run_diagnostics":
                result = await self._doctor_check()
            elif task.action == "analyze_results":
                result = await self._qa_analyze()
            elif task.action == "fix_issues":
                result = await self._developer_fix(task.result.get("issues", []))
            else:
                result = {"success": False, "error": f"Unknown action: {task.action}"}
            
            task.status = TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED
            task.result = result
            
            print(f"✅ Completed [{task.role.value}] {task.action}")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            print(f"❌ Failed [{task.role.value}] {task.action}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_qa_feedback(
        self, task_map: Dict[str, Task], qa_result: Dict[str, Any]
    ):
        """
        Handle QA feedback loop: Developer fixes -> Rebuild -> Retest
        
        Args:
            task_map: Current task map
            qa_result: QA analysis with detected issues
        """
        self.state.qa_iterations += 1
        print(f"\n🔄 QA Feedback Loop - Iteration {self.state.qa_iterations}")
        print(f"   Issues found: {len(qa_result.get('issues', []))}")
        
        # Create fix task
        fix_task = Task(
            id=f"fix_issues_{self.state.qa_iterations}",
            role=AgentRole.DEVELOPER,
            action="fix_issues",
            dependencies=[],
            status=TaskStatus.PENDING
        )
        fix_task.result = {"issues": qa_result.get("issues", [])}
        
        # Add to workflow
        task_map[fix_task.id] = fix_task
        
        # Execute fix
        await self._execute_task(fix_task)
        
        # Rebuild
        rebuild_task = Task(
            id=f"rebuild_{self.state.qa_iterations}",
            role=AgentRole.BUILDER,
            action="compile_and_cache",
            dependencies=[fix_task.id],
            status=TaskStatus.PENDING
        )
        task_map[rebuild_task.id] = rebuild_task
        await self._execute_task(rebuild_task)
        
        # Retest
        retest_task = Task(
            id=f"retest_{self.state.qa_iterations}",
            role=AgentRole.QA,
            action="analyze_results",
            dependencies=[rebuild_task.id],
            status=TaskStatus.PENDING
        )
        task_map[retest_task.id] = retest_task
        await self._execute_task(retest_task)
    
    # Agent action implementations
    
    async def _project_manager_validate(self) -> Dict[str, Any]:
        """Validate project structure"""
        tool = self.tools["list_files"]
        result = tool.invoke(".")
        return {
            "success": "CMakeLists.txt" in result,
            "structure": result
        }
    
    async def _project_manager_set_target(self) -> Dict[str, Any]:
        """Set target chip"""
        tool = self.tools["idf_set_target"]
        result = tool.invoke(self.state.target)
        return {"success": True, "output": result}
    
    async def _builder_compile(self) -> Dict[str, Any]:
        """Compile firmware and cache artifacts"""
        await self._update_agent_status("build", "active")
        await self._emit_event("INFO", "🔨 Build agent compiling firmware", agent_id="build")
        await self._emit_progress("build", 0, "Starting compilation", agent_id="build")
        
        tool = self.tools["idf_build"]
        result = tool.invoke("")
        
        success = "error" not in result.lower()
        
        if success:
            await self._emit_progress("build", 50, "Compilation successful, getting artifacts", agent_id="build")
            # Get artifacts
            artifacts_tool = self.tools["get_build_artifacts"]
            artifacts = artifacts_tool.invoke("")
            self.state.artifacts["build"] = artifacts
            
            await self._emit_progress("build", 100, "Build completed successfully", agent_id="build")
            await self._emit_event("SUCCESS", "✅ Build successful", agent_id="build")
        else:
            await self._emit_event("ERROR", "❌ Build failed", agent_id="build")
            artifacts = None
        
        await self._update_agent_status("build", "idle")
        
        return {
            "success": success,
            "output": result,
            "artifacts": artifacts
        }
    
    async def _tester_flash(self) -> Dict[str, Any]:
        """Flash to hardware using cached artifacts"""
        tool = self.tools["idf_flash"]
        result = tool.invoke({
            "port": "/dev/cu.usbmodem21101",
            "use_cached": True
        })
        return {
            "success": "successfully" in result.lower(),
            "output": result
        }
    
    async def _tester_qemu(self) -> Dict[str, Any]:
        """Start QEMU simulation"""
        tool = self.tools["run_qemu_simulation"]
        result = tool.invoke({"target": self.state.target})
        
        # Wait for simulation to start
        await asyncio.sleep(3)
        
        # Get output
        output_tool = self.tools["qemu_get_output"]
        output = output_tool.invoke({"lines": 100})
        
        self.state.artifacts["qemu_output"] = output
        
        return {
            "success": True,
            "output": output
        }
    
    async def _doctor_check(self) -> Dict[str, Any]:
        """Run hardware diagnostics"""
        tool = self.tools["idf_doctor"]
        result = tool.invoke("")
        return {
            "success": "error" not in result.lower(),
            "report": result
        }
    
    async def _qa_analyze(self) -> Dict[str, Any]:
        """
        Analyze test results and detect issues.
        
        QA checks:
        - Build success
        - QEMU output analysis
        - Flash success
        - Memory usage
        - Expected behaviors
        """
        await self._update_agent_status("test", "active")
        await self._emit_event("INFO", "🔍 Test agent analyzing results", agent_id="test")
        await self._emit_progress("validate", 0, "Starting validation", agent_id="test")
        
        issues = []
        
        # Check build
        if "build" in self.state.artifacts:
            await self._emit_progress("validate", 25, "Checking build artifacts", agent_id="test")
            build_info = self.state.artifacts["build"]
            if "error" in str(build_info).lower():
                issues.append({
                    "severity": "high",
                    "component": "build",
                    "message": "Build errors detected"
                })
                await self._emit_event("WARNING", "⚠️  Build errors detected", agent_id="test")
        
        # Check QEMU output
        if "qemu_output" in self.state.artifacts:
            await self._emit_progress("validate", 50, "Analyzing QEMU output", agent_id="test")
            output = self.state.artifacts["qemu_output"]
            
            # Check for expected patterns
            if "Hello World" not in output:
                issues.append({
                    "severity": "high",
                    "component": "application",
                    "message": "Expected 'Hello World' output not found in QEMU"
                })
                await self._emit_event("WARNING", "⚠️  Expected output not found", agent_id="test")
            
            # Check for errors/warnings
            if "error" in output.lower() or "abort" in output.lower():
                issues.append({
                    "severity": "medium",
                    "component": "runtime",
                    "message": "Runtime errors detected in QEMU output"
                })
        
        # Generate report
        passed = len(issues) == 0
        
        await self._emit_progress("validate", 100, f"Validation complete: {len(issues)} issues found", agent_id="test")
        
        if passed:
            await self._emit_event("SUCCESS", "✅ All validations passed", agent_id="test")
        else:
            await self._emit_event("WARNING", f"⚠️  Found {len(issues)} issues", agent_id="test")
        
        await self._update_agent_status("test", "idle")
        
        return {
            "success": True,
            "passed": passed,
            "issues": issues,
            "report": f"QA Analysis: {'PASSED' if passed else 'FAILED'}\n"
                     f"Issues found: {len(issues)}"
        }
    
    async def _developer_fix(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fix issues reported by QA using LLM-powered code analysis.
        
        Uses ESP32CodeFixer to analyze build errors and generate fixes.
        Reads buggy code from files, applies fixes, and writes back.
        """
        print(f"🔧 Developer fixing {len(issues)} issues with LLM...")
        await self._update_agent_status("developer", "active")
        await self._emit_event("INFO", f"🔧 Developer agent fixing {len(issues)} issues", agent_id="developer")
        await self._emit_progress("fix", 0, f"Starting to fix {len(issues)} issues", agent_id="developer")
        
        fixes_applied = []
        fixes_failed = []
        
        for idx, issue in enumerate(issues, 1):
            progress = int((idx / len(issues)) * 100)
            print(f"\n   [{idx}/{len(issues)}] {issue['severity']}: {issue['message']}")
            await self._emit_progress("fix", progress, f"Fixing issue {idx}/{len(issues)}", agent_id="developer")
            
            # Extract file path and error details
            file_path = issue.get("file")
            component = issue.get("component", "unknown")
            error_message = issue.get("message", "")
            
            if not file_path or not os.path.exists(file_path):
                print(f"   ⚠️  File not found: {file_path}")
                fixes_failed.append({
                    "issue": error_message,
                    "reason": "File not accessible",
                    "component": component
                })
                continue
            
            try:
                # Read buggy code
                with open(file_path, 'r', encoding='utf-8') as f:
                    buggy_code = f.read()
                
                print(f"   🔍 Analyzing {Path(file_path).name}...")
                
                # Use LLM to fix the code
                result = self.code_fixer.fix_code(
                    buggy_code=buggy_code,
                    error_message=error_message,
                    filename=Path(file_path).name,
                    component=component
                )
                
                if result.success and result.fixed_code:
                    # Write fixed code back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(result.fixed_code)
                    
                    print(f"   ✅ Fixed! Confidence: {result.confidence}")
                    print(f"   📝 Changes: {result.changes_made}")
                    await self._emit_event("SUCCESS", f"✅ Fixed {Path(file_path).name}: {result.changes_made[:100]}", agent_id="developer")
                    
                    fixes_applied.append({
                        "issue": error_message,
                        "fix": result.changes_made,
                        "component": component,
                        "file": file_path,
                        "confidence": result.confidence,
                        "diagnosis": result.diagnosis
                    })
                else:
                    print(f"   ❌ Failed: {result.error}")
                    await self._emit_event("WARNING", f"❌ Failed to fix {Path(file_path).name}: {result.error}", agent_id="developer")
                    fixes_failed.append({
                        "issue": error_message,
                        "reason": result.error or "LLM could not generate fix",
                        "component": component
                    })
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                fixes_failed.append({
                    "issue": error_message,
                    "reason": f"Exception: {str(e)}",
                    "component": component
                })
        
        success = len(fixes_applied) > 0
        
        print(f"\n📊 Fix Summary:")
        print(f"   ✅ Applied: {len(fixes_applied)}")
        print(f"   ❌ Failed: {len(fixes_failed)}")
        
        await self._emit_progress("fix", 100, f"Completed: {len(fixes_applied)} fixes applied, {len(fixes_failed)} failed", agent_id="developer")
        await self._update_agent_status("developer", "idle")
        
        if success:
            await self._emit_event("SUCCESS", f"🎉 Developer agent completed: {len(fixes_applied)} fixes applied", agent_id="developer")
        else:
            await self._emit_event("ERROR", f"❌ Developer agent failed to apply any fixes", agent_id="developer")
        
        return {
            "success": success,
            "fixes": fixes_applied,
            "failures": fixes_failed
        }
    
    def get_workflow_summary(self) -> str:
        """Get human-readable workflow summary"""
        if not self.state:
            return "No workflow executed yet"
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║             ESP32 Development Workflow Summary               ║
╚══════════════════════════════════════════════════════════════╝

📁 Project: {self.state.project_path}
🎯 Target: {self.state.target}
🔄 QA Iterations: {self.state.qa_iterations}/{self.state.max_qa_iterations}

Tasks:
"""
        for task_id, task in self.state.tasks.items():
            status_icon = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.PENDING: "⏳",
                TaskStatus.BLOCKED: "🚫"
            }.get(task.status, "❓")
            
            summary += f"  {status_icon} [{task.role.value}] {task.action}\n"
        
        return summary
