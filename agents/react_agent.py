"""ReAct Agent - Reasoning and Acting framework for multi-agent system.

Implements the ReAct (Reasoning + Acting) pattern where agents:
1. Think about the task (Reasoning)
2. Execute actions using tools (Acting)
3. Observe results
4. Repeat until goal is achieved
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re

from .llm_provider import LLMManager, LLMResponse

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of reasoning steps."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    ANSWER = "answer"


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
Action Input: {"param": "value"}
Observation: [result will be provided]
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Answer: [your final answer]

Task: {task}

Begin!
"""
    
    def __init__(
        self,
        name: str,
        llm_manager: LLMManager,
        tools: List[Tool] = None,
        max_iterations: int = 10,
        temperature: float = 0.7
    ):
        self.name = name
        self.llm_manager = llm_manager
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.reasoning_chain: List[ReasoningStep] = []
    
    def register_tool(self, tool: Tool):
        """Register a new tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def _format_tools_description(self) -> str:
        """Format tools for prompt."""
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        for name, tool in self.tools.items():
            param_desc = json.dumps(tool.parameters, indent=2) if tool.parameters else "No parameters"
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
                    step_type=StepType.ANSWER,
                    content=answer_match.group(1).strip()
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
                        tool_input = json.loads(input_match.group(1).strip())
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse action input: {input_match.group(1)}")
                
                return ReasoningStep(
                    step_type=StepType.ACTION,
                    content=thought_match.group(1).strip() if thought_match else "",
                    tool_name=tool_name,
                    tool_input=tool_input
                )
        
        # Default to thought
        thought_match = re.search(r"Thought:\s*(.+)", response, re.DOTALL)
        content = thought_match.group(1).strip() if thought_match else response
        
        return ReasoningStep(
            step_type=StepType.THOUGHT,
            content=content
        )
    
    def _execute_tool(self, step: ReasoningStep) -> str:
        """Execute a tool and return observation."""
        if not step.tool_name or step.tool_name not in self.tools:
            return f"Error: Tool '{step.tool_name}' not found"
        
        tool = self.tools[step.tool_name]
        try:
            result = tool.execute(**(step.tool_input or {}))
            step.tool_output = result
            return f"Observation: {str(result)}"
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def run(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run the ReAct agent on a task."""
        self.reasoning_chain = []
        
        # Build initial prompt
        tools_desc = self._format_tools_description()
        prompt = self.REACT_PROMPT.format(
            tools_description=tools_desc,
            task=task
        )
        
        if context:
            prompt += f"\n\nContext:\n{json.dumps(context, indent=2)}"
        
        messages = [{"role": "system", "content": prompt}]
        conversation_history = []
        
        for iteration in range(self.max_iterations):
            logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                # Get LLM response
                llm_response = self.llm_manager.complete(
                    messages=messages,
                    temperature=self.temperature
                )
                
                # Parse response
                step = self._parse_llm_response(llm_response.content)
                step.confidence = llm_response.confidence
                self.reasoning_chain.append(step)
                
                conversation_history.append(llm_response.content)
                
                # Check if done
                if step.step_type == StepType.ANSWER:
                    logger.info(f"Agent completed task in {iteration + 1} iterations")
                    return {
                        "success": True,
                        "answer": step.content,
                        "reasoning_chain": self.reasoning_chain,
                        "iterations": iteration + 1,
                        "conversation_history": conversation_history
                    }
                
                # Execute action if needed
                if step.step_type == StepType.ACTION:
                    observation = self._execute_tool(step)
                    
                    # Add observation to chain
                    obs_step = ReasoningStep(
                        step_type=StepType.OBSERVATION,
                        content=observation
                    )
                    self.reasoning_chain.append(obs_step)
                    conversation_history.append(observation)
                    
                    # Add observation to messages
                    messages.append({
                        "role": "assistant",
                        "content": llm_response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": observation
                    })
                else:
                    # Continue reasoning
                    messages.append({
                        "role": "assistant",
                        "content": llm_response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": "Continue..."
                    })
            
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "reasoning_chain": self.reasoning_chain,
                    "iterations": iteration + 1
                }
        
        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached without answer")
        return {
            "success": False,
            "error": "Max iterations reached",
            "reasoning_chain": self.reasoning_chain,
            "iterations": self.max_iterations,
            "partial_answer": self.reasoning_chain[-1].content if self.reasoning_chain else None
        }
    
    def get_reasoning_summary(self) -> str:
        """Get a human-readable summary of the reasoning chain."""
        if not self.reasoning_chain:
            return "No reasoning chain available."
        
        summary = []
        for i, step in enumerate(self.reasoning_chain, 1):
            if step.step_type == StepType.THOUGHT:
                summary.append(f"{i}. Thought: {step.content}")
            elif step.step_type == StepType.ACTION:
                summary.append(f"{i}. Action: {step.tool_name} with {step.tool_input}")
            elif step.step_type == StepType.OBSERVATION:
                summary.append(f"{i}. Observation: {step.content}")
            elif step.step_type == StepType.ANSWER:
                summary.append(f"{i}. Final Answer: {step.content}")
        
        return "\n".join(summary)
