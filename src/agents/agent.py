import inspect
import json
import re
from typing import Dict, List, Optional

from src.agents.llm_provider import BaseLLM
from src.agents.tools import ToolRegistry


class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        llm: BaseLLM,
        registry: ToolRegistry,
        system_prompt: Optional[str] = None,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.llm = llm
        self.registry = registry
        self.system_prompt = system_prompt or self._generate_default_system_prompt()
        self.memory: List[Dict[str, str]] = []

    def _generate_default_system_prompt(self) -> str:
        tools_info = "\n".join(
            [
                f"- {t.name}: {t.description} (Params: {inspect.signature(t.func)})"
                for t in self.registry.tools.values()
            ]
        )
        return f"""You are {self.name}, {self.role}.
Your goal is: {self.goal}

You have access to the following tools:
{tools_info}

Use the following format:
Thought: you should always think about what to do
Action: the action to take, should be one of [{", ".join(t.name for t in self.registry.tools.values())}]
Action Input: the input to the action (JSON format)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""

    def run(self, user_input: str, max_iterations: int = 5) -> str:
        self.memory = [{"role": "system", "content": self.system_prompt}]
        self.memory.append({"role": "user", "content": user_input})

        for i in range(max_iterations):
            response = self.llm.generate(self.memory)
            content = response.content
            self.memory.append({"role": "assistant", "content": content})

            # Check for Final Answer
            if "Final Answer:" in content:
                return content.split("Final Answer:")[-1].strip()

            # Parse Action and Action Input
            action_match = re.search(r"Action: (.*)", content)
            action_input_match = re.search(r"Action Input: (.*)", content)

            if action_match and action_input_match:
                action_name = action_match.group(1).strip()
                action_input_str = action_input_match.group(1).strip()

                try:
                    action_input = json.loads(action_input_str)
                except json.JSONDecodeError:
                    observation = f"Error: Invalid JSON format for Action Input: {action_input_str}"
                else:
                    tool = self.registry.get_tool(action_name)
                    if tool:
                        try:
                            observation = str(tool.run(**action_input))
                        except Exception as e:
                            observation = f"Error: Tool execution failed: {str(e)}"
                    else:
                        observation = f"Error: Tool '{action_name}' not found."

                self.memory.append({"role": "system", "content": f"Observation: {observation}"})
            else:
                # If no action is found and no final answer, we might be stuck or the LLM is just talking
                if "Thought:" not in content:
                    return content  # Fallback

                # Continue loop to let it try again or finish

        return "Error: Maximum iterations reached without final answer."
