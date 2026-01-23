"""Base agent template integrating LLM provider and ReAct framework."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .llm_provider import LLMManager, LLMProvider
from .react_agent import ReActAgent, Task, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for base agent."""

    name: str
    description: str
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = "claude-3-5-haiku-20241022"
    temperature: float = 0.7
    max_iterations: int = 10
    timeout: int = 300
    enable_logging: bool = True


@dataclass
class AgentContext:
    """Context information for agent execution."""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Abstract base class for all agents in the system.

    Integrates:
    - LLM provider management
    - ReAct reasoning framework
    - Tool/action execution
    - State management
    - Error handling and logging
    """

    def __init__(self, config: AgentConfig, context: Optional[AgentContext] = None):
        """Initialize base agent.

        Args:
            config: Agent configuration
            context: Execution context
        """
        self.config = config
        self.context = context or AgentContext()

        # Initialize LLM manager
        self.llm_manager = LLMManager()

        # Initialize ReAct agent
        self.react_agent = ReActAgent(
            llm_manager=self.llm_manager,
            provider=config.llm_provider,
            model=config.model,
            max_iterations=config.max_iterations,
            temperature=config.temperature,
            name=config.name,
        )

        # Agent state
        self.state: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []

        if config.enable_logging:
            logger.info(f"Initialized agent: {config.name}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Returns:
            System prompt string
        """

    @abstractmethod
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools for this agent.

        Returns:
            List of tool definitions with name, description, and parameters
        """

    @abstractmethod
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a specific tool.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """

    def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute agent task using ReAct framework.

        Args:
            objective: Task objective/goal
            context: Additional context for execution

        Returns:
            Execution result with status, output, and metadata
        """
        start_time = datetime.utcnow()

        try:
            # Create task
            task = Task(
                id=f"{self.config.name}_{start_time.isoformat()}",
                description=objective,
                context=context or {},
            )

            # Get system prompt and tools
            system_prompt = self.get_system_prompt()
            tools = self.get_available_tools()

            # Execute using ReAct
            result = self.react_agent.solve(
                task=task, system_prompt=system_prompt, tools=tools, tool_executor=self.execute_tool
            )

            # Record execution
            execution_record = {
                "timestamp": start_time.isoformat(),
                "objective": objective,
                "status": result.status.value,
                "result": result.result,
                "iterations": result.iterations,
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }
            self.execution_history.append(execution_record)

            if self.config.enable_logging:
                logger.info(
                    f"Agent {self.config.name} completed: "
                    f"status={result.status.value}, iterations={result.iterations}"
                )

            return {
                "success": result.status == TaskStatus.COMPLETED,
                "status": result.status.value,
                "output": result.result,
                "iterations": result.iterations,
                "reasoning_trace": result.reasoning_trace,
                "metadata": execution_record,
            }

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return {
                "success": False,
                "status": "error",
                "error": error_msg,
                "metadata": {
                    "timestamp": start_time.isoformat(),
                    "objective": objective,
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                },
            }

    def update_state(self, key: str, value: Any) -> None:
        """Update agent state.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get agent state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return self.state.get(key, default)

    def clear_state(self) -> None:
        """Clear agent state."""
        self.state = {}

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get agent execution history.

        Returns:
            List of execution records
        """
        return self.execution_history

    def reset(self) -> None:
        """Reset agent to initial state."""
        self.state = {}
        self.execution_history = []
        if self.config.enable_logging:
            logger.info(f"Reset agent: {self.config.name}")
