from first_agent.config import get_settings
from first_agent.game_generator import (
    build_fallback_output,
    build_generation_request,
    generate_game,
    build_system_prompt,
    build_user_prompt,
)
from first_agent.ideation import generate_idea
from first_agent.memory import AgentMemory
from first_agent.tools import brainstorm_next_steps, get_current_time
from first_agent.writer import Entert2Writer


class FirstAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = self._build_client()

    def _build_client(self):
        if not self.settings.openai_api_key:
            return None
        try:
            from openai import OpenAI
        except ModuleNotFoundError:
            return None
        return OpenAI(api_key=self.settings.openai_api_key)

    def run(self, goal: str) -> str:
        request = build_generation_request(goal)
        game = generate_game(request)
        memory = AgentMemory(goal=goal)
        memory.remember_observation(f"Goal received at {get_current_time()}")
        next_steps = brainstorm_next_steps(goal)
        memory.remember_action("Generated local next-step plan")

        if self.client is None:
            return self._fallback_response(memory, next_steps, game)

        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": (
                        f"{build_user_prompt(request)}\n"
                        f"Current observations: {memory.observations}\n"
                        f"Planning hints: {next_steps}"
                    )
                },
            ],
        )
        memory.remember_action("Asked the model for an execution-oriented response")
        return response.output_text.strip()

    def write_directly(self, goal: str, repo_path: str | None = None) -> str:
        request = build_generation_request(goal)
        game = generate_game(request)
        writer = Entert2Writer(repo_path or self.settings.entert2_path)
        written_paths = writer.write(game)
        route_url = f"http://localhost:8080/#/{request.component_key}"
        return "\n".join(
            [
                f"Wrote {request.game_name} directly into entert2.",
                f"Open URL: {route_url}",
                *[f"- {path}" for path in written_paths],
            ]
        )

    def auto_run(self, seed: str | None = None, repo_path: str | None = None) -> str:
        idea = generate_idea(seed, repo_path=repo_path or self.settings.entert2_path)
        return self.run(idea)

    def auto_write(self, repo_path: str | None = None, seed: str | None = None) -> str:
        target_repo = repo_path or self.settings.entert2_path
        idea = generate_idea(seed, repo_path=target_repo)
        return self.write_directly(idea, repo_path=target_repo)

    def _fallback_response(
        self,
        memory: AgentMemory,
        next_steps: list[str],
        game,
    ) -> str:
        plan = "\n".join(
            [
                f"{self.settings.agent_name} fallback mode",
                f"Goal: {memory.goal}",
                f"Observations: {'; '.join(memory.observations)}",
                "Planned next steps:",
                *[f"- {step}" for step in next_steps],
                "Immediate action: Generate a first-pass component scaffold for entert2.",
            ]
        )
        return f"{plan}\n\n{build_fallback_output(game)}"
