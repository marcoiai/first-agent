from datetime import datetime, UTC


def get_current_time() -> str:
    return datetime.now(UTC).isoformat()


def brainstorm_next_steps(goal: str) -> list[str]:
    normalized = goal.strip()
    return [
        f"Clarify the desired outcome for: {normalized}",
        f"Break '{normalized}' into smaller implementation steps",
        "Identify the first concrete action that can be executed now",
    ]
