from difflib import SequenceMatcher
from pathlib import Path

from first_agent.config import get_settings
from first_agent.feedback_store import FeedbackStore
from first_agent.game_generator import (
    GameGenerationRequest,
    GeneratedGame,
    build_generation_request,
    build_system_prompt,
    build_user_prompt,
    generate_game,
)
from first_agent.ideation import (
    generate_idea,
    generate_idea_for_category,
    get_prompt_suggestions,
    infer_category_from_engine,
    list_suggestion_families,
)
from first_agent.memory import AgentMemory
from first_agent.reference_library import infer_template_hint, select_game_references
from first_agent.reviewer import review_and_refine_game
from first_agent.tools import brainstorm_next_steps, get_current_time
from first_agent.writer import Entert2Writer

SIMILARITY_THRESHOLD = 0.86
NOVELTY_ATTEMPTS = 4
DEFAULT_APP_BASE_URL = "https://127.0.0.1:8081"


class FirstAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = self._build_client()
        self.feedback_store = FeedbackStore(
            self.settings.feedback_store_path,
            self.settings.last_generation_path,
        )

    def _build_client(self):
        if not self.settings.openai_api_key:
            return None
        try:
            from openai import OpenAI
        except ModuleNotFoundError:
            return None
        return OpenAI(api_key=self.settings.openai_api_key)

    def run(self, goal: str) -> str:
        references = select_game_references(goal, self.settings.entert2_path)
        request, game, review, novelty_note = self._generate_with_novelty(goal, self.settings.entert2_path, references)
        self._record_generation(goal, game, references, review)
        memory = AgentMemory(goal=goal)
        memory.remember_observation(f"Goal received at {get_current_time()}")
        next_steps = brainstorm_next_steps(goal)
        memory.remember_action("Generated local next-step plan")
        memory.remember_observation(
            "Review status: " + ("passed" if review.passed else "needs attention")
        )
        if novelty_note:
            memory.remember_observation(novelty_note)
        if references:
            memory.remember_observation(
                "Reference games: " + ", ".join(reference.name for reference in references)
            )

        if self.client is None:
            return self._fallback_response(game, references, review, novelty_note)

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
                        f"{build_user_prompt(request, references=references)}\n"
                        f"Current observations: {memory.observations}\n"
                        f"Planning hints: {next_steps}"
                    )
                },
            ],
        )
        memory.remember_action("Asked the model for an execution-oriented response")
        return response.output_text.strip()

    def write_directly(self, goal: str, repo_path: str | None = None) -> str:
        target_repo = repo_path or self.settings.entert2_path
        references = select_game_references(goal, target_repo)
        request, game, _review, _novelty_note = self._generate_with_novelty(goal, target_repo, references)
        self._record_generation(goal, game, references, _review)
        writer = Entert2Writer(target_repo)
        written_paths = writer.write(game)
        route_url = f"{DEFAULT_APP_BASE_URL}/#/{request.component_key}"
        return "\n".join(
            [
                f"Open URL: {route_url}",
                *[f"- {path}" for path in written_paths],
            ]
        )

    def record_feedback(self, outcome: str, game_name: str | None = None) -> str:
        target = self.feedback_store.record_feedback(outcome, game_name=game_name)
        return (
            f"Recorded {outcome} for {target['game_name']}.\n"
            f"Engine: {target['engine_name']}\n"
            f"Idea: {target['idea']}"
        )

    def show_last_generation(self) -> str:
        generation = self.feedback_store.get_last_generation()
        if not generation:
            return "No stored generation found yet."

        lines = [
            f"Goal: {generation.get('goal', '-')}",
            f"Idea: {generation.get('idea', '-')}",
            f"Game: {generation.get('game_name', '-')}",
            f"Component key: {generation.get('component_key', '-')}",
            f"Engine: {generation.get('engine_name', '-')}",
            f"Category: {generation.get('experience_category', '-')}",
            f"Route: {generation.get('route_url', '-')}",
            f"Recommendation: {generation.get('review_recommendation', '-')}",
        ]

        review_average = generation.get("review_average")
        if review_average is not None:
            lines.append(f"Review average: {review_average}/10")

        review_scores = generation.get("review_scores") or {}
        if review_scores:
            lines.append(
                "Scores: "
                + ", ".join(f"{name} {value}" for name, value in review_scores.items())
            )

        references = generation.get("references") or []
        if references:
            lines.append("References: " + ", ".join(references))

        failed_checks = generation.get("failed_checks") or []
        if failed_checks:
            lines.append("Failed checks: " + ", ".join(failed_checks))

        return "\n".join(lines)

    def write_last_generation(self, repo_path: str | None = None) -> str:
        generation = self.feedback_store.get_last_generation()
        if not generation:
            return "No stored generation found yet."

        target_repo = repo_path or self.settings.entert2_path
        game = self._game_from_generation(generation)
        if game is None:
            idea = generation.get("idea") or generation.get("goal")
            if not idea:
                return "Last generation is missing the idea needed to rebuild it."
            return self.write_directly(idea, repo_path=target_repo)

        writer = Entert2Writer(target_repo)
        written_paths = writer.write(game)
        route_url = generation.get("route_url") or f"{DEFAULT_APP_BASE_URL}/#/{game.request.component_key}"
        return "\n".join(
            [
                f"Open URL: {route_url}",
                *[f"- {path}" for path in written_paths],
            ]
        )

    def auto_run(self, seed: str | None = None, repo_path: str | None = None) -> str:
        idea = generate_idea(seed, repo_path=repo_path or self.settings.entert2_path)
        return self.run(idea)

    def auto_write(self, repo_path: str | None = None, seed: str | None = None, category: str | None = None) -> str:
        target_repo = repo_path or self.settings.entert2_path
        if category:
            idea = generate_idea_for_category(category, seed=seed, repo_path=target_repo)
        else:
            idea = generate_idea(seed, repo_path=target_repo)
        return self.write_directly(idea, repo_path=target_repo)

    def auto_run_for_category(self, category: str, seed: str | None = None, repo_path: str | None = None) -> str:
        idea = generate_idea_for_category(category, seed=seed, repo_path=repo_path or self.settings.entert2_path)
        return self.run(idea)

    def show_suggestions(self, family: str | None = None) -> str:
        suggestions = get_prompt_suggestions(family)
        if family and not suggestions.get(family):
            available = ", ".join(list_suggestion_families())
            return f"No suggestion family named '{family}'. Available families: {available}"

        lines: list[str] = []
        for suggestion_family, prompts in suggestions.items():
            lines.append(f"[{suggestion_family}]")
            lines.extend(f"- {prompt}" for prompt in prompts)
            lines.append("")
        return "\n".join(lines).strip()

    def _fallback_response(self, game, references, review, novelty_note: str | None = None) -> str:
        lines = [
            f"Idea: {game.request.idea}",
            f"Game: {game.request.game_name}",
            f"Engine: {game.engine_name}",
            f"Planned route if written: {DEFAULT_APP_BASE_URL}/#/{game.request.component_key}",
            (
                "Quality: "
                f"{review.scorecard.average}/10"
                f" (clarity {review.scorecard.clarity}, interactivity {review.scorecard.interactivity}, "
                f"originality {review.scorecard.originality}, visual {review.scorecard.visual}, "
                f"theme {review.scorecard.theme_fit}, utility {review.scorecard.utility})"
            ),
            f"Recommendation: {review.recommendation}",
            "Status: generated locally only. Use --write or --write-last to publish it into entert2.",
        ]
        if references:
            lines.append("References: " + ", ".join(reference.name for reference in references))
        if not review.passed:
            lines.append(
                "Review: needs attention on "
                + ", ".join(check.name for check in review.checks if not check.passed)
            )
        if novelty_note:
            lines.append(f"Novelty: {novelty_note}")
        return "\n".join(lines)

    def _record_generation(self, goal: str, game, references, review) -> None:
        self.feedback_store.record_generation(
            {
                "goal": goal,
                "idea": game.request.idea,
                "game_name": game.request.game_name,
                "component_key": game.request.component_key,
                "engine_name": game.engine_name,
                "component_code": game.component_code,
                "screen_code": game.screen_code,
                "main_import": game.main_import,
                "task_entry": game.task_entry,
                "route_entry": game.route_entry,
                "screen_render": game.screen_render,
                "screen_component": game.screen_component,
                "client_render": game.client_render,
                "client_component": game.client_component,
                "experience_category": infer_category_from_engine(game.engine_name),
                "references": [reference.name for reference in references],
                "route_url": f"{DEFAULT_APP_BASE_URL}/#/{game.request.component_key}",
                "review_average": review.scorecard.average,
                "review_recommendation": review.recommendation,
                "review_scores": {
                    "clarity": review.scorecard.clarity,
                    "interactivity": review.scorecard.interactivity,
                    "originality": review.scorecard.originality,
                    "visual": review.scorecard.visual,
                    "theme_fit": review.scorecard.theme_fit,
                    "utility": review.scorecard.utility,
                },
                "failed_checks": [check.name for check in review.checks if not check.passed],
            }
        )

    def _game_from_generation(self, payload: dict) -> GeneratedGame | None:
        required_fields = [
            "idea",
            "game_name",
            "component_key",
            "engine_name",
            "component_code",
            "screen_code",
            "main_import",
            "task_entry",
            "route_entry",
            "screen_render",
            "screen_component",
            "client_render",
            "client_component",
        ]
        if any(not payload.get(field) for field in required_fields):
            return None

        request = GameGenerationRequest(
            idea=payload["idea"],
            game_name=payload["game_name"],
            component_key=payload["component_key"],
            variant_seed=0,
        )
        return GeneratedGame(
            request=request,
            engine_name=payload["engine_name"],
            component_code=payload["component_code"],
            screen_code=payload["screen_code"],
            main_import=payload["main_import"],
            task_entry=payload["task_entry"],
            route_entry=payload["route_entry"],
            screen_render=payload["screen_render"],
            screen_component=payload["screen_component"],
            client_render=payload["client_render"],
            client_component=payload["client_component"],
        )

    def _generate_with_novelty(self, goal: str, repo_path: str, references):
        best_candidate = None
        best_similarity = None
        best_match = None

        for variant_seed in range(NOVELTY_ATTEMPTS):
            request = build_generation_request(goal, variant_seed=variant_seed)
            game = generate_game(request, references=references)
            review = review_and_refine_game(game)
            game = review.game
            similarity, match_name = self._max_similarity(game.engine_name, game.component_code, repo_path, game.request.game_name)

            if best_candidate is None or similarity < best_similarity:
                best_candidate = (request, game, review)
                best_similarity = similarity
                best_match = match_name

            if similarity < SIMILARITY_THRESHOLD:
                note = f"closest existing match {match_name} at similarity {similarity:.2f}" if match_name else None
                return request, game, review, note

        request, game, review = best_candidate
        note = None
        if best_match:
            note = f"kept least-similar variant; closest match {best_match} at similarity {best_similarity:.2f}"
        return request, game, review, note

    def _max_similarity(self, engine_name: str, component_code: str, repo_path: str, game_name: str) -> tuple[float, str | None]:
        components_dir = Path(repo_path) / "src" / "components"
        if not components_dir.exists():
            return 0.0, None

        engine_parts = set(engine_name.split("+"))
        normalized_candidate = self._normalize_component(component_code)
        best_similarity = 0.0
        best_match = None

        for file_path in components_dir.glob("*.vue"):
            if not file_path.is_file() or file_path.stem == game_name:
                continue
            content = file_path.read_text(encoding="utf-8")
            existing_engine = infer_template_hint(file_path.stem, content)
            if engine_parts.isdisjoint(set(existing_engine.split("+"))):
                continue
            similarity = SequenceMatcher(
                None,
                normalized_candidate,
                self._normalize_component(content),
            ).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = file_path.stem

        return best_similarity, best_match

    def _normalize_component(self, content: str) -> str:
        normalized = content.lower()
        normalized = " ".join(normalized.split())
        normalized = normalized.replace("generated game", "")
        return normalized
