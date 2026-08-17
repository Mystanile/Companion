from __future__ import annotations

import json
from typing import Any

from groq import Groq

from companion.tools import TOOL_DEFINITIONS, run_tool

SYSTEM_PROMPT = """You are Companion, a practical desktop assistant on Windows.

Rules:
- Use tools to complete requests. Do not pretend to act.
- Resolve paths like Desktop, Documents, Downloads relative to the user's home folder.
- Prefer open_path for default apps, open_in_editor only when the user names Cursor or VS Code.
- Keep spoken replies short (1-2 sentences).
- If a request is ambiguous, ask one brief clarifying question.
- You may create, edit, rename, move, copy, delete, list, and open files/folders under the user's home directory.
- Be careful with delete_path; only delete when the user clearly asks.
"""


class CompanionAgent:
    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self.client = Groq(api_key=groq_api_key)
        self.model = model
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def handle(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

        for _ in range(6):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.2,
            )
            message = response.choices[0].message
            assistant_message: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
            tool_calls = message.tool_calls or []

            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ]
                self.messages.append(assistant_message)

                for call in tool_calls:
                    args = json.loads(call.function.arguments or "{}")
                    result = run_tool(call.function.name, args)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result,
                        }
                    )
                continue

            reply = (message.content or "").strip()
            if not reply:
                reply = "Done."
            self.messages.append({"role": "assistant", "content": reply})
            self.trim_history()
            return reply

        reply = "I hit a limit trying to finish that. Want to try again?"
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def trim_history(self, max_messages: int = 20) -> None:
        if len(self.messages) <= max_messages:
            return
        system = self.messages[0]
        self.messages = [system, *self.messages[-(max_messages - 1) :]]
