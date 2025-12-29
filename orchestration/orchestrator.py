"""Enhanced Orchestrator - Manages multiple agents and coordinates workflows."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import sys
sys.path.append('../agents')
from base_agent import BaseAgent


logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentTask:
    """Task to be executed by an agent."""
    id: str
    agent_name: str
    objective: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: int = 300
    dependencies: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class WorkflowDefinition:
    """Workflow definition with tasks and dependencies."""
    id: str
    name: str
    description: str
    tasks: List[AgentTask]
    context: Dict[str, Any] = field(default_factory=dict)
    max_parallel: int = 3
    timeout: int = 1800


class Orchestrator:
    """Enhanced orchestrator for managing multiple agents and workflows.
    
    Features:
    - Agent registration and management
    - Task dependency resolution
    - Parallel execution with configurable concurrency
    - Timeout handling
    - Error recovery
    - Workflow state management
    - Execution history and metrics
    """
    
    def __init__(self, max_workers: int = 5):
        """Initialize orchestrator.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"Orchestrator initialized with {max_workers} workers")
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator.
        
        Args:
            name: Agent name/identifier
            agent: Agent instance
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str) -> None:
        """Unregister an agent.
        
        Args:
            name: Agent name to unregister
        """
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Unregistered agent: {name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get registered agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(name)
    
    def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create and register a workflow.
        
        Args:
            definition: Workflow definition
            
        Returns:
            Workflow ID
        """
        self.workflows[definition.id] = definition
        logger.info(f"Created workflow: {definition.name} ({definition.id})")
        return definition.id
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a single agent task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task execution result
        """
        agent = self.agents.get(task.agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {task.agent_name}")
        
        task.status = WorkflowStatus.RUNNING
        task.start_time = datetime.utcnow()
        
        try:
            # Execute with timeout
            future = self.executor.submit(
                agent.execute,
                task.objective,
                task.context
            )
            
            result = future.result(timeout=task.timeout)
            
            task.status = WorkflowStatus.COMPLETED if result.get('success') else WorkflowStatus.FAILED
            task.result = result
            
            if not result.get('success'):
                task.error = result.get('error', 'Unknown error')
            
        except TimeoutError:
            task.status = WorkflowStatus.TIMEOUT
            task.error = f"Task timeout after {task.timeout}s"
            logger.error(f"Task {task.id} timed out")
            
        except Exception as e:
            task.status = WorkflowStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
        
        finally:
            task.end_time = datetime.utcnow()
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "duration_seconds": (task.end_time - task.start_time).total_seconds() if task.start_time else 0
        }
    
    def resolve_dependencies(self, tasks: List[AgentTask]) -> List[List[AgentTask]]:
        """Resolve task dependencies and group tasks by execution level.
        
        Args:
            tasks: List of tasks
            
        Returns:
            List of task groups (levels) that can be executed in parallel
        """
        task_map = {task.id: task for task in tasks}
        levels: List[List[AgentTask]] = []
        completed_tasks = set()
        
        while len(completed_tasks) < len(tasks):
            current_level = []
            
            for task in tasks:
                if task.id in completed_tasks:
                    continue
                
                # Check if all dependencies are completed
                deps_met = all(dep_id in completed_tasks for dep_id in task.dependencies)
                
                if deps_met:
                    current_level.append(task)
            
            if not current_level:
                # Circular dependency detected
                remaining = [t.id for t in tasks if t.id not in completed_tasks]
                raise ValueError(f"Circular dependency detected in tasks: {remaining}")
            
            # Sort by priority within level
            current_level.sort(key=lambda t: t.priority.value, reverse=True)
            levels.append(current_level)
            
            # Mark tasks as scheduled
            completed_tasks.update(task.id for task in current_level)
        
        return levels
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow with dependency resolution and parallel execution.
        
        Args:
            workflow_id: Workflow ID to execute
            
        Returns:
            Workflow execution result
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        start_time = datetime.utcnow()
        logger.info(f"Starting workflow: {workflow.name} ({workflow_id})")
        
        try:
            # Resolve task dependencies
            task_levels = self.resolve_dependencies(workflow.tasks)
            
            results = []
            failed_tasks = []
            
            # Execute tasks level by level
            for level_idx, level_tasks in enumerate(task_levels):
                logger.info(f"Executing level {level_idx + 1}/{len(task_levels)} with {len(level_tasks)} tasks")
                
                # Execute tasks in parallel with max_parallel limit
                for i in range(0, len(level_tasks), workflow.max_parallel):
                    batch = level_tasks[i:i + workflow.max_parallel]
                    
                    # Submit batch for parallel execution
                    futures = [
                        self.executor.submit(self.execute_task, task)
                        for task in batch
                    ]
                    
                    # Wait for batch to complete
                    for future, task in zip(futures, batch):
                        try:
                            result = future.result(timeout=task.timeout)
                            results.append(result)
                            
                            if task.status != WorkflowStatus.COMPLETED:
                                failed_tasks.append(task)
                                
                        except Exception as e:
                            logger.error(f"Task execution error: {e}")
                            failed_tasks.append(task)
                
                # Stop if critical task failed
                if any(t.priority == TaskPriority.CRITICAL for t in failed_tasks):
                    logger.error("Critical task failed, stopping workflow")
                    break
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            execution_record = {
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tasks": len(workflow.tasks),
                "completed_tasks": len([t for t in workflow.tasks if t.status == WorkflowStatus.COMPLETED]),
                "failed_tasks": len(failed_tasks),
                "results": results
            }
            
            self.execution_history.append(execution_record)
            
            success = len(failed_tasks) == 0
            logger.info(
                f"Workflow {workflow.name} {'completed' if success else 'failed'}: "
                f"{len(results)} tasks in {duration:.2f}s"
            )
            
            return {
                "success": success,
                "workflow_id": workflow_id,
                "execution_record": execution_record,
                "failed_tasks": [{
                    "id": t.id,
                    "agent": t.agent_name,
                    "error": t.error
                } for t in failed_tasks]
            }
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": error_msg
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow status information
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "total_tasks": len(workflow.tasks),
            "pending": len([t for t in workflow.tasks if t.status == WorkflowStatus.PENDING]),
            "running": len([t for t in workflow.tasks if t.status == WorkflowStatus.RUNNING]),
            "completed": len([t for t in workflow.tasks if t.status == WorkflowStatus.COMPLETED]),
            "failed": len([t for t in workflow.tasks if t.status == WorkflowStatus.FAILED])
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get orchestrator execution history.
        
        Returns:
            List of execution records
        """
        return self.execution_history
    
    def shutdown(self) -> None:
        """Shutdown orchestrator and cleanup resources."""
        logger.info("Shutting down orchestrator")
        self.executor.shutdown(wait=True)
