import re
from dataclasses import dataclass
from pathlib import Path

CURATED_REFERENCE_BOOSTS = {
    "Platform": 6,
    "Vote": 4,
    "Ranking": 4,
    "AskMultiple": 5,
    "Catapult": 4,
    "StreetView": 5,
    "TagCloud": 4,
    "SpeechSynthesis": 3,
    "WhereDog": 2,
    "TreasureDoors": 5,
    "ReactionRush": 4,
    "PunchoutMobileGame": 5,
    "MemoryGameWithHiddenSymbols": 5,
    "MemoryMobileGame": 4,
    "Jankenpo": 4,
    "Jumper": 4,
    "JumperMobileGame": 3,
    "HowManyPizza": 4,
    "TopTrumps2": 3,
    "TopTrumps": 4,
    "SafeBox": 4,
    "Crosswords": 5,
    "Dice": 3,
    "FlipCard": 4,
    "Stop": 4,
    "Math1": 3,
    "TicTacToe": 3,
    "MathChallenge": 3,
    "MarioBros": 3,
    "CarGame": 2,
}

CURATED_TEMPLATE_HINTS = {
    "Platform": "platform-hub",
    "Vote": "diagnostic",
    "Ranking": "diagnostic",
    "AskMultiple": "quiz",
    "Catapult": "physics",
    "StreetView": "adventure",
    "TagCloud": "self-development",
    "SpeechSynthesis": "learning",
    "WhereDog": "learning",
    "TreasureDoors": "pick-one",
    "ReactionRush": "reaction",
    "PunchoutMobileGame": "duel",
    "MemoryGameWithHiddenSymbols": "memory",
    "MemoryMobileGame": "memory",
    "Jankenpo": "pick-one",
    "Jumper": "runner",
    "JumperMobileGame": "runner",
    "HowManyPizza": "pattern",
    "TopTrumps": "duel",
    "TopTrumps2": "duel",
    "SafeBox": "pick-one",
    "Crosswords": "crossword",
    "Dice": "pick-one",
    "FlipCard": "memory",
    "Stop": "pattern",
    "Math1": "pattern",
    "TicTacToe": "pattern",
    "MathChallenge": "pattern",
    "MarioBros": "runner",
    "CarGame": "car",
}

NON_GAME_COMPONENTS = {
    "HelloWorld",
    "Client",
    "Client2",
    "Control",
    "Task",
    "TaskAdmin",
    "TaskEdit",
    "TaskList",
    "QuizForm",
    "GameStatsBar",
    "Paused",
    "Screen",
    "Grid",
    "Cell",
    "Map",
    "MapTest",
    "Welcome",
    "LocationBased",
    "Envelope",
    "Youtube",
    "Timer",
    "Fireworks",
    "GameTemplate",
}

LOW_CONFIDENCE_GENERATED_TOKENS = {
    "quick",
    "rounds",
    "mobile",
    "challenge",
    "survival",
    "simple",
    "replayability",
    "live",
    "audience",
}


@dataclass
class GameReference:
    name: str
    path: str
    template_hint: str
    layout_profile: str
    score: int
    excerpt: str


def _tokenize(value: str) -> set[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalized.lower())
        if len(token) > 2
    }


def _template_hint(name: str, content: str) -> str:
    if name in CURATED_TEMPLATE_HINTS:
        return CURATED_TEMPLATE_HINTS[name]

    lowered = f"{name} {content}".lower()
    if (
        "platform" in lowered
        or "modalgame" in lowered
        or "currenttask" in lowered
        or "timeline-item" in lowered
        or "agames" in lowered
        or "closeplatformmodal" in lowered
        or "door.route" in lowered
        or "data/level0" in lowered
    ):
        return "platform-hub"
    if (
        "diagnostic" in lowered
        or "assessment" in lowered
        or "rank" in lowered
        or "ranking" in lowered
        or "leader" in lowered
        or "improvement" in lowered
        or "feedback" in lowered
    ):
        return "diagnostic"
    if (
        "self development" in lowered
        or "self-development" in lowered
        or "reflection" in lowered
        or "tagcloud" in lowered
        or "self" in lowered
        or "growth" in lowered
        or "habit" in lowered
        or "confidence" in lowered
    ):
        return "self-development"
    if (
        "learning" in lowered
        or "teach" in lowered
        or "teaches" in lowered
        or "speech" in lowered
        or "question" in lowered
        or "practice" in lowered
        or "skill" in lowered
    ):
        return "learning"
    if "punch" in lowered or "box" in lowered or "fight" in lowered or "battle" in lowered:
        return "duel"
    if (
        "streetview" in lowered
        or "street view" in lowered
        or "panorama" in lowered
        or "google street" in lowered
        or "location clue" in lowered
        or "guess the place" in lowered
        or "landmark" in lowered
    ):
        return "adventure"
    if (
        "catapult" in lowered
        or "cannon" in lowered
        or "trajectory" in lowered
        or "launch" in lowered
        or "projectile" in lowered
        or "angle" in lowered
        or "power" in lowered
    ):
        return "physics"
    if "car" in lowered or "race" in lowered or "drive" in lowered or "drift" in lowered or "road" in lowered:
        return "car"
    if "jump" in lowered or "runner" in lowered or "obstacle" in lowered or "avoid" in lowered:
        return "runner"
    if "reaction" in lowered or "tempo" in lowered or "rapid" in lowered:
        return "reaction"
    if "memory" in lowered or "sequencia" in lowered or "simbolo" in lowered:
        return "memory"
    if (
        "task" in lowered
        and (
            "door" in lowered
            or "hub" in lowered
            or "portal" in lowered
            or "timeline" in lowered
            or "stage" in lowered
            or "json" in lowered
        )
    ):
        return "platform-hub"
    if (
        "adventure" in lowered
        or "quest" in lowered
        or "explore" in lowered
        or "exploration" in lowered
        or "relic" in lowered
        or "temple" in lowered
        or "journey" in lowered
    ):
        return "adventure"
    if (
        "crossword" in lowered
        or "word search" in lowered
        or "letters" in lowered
        or "spelling" in lowered
        or "anagram" in lowered
    ):
        return "crossword"
    if (
        "multiple choice" in lowered
        or "quiz" in lowered
        or "answer" in lowered
        or "trivia" in lowered
        or "question" in lowered
    ):
        return "quiz"
    if (
        "pattern" in lowered
        or "order" in lowered
        or "sorting" in lowered
        or "crossword" in lowered
        or "word" in lowered
        or "quiz" in lowered
        or "math" in lowered
        or "trivia" in lowered
        or "puzzle" in lowered
    ):
        return "pattern"
    return "pick-one"


def infer_template_hint(name: str, content: str) -> str:
    return _template_hint(name, content)


def _layout_profile(name: str, content: str) -> str:
    lowered = f"{name} {content}".lower()
    if (
        "modalgame" in lowered
        or "timeline-item" in lowered
        or "closeplatformmodal" in lowered
        or "currenttask" in lowered
        or "fullscreen" in lowered
        or "door.route" in lowered
        or "data/level0" in lowered
    ):
        return "task-world"
    if (
        "ranking" in lowered
        or "leader" in lowered
        or "results" in lowered
        or "score total" in lowered
    ):
        return "results-board"
    if (
        "reflection" in lowered
        or "tagcloud" in lowered
        or "speech" in lowered
        or "feedback" in lowered
    ):
        return "reflection-panel"
    if (
        "radio-group" in lowered
        or "v-radio" in lowered
        or "question" in lowered
        or "choices" in lowered
    ):
        return "question-stack"
    if (
        "crossword" in lowered
        or "clue" in lowered
        or "input" in lowered
        or "word" in lowered
    ):
        return "workbench"
    if (
        "combination" in lowered
        or "safe" in lowered
        or "keypad" in lowered
        or "v-btn @click=\"combination" in lowered
    ):
        return "control-panel"
    if (
        "hud" in lowered
        or "card-deck" in lowered
        or "summary" in lowered
        or "buttons" in lowered
    ):
        return "hud-stage"
    if (
        "scene" in lowered
        or "mapa" in lowered
        or "relic" in lowered
        or "journey" in lowered
        or "street-view" in lowered
        or "streetview" in lowered
        or "panorama" in lowered
    ):
        return "split-board"
    return "game-surface"


def _excerpt(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return " ".join(lines[:4])[:240]


def _goal_template_hint(goal: str) -> str:
    return _template_hint("goal", goal)


def _reference_penalty(name: str) -> int:
    if name in CURATED_REFERENCE_BOOSTS:
        return 0

    tokens = _tokenize(name)
    penalty = 0

    if len(tokens) >= 5:
        penalty += 2
    if len(tokens & LOW_CONFIDENCE_GENERATED_TOKENS) >= 2:
        penalty += 2

    return penalty


def select_game_references(goal: str, repo_path: str | None, limit: int = 3) -> list[GameReference]:
    if not repo_path:
        return []

    components_dir = Path(repo_path) / "src" / "components"
    if not components_dir.exists():
        return []

    goal_tokens = _tokenize(goal)
    preferred_template = _goal_template_hint(goal)
    references: list[GameReference] = []

    for file_path in components_dir.glob("*.vue"):
        if not file_path.is_file():
            continue

        if file_path.stem in NON_GAME_COMPONENTS:
            continue

        content = file_path.read_text(encoding="utf-8")
        name_tokens = _tokenize(file_path.stem)
        content_tokens = _tokenize(content)
        overlap = len(goal_tokens & (name_tokens | content_tokens))

        template_hint = _template_hint(file_path.stem, content)
        overlap += CURATED_REFERENCE_BOOSTS.get(file_path.stem, 0)
        overlap -= _reference_penalty(file_path.stem)
        if template_hint == preferred_template:
            overlap += 3
        elif preferred_template in {
            "quiz",
            "crossword",
            "car",
            "runner",
            "memory",
            "duel",
            "reaction",
            "adventure",
            "learning",
            "self-development",
            "diagnostic",
            "physics",
            "platform-hub",
        }:
            overlap -= 1

        if overlap == 0 and file_path.stem not in CURATED_REFERENCE_BOOSTS:
            continue

        references.append(
            GameReference(
                name=file_path.stem,
                path=str(file_path),
                template_hint=template_hint,
                layout_profile=_layout_profile(file_path.stem, content),
                score=overlap,
                excerpt=_excerpt(content),
            )
        )

    references.sort(key=lambda item: (-item.score, item.name))
    return references[:limit]
