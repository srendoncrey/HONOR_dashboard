"""Base agent class with Claude API agentic loop."""

import json
import anthropic


class BaseAgent:
    """Base class for all agents. Handles the Claude tool_use agentic loop."""

    name = "base"
    model = "claude-haiku-4-5-20251001"
    system_prompt = ""
    tool_definitions = []

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self._handlers = {}

    def register_tool(self, name, handler):
        self._handlers[name] = handler

    def run(self, user_message: str, max_turns: int = 10) -> str:
        messages = [{"role": "user", "content": user_message}]

        for _ in range(max_turns):
            response = self.client.messages.create(
                model=self.model,
                system=self.system_prompt,
                messages=messages,
                tools=self.tool_definitions,
                max_tokens=4096,
            )

            # Collect text and tool_use blocks
            text_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if text_parts:
                print(f"  [{self.name}] {text_parts[0][:200]}")

            if response.stop_reason == "end_turn" or not tool_calls:
                return "\n".join(text_parts)

            # Execute tool calls
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for tc in tool_calls:
                handler = self._handlers.get(tc.name)
                if handler:
                    try:
                        result = handler(**tc.input)
                        result_str = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                    except Exception as e:
                        result_str = f"Error: {e}"
                else:
                    result_str = f"Error: unknown tool '{tc.name}'"
                print(f"  [{self.name}] tool:{tc.name} -> {result_str[:150]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })
            messages.append({"role": "user", "content": tool_results})

        return "\n".join(text_parts) if text_parts else "Max turns reached."
