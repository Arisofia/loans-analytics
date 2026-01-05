"""ReAct Agent - Reasoning and Acting framework for multi-agent system.

Implements the ReAct (Reasoning + Acting) pattern where agents:
1. Think about the task (Reasoning)
2. Execute actions using tools (Acting)
3. Observe results
4. Repeat until goal is achieved
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .llm_provider import LLMManager, LLMProvider

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of reasoning steps."""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    ANSWER = "answer"


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""

    step_type: StepType
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict] = None
    tool_output: Optional[Any] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task definition for agent execution."""

    id: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    iterations: int = 0
    reasoning_trace: List[str] = field(default_factory=list)


@dataclass
class Tool:
    """Tool definition for agent actions."""

    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)

    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        try:
            return self.function(**kwargs)
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            raise


class ReActAgent:
    """ReAct pattern agent with reasoning and tool execution."""

    REACT_PROMPT = """You are an AI agent that solves problems by reasoning step-by-step and taking actions.

Available tools:
{tools_description}

Use this format:
Thought: [your reasoning about what to do next]
Action: [tool name]
Action Input: {{"param": "value"}}
Observation: [result will be provided]
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Answer: [your final answer]

Task: {task}

Begin!
"""

    def __init__(
        self,
        llm_manager: LLMManager,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "gpt-4",
        max_iterations: int = 10,
        temperature: float = 0.7,
        name: str = "ReActAgent",
    ):
        self.llm_manager = llm_manager
        self.provider = provider
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.name = name
        self.tools = {}
        self.reasoning_chain: List[ReasoningStep] = []

    def register_tool(self, tool: Tool):
        """Register a new tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def _format_tools_description(self, tools: Optional[List[Dict]] = None) -> str:
        """Format tools for prompt."""
        if tools:
            # Format from list of dicts (as passed by BaseAgent)
            descriptions = []
            for tool in tools:
                name = tool.get("name")
                desc = tool.get("description")
                params = tool.get("parameters", {})
                descriptions.append(
                    f"- {name}: {desc}\n  Parameters: {json.dumps(params, indent=2)}"
                )
            return "\n".join(descriptions)

        if not self.tools:
            return "No tools available."

        descriptions = []
        for name, tool in self.tools.items():
            param_desc = (
                json.dumps(tool.parameters, indent=2) if tool.parameters else "No parameters"
            )
            descriptions.append(f"- {name}: {tool.description}\n  Parameters: {param_desc}")

        return "\n".join(descriptions)

    def _parse_llm_response(self, response: str) -> ReasoningStep:
        """Parse LLM response into reasoning step."""
        response = response.strip()

        # Check for final answer
        if "Answer:" in response:
            answer_match = re.search(r"Answer:\s*(.+)", response, re.DOTALL)
            if answer_match:
                return ReasoningStep(
                    step_type=StepType.ANSWER, content=answer_match.group(1).strip()
                )

        # Check for action
        if "Action:" in response:
            thought_match = re.search(r"Thought:\s*(.+?)\n", response)
            action_match = re.search(r"Action:\s*(.+?)\n", response)
            input_match = re.search(r"Action Input:\s*(.+)", response, re.DOTALL)

            if action_match:
                tool_name = action_match.group(1).strip()
                tool_input = {}

                if input_match:
                    try:
                        # Try to find JSON in the input match
                        input_text = input_match.group(1).strip()
                        json_match = re.search(r"(\{.*\})", input_text, re.DOTALL)
                        if json_match:
                            tool_input = json.loads(json_match.group(1))
                        else:
                            tool_input = json.loads(input_text)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse action input: {input_match.group(1)}")

                return ReasoningStep(
                    step_type=StepType.ACTION,
                    content=thought_match.group(1).strip() if thought_match else "",
                    tool_name=tool_name,
                    tool_input=tool_input,
                )

        # Default to thought
        thought_match = re.search(r"Thought:\s*(.+)", response, re.DOTALL)
        content = thought_match.group(1).strip() if thought_match else response

        return ReasoningStep(step_type=StepType.THOUGHT, content=content)

    def solve(
        self, task: Task, system_prompt: str, tools: List[Dict[str, Any]], tool_executor: Callable
    ) -> Task:
        """Solve a task using the ReAct framework.

        Matches the interface expected by BaseAgent.
        """
        task.status = TaskStatus.IN_PROGRESS
        self.reasoning_chain = []

        # Build initial prompt
        tools_desc = self._format_tools_description(tools)
        full_system_prompt = f"{system_prompt}\n\n{self.REACT_PROMPT.format(tools_description=tools_desc, task=task.description)}"

        if task.context:
            full_system_prompt += f"\n\nContext:\n{json.dumps(task.context, indent=2)}"

        messages = [{"role": "system", "content": full_system_prompt}]

        for iteration in range(self.max_iterations):
            task.iterations = iteration + 1
            logger.info(f"Iteration {task.iterations}/{self.max_iterations}")

            try:
                # Get LLM response
                llm_response = self.llm_manager.complete(
                    messages=messages,
                    provider=self.provider.value,
                    model=self.model,
                    temperature=self.temperature,
                )

                # Parse response
                step = self._parse_llm_response(llm_response.content)
                self.reasoning_chain.append(step)
                task.reasoning_trace.append(llm_response.content)

                # Check if done
                if step.step_type == StepType.ANSWER:
                    logger.info(f"Agent completed task in {task.iterations} iterations")
                    task.status = TaskStatus.COMPLETED
                    task.result = step.content
                    return task

                # Execute action if needed
                if step.step_type == StepType.ACTION:
                    observation_result = tool_executor(step.tool_name, step.tool_input)
                    observation = f"Observation: {json.dumps(observation_result)}"

                    # Add observation to chain
                    obs_step = ReasoningStep(
                        step_type=StepType.OBSERVATION,
                        content=observation,
                        tool_output=observation_result,
                    )
                    self.reasoning_chain.append(obs_step)
                    task.reasoning_trace.append(observation)

                    # Add to messages
                    messages.append({"role": "assistant", "content": llm_response.content})
                    messages.append({"role": "user", "content": observation})
                else:
                    # Continue reasoning
                    messages.append({"role": "assistant", "content": llm_response.content})
                    messages.append(
                        {
                            "role": "user",
                            "content": "Please continue with your next Thought or Action.",
                        }
                    )

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                task.status = TaskStatus.FAILED
                task.result = str(e)
                return task

        task.status = TaskStatus.FAILED
        task.result = "Max iterations reached without answer"
        return task

    def run(self, task_description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Legacy run method for backward compatibility."""
        task = Task(
            id=f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            description=task_description,
            context=context or {},
        )

        # We need a system prompt and tools for solve()
        # This is a bit tricky if called via run() directly without those
        # For now, let's assume it's mostly called via BaseAgent.execute()
        result_task = self.solve(
            task=task,
            system_prompt="You are a helpful assistant.",
            tools=[],
            tool_executor=lambda name, input: {"error": "Tool executor not provided"},
        )

        return {
            "success": result_task.status == TaskStatus.COMPLETED,
            "answer": result_task.result,
            "reasoning_chain": self.reasoning_chain,
            "iterations": result_task.iterations,
        }
