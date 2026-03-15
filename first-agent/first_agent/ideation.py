import random
from pathlib import Path

from first_agent.game_generator import build_generation_request


MECHANICS = [
    "reaction challenge with color changes",
    "memory game with symbols",
    "risk and reward door picking game",
    "timed tapping challenge",
    "pattern recognition puzzle",
    "guess the hidden order game",
    "double or nothing treasure picking game",
    "tap sequence survival challenge",
    "hidden trap path game",
    "speed sorting mini game",
]

THEMES = [
    "for event participants",
    "with a playful competition vibe",
    "for quick rounds on mobile",
    "for a live audience screen",
    "with simple scoring and replayability",
    "for head to head team turns",
    "with push your luck decisions",
    "with escalating risk each round",
]


def _existing_component_names(repo_path: str | None = None) -> set[str]:
    if not repo_path:
        return set()

    components_path = Path(repo_path) / "src" / "components"
    if not components_path.exists():
        return set()

    return {
        file_path.stem.lower()
        for file_path in components_path.glob("*.vue")
        if file_path.is_file()
    }


def _candidate_ideas(rng: random.Random) -> list[str]:
    ideas = [f"{mechanic} {theme}" for mechanic in MECHANICS for theme in THEMES]
    rng.shuffle(ideas)
    return ideas


def generate_idea(seed: str | None = None, repo_path: str | None = None) -> str:
    rng = random.Random(seed)
    existing_names = _existing_component_names(repo_path)

    for idea in _candidate_ideas(rng):
        request = build_generation_request(idea)
        if request.game_name.lower() not in existing_names:
            return idea

    fallback_idea = rng.choice(MECHANICS) + " " + rng.choice(THEMES)
    suffix = rng.randint(2, 99)
    return f"{fallback_idea} variant {suffix}"
