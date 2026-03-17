import json
from pathlib import Path


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


class FeedbackStore:
    def __init__(self, feedback_path: str, last_generation_path: str) -> None:
        self.feedback_path = Path(feedback_path)
        self.last_generation_path = Path(last_generation_path)

    def _ensure_parent(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def get_feedback(self) -> dict:
        return _read_json(
            self.feedback_path,
            {
                "engines": {},
                "history": [],
            },
        )

    def get_last_generation(self) -> dict | None:
        return _read_json(self.last_generation_path, None)

    def record_generation(self, payload: dict) -> None:
        self._ensure_parent(self.last_generation_path)
        self.last_generation_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def record_feedback(self, outcome: str, game_name: str | None = None) -> dict:
        feedback = self.get_feedback()
        generation = self.get_last_generation()

        target = generation if generation and (game_name is None or generation.get("game_name") == game_name) else None
        if target is None and generation is None:
            raise ValueError("No previous generation found to review.")
        if target is None:
            raise ValueError(f"No stored generation found for {game_name}.")

        engine = target["engine_name"]
        engine_stats = feedback["engines"].setdefault(engine, {"approved": 0, "rejected": 0})
        if outcome == "approved":
            engine_stats["approved"] += 1
        else:
            engine_stats["rejected"] += 1

        feedback["history"].append(
            {
                "game_name": target["game_name"],
                "idea": target["idea"],
                "engine_name": engine,
                "outcome": outcome,
                "review_average": target.get("review_average"),
                "review_recommendation": target.get("review_recommendation"),
                "review_scores": target.get("review_scores", {}),
            }
        )
        feedback["history"] = feedback["history"][-50:]

        self._ensure_parent(self.feedback_path)
        self.feedback_path.write_text(
            json.dumps(feedback, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        return target
