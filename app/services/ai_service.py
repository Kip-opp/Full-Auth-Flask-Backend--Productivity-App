import requests
from datetime import datetime


class AIService:
    def __init__(self, app=None):
        self.app = app

    def ask_grok(self, prompt, todos=None):
        if not self.app:
            raise ValueError("AIService requires Flask app context/app instance")

        api_key = self.app.config.get("XAI_API_KEY")
        base_url = self.app.config.get("XAI_BASE_URL")
        model = self.app.config.get("XAI_MODEL")

        if not api_key:
            return {
                "success": False,
                "response": "Missing XAI_API_KEY in environment variables."
            }

        todo_context = self._format_todos_for_prompt(todos or [])

        system_prompt = (
            "You are an AI productivity assistant for a todo app. "
            "Help the user prioritize tasks, schedule tasks, break down work, "
            "and suggest next actions clearly and practically."
        )

        user_prompt = f"""
Current date/time: {datetime.utcnow().isoformat()} UTC

User request:
{prompt}

Current todos:
{todo_context}

Instructions:
- Keep the answer practical.
- If asked to schedule, suggest an ordered plan.
- If asked to break down a task, give clear steps.
- If priorities are unclear, recommend priorities.
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]

            return {
                "success": True,
                "response": content
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "response": f"Grok API request failed: {str(e)}"
            }
        except (KeyError, IndexError, TypeError):
            return {
                "success": False,
                "response": "Unexpected response format from Grok API."
            }

    def _format_todos_for_prompt(self, todos):
        if not todos:
            return "No todos available."

        lines = []
        for todo in todos:
            due = todo.due_date.isoformat() if todo.due_date else "No due date"
            status = "Done" if todo.completed else "Pending"
            lines.append(
                f"- {todo.title} | {status} | Priority: {todo.priority} | Due: {due}"
            )
        return "\n".join(lines)