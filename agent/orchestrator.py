"""
Multi-Agent Orchestrator for ESP32 Development Workflow
Coordinates specialized agents for parallel and sequential task execution
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


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
    
    def __init__(self, langchain_tools: List[Any]):
        """
        Initialize orchestrator with LangChain tools.
        
        Args:
            langchain_tools: List of LangChain-wrapped MCP tools
        """
        self.tools = {tool.name: tool for tool in langchain_tools}
        self.state: Optional[WorkflowState] = None
        self.agent_roles = self._initialize_agents()
        
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
        run_qemu: bool = True
    ) -> Dict[str, Any]:
        """
        Execute complete development workflow with parallelization.
        
        Args:
            project_path: Path to ESP-IDF project
            target: Target chip (esp32, esp32c6, etc.)
            flash_device: Whether to flash physical device
            run_qemu: Whether to run QEMU simulation
            
        Returns:
            Workflow results with all task outcomes
        """
        # Initialize workflow state
        self.state = WorkflowState(
            project_path=project_path,
            target=target,
            current_phase="initialization",
            tasks={},
            artifacts={}
        )
        
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
        tool = self.tools["idf_build"]
        result = tool.invoke("")
        
        # Get artifacts
        artifacts_tool = self.tools["get_build_artifacts"]
        artifacts = artifacts_tool.invoke("")
        self.state.artifacts["build"] = artifacts
        
        return {
            "success": "error" not in result.lower(),
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
        issues = []
        
        # Check build
        if "build" in self.state.artifacts:
            build_info = self.state.artifacts["build"]
            if "error" in str(build_info).lower():
                issues.append({
                    "severity": "high",
                    "component": "build",
                    "message": "Build errors detected"
                })
        
        # Check QEMU output
        if "qemu_output" in self.state.artifacts:
            output = self.state.artifacts["qemu_output"]
            
            # Check for expected patterns
            if "Hello World" not in output:
                issues.append({
                    "severity": "high",
                    "component": "application",
                    "message": "Expected 'Hello World' output not found in QEMU"
                })
            
            # Check for errors/warnings
            if "error" in output.lower() or "abort" in output.lower():
                issues.append({
                    "severity": "medium",
                    "component": "runtime",
                    "message": "Runtime errors detected in QEMU output"
                })
        
        # Generate report
        passed = len(issues) == 0
        
        return {
            "success": True,
            "passed": passed,
            "issues": issues,
            "report": f"QA Analysis: {'PASSED' if passed else 'FAILED'}\n"
                     f"Issues found: {len(issues)}"
        }
    
    async def _developer_fix(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fix issues reported by QA.
        
        This is a placeholder - in production, this would use an LLM
        to analyze issues and generate code fixes.
        """
        print(f"🔧 Developer fixing {len(issues)} issues...")
        
        fixes_applied = []
        for issue in issues:
            print(f"   - {issue['severity']}: {issue['message']}")
            fixes_applied.append({
                "issue": issue["message"],
                "fix": "Applied automatic fix",  # Placeholder
                "component": issue["component"]
            })
        
        return {
            "success": True,
            "fixes": fixes_applied
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
