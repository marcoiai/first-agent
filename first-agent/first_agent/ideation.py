import random
from pathlib import Path

from first_agent.config import get_settings
from first_agent.feedback_store import FeedbackStore
from first_agent.game_generator import build_generation_request


ENGINE_IDEAS = {
    "learning": [
        "active listening rescue where each response calms a tense conversation",
        "time management control room where players triage urgent requests",
        "decision lab with practical tradeoffs and immediate explanations",
        "communication coaching rounds where each choice unlocks a stronger reply",
    ],
    "self-development": [
        "communication mirror that reveals behavior patterns and next actions",
        "focus habits check in with strengths, blind spots and growth advice",
        "self awareness pulse with reflective prompts and improvement guidance",
        "confidence ladder where each choice builds a practical next move",
    ],
    "diagnostic": [
        "leadership radar that finds strengths and hidden improvement areas",
        "collaboration checkup with score interpretation and coaching advice",
        "productivity blocker finder with practical fixes after each result",
        "diagnostic path that shows what to improve next and why",
    ],
    "pick-one": [
        "festival vault pick where everyone chooses one panel and chases the jackpot",
        "crowd prize wall where one panel hides a rare bonus and others hide decoys",
        "mystery artifact pick for online participants with instant reveal and risk escalation",
        "sealed chest showdown where every attendee locks one choice before the reveal",
    ],
    "reaction": [
        "laser timing arena where online participants strike only on the green pulse",
        "perfect tap spotlight for a live crowd countdown and shared leaderboard",
        "signal storm reflex game with fake-outs, streak pressure and many simultaneous players",
        "color pulse reflex wall with combo scoring for the whole event",
    ],
    "memory": [
        "rune sequence recall with escalating patterns and one final showdown",
        "hidden icon recall where the board scrambles after each reveal",
        "team signal memory relay with visible sequence and rising tension",
        "orb pattern recall with escalating difficulty and recovery rounds",
    ],
    "pattern": [
        "tile ordering puzzle where each attendee races to repair the same disrupted board",
        "pattern decoding table with numbered cards and fragile lives for online participants",
        "sorting conveyor with visible targets and pressure rounds for the event room",
        "sequence repair board for event screens with escalating complexity and compareable scores",
    ],
    "physics": [
        "catapult skill shot where players tune angle and power to hit spotlight targets",
        "festival launch lab with moving distance goals, risky power boosts and crowd replay moments",
        "arcade trajectory challenge where each attendee chases the perfect landing window",
        "cannon calibration game with visible physics knobs and jackpot zones on the stage",
    ],
    "quiz": [
        "spotlight trivia quiz ladder with score streaks, harder final questions and shared ranking",
        "four choice quiz showdown with limited lives and comeback moments for the full audience",
        "event question quiz board with instant feedback, dramatic reveals and simultaneous play",
        "escalating quiz climb where each correct answer powers the next tier for everyone online",
    ],
    "crossword": [
        "clue board where each solved word lights up the next hint",
        "hidden word workbench with visible slots and tension from mistakes",
        "letter forge puzzle where players assemble answers from drifting options",
        "spelling lock with clue cards and answer slots",
    ],
    "adventure": [
        "temple relic expedition with risky paths and fading energy",
        "forked exploration map with hidden rewards and danger choices",
        "jungle relic hunt with danger decisions and treasure progress",
        "story path adventure with map nodes and high risk events",
    ],
    "platform-hub": [
        "task world hub with unlockable doors and side progress timeline",
        "scrolling portal map where each door opens a different mission task",
        "platform-style task plaza with collectible unlocks and live progress rail",
        "mission street hub with staged scenes, portal doors and task history",
        "vertical task tower with reachable blocks and buildings on upper ledges",
        "climbable mission stack where some doors live on higher platforms",
    ],
    "variety": [
        "festival gauntlet mixing memory, quiz, reflex and treasure picks for everyone online",
        "multi stage arena with a different mechanic every round and event-wide score race",
        "party circuit that rotates through puzzle, reflex and choice phases for the whole audience",
        "all in one showdown with escalating mixed mechanics and shared ranking tension",
    ],
    "duel": [
        "boxing read-and-react duel with counter windows and stamina swings",
        "arcade fight with block, dodge and punish decisions",
        "telegraphed punch duel with readable enemy cues and momentum",
        "head to head clash with three combat responses and pressure rounds",
    ],
    "runner": [
        "skyline jump runner with speeding obstacles and rescue beacons",
        "one tap survival sprint through collapsing hazards",
        "arcade rooftop jumper with score streaks and tempo shifts",
        "timing dodge run with narrow escapes and bonus gates",
    ],
    "car": [
        "traffic weave road duel with escalating speed and near miss bonuses",
        "three lane chase where players dodge wrecks and collect bursts",
        "arcade driving escape with fast lane switches and pressure spikes",
        "endless neon road survival with quick reactions and recovery windows",
    ],
}

SUGGESTION_FAMILIES = {
    "assessment": [
        "self awareness assessment with guided questions and a practical profile at the end",
        "leadership evaluation with short scenarios, score breakdown and coaching advice",
        "teamwork checkup with multiple questions and a final interpretation report",
        "decision style assessment with branching questions and personalized feedback",
        "communication diagnostic with quick answers and a strengths versus gaps summary",
    ],
    "adventure": [
        "temple relic expedition with risky paths and fading energy",
        "jungle relic ascent with risky shortcuts and fading torchlight",
        "desert artifact run with dangerous paths and shrinking stamina",
        "lost ruins expedition with fading supplies and branching hazards",
        "storm relic hunt with unstable routes and fragile energy",
    ],
    "event-platform": [
        "multi stage event platform with central game area and support timeline",
        "event control platform with central arena and side support timeline",
        "showtime event platform with central stage and support progress rail",
        "live mission platform with central play area and side operations timeline",
        "audience event platform with central interaction zone and support timeline",
    ],
    "platform-hub": [
        "task world hub with unlockable doors and side progress timeline",
        "mission world hub with unlockable buildings and side reputation timeline",
        "quest district hub with gated houses and side progress rail",
        "adventure task hub with locked portals and side milestone tracker",
        "platform mission hub with unlockable rooms and side journey timeline",
    ],
    "vertical-platform-hub": [
        "vertical phaser task tower with reachable platforms, event tasks, stacked buildings and climbable pivot platforms",
        "vertical mission tower with reachable ledges, event tasks and unlockable upper buildings",
        "climbable task stack with upper houses, pivot platforms and side progress rail",
        "tower mission hub with stacked buildings, jumpable supports and live event tasks",
        "vertical quest world with reachable blocks, upper doors and climbable support platforms",
    ],
}

EXPERIENCE_CATEGORIES = {
    "learning": ["learning", "quiz", "memory", "pattern", "crossword"],
    "self-development": ["self-development", "diagnostic", "quiz", "adventure"],
    "diagnostic": ["diagnostic", "self-development", "quiz", "pattern"],
    "training": ["quiz", "crossword", "memory", "pattern"],
    "event": ["quiz", "reaction", "pick-one", "variety", "pattern", "platform-hub"],
    "showtime": ["reaction", "variety", "physics", "duel", "adventure", "car", "platform-hub"],
    "presentation": ["quiz", "reaction", "pick-one", "variety", "pattern", "physics", "platform-hub"],
}

ENGINE_KEYWORDS = {
    "learning": {"learn", "learning", "teach", "training", "skill", "lesson", "practice"},
    "self-development": {"self", "growth", "reflection", "confidence", "habit", "improve", "awareness"},
    "diagnostic": {"diagnostic", "assessment", "diagnose", "strength", "weakness", "improvement", "better"},
    "pick-one": {"door", "pick", "choice", "treasure", "card", "mystery"},
    "reaction": {"reaction", "tap", "timing", "signal", "fast"},
    "memory": {"memory", "symbol", "sequence", "recall", "hidden"},
    "pattern": {"pattern", "order", "sorting", "sequence", "tiles"},
    "physics": {"catapult", "cannon", "launch", "trajectory", "angle", "power", "projectile"},
    "quiz": {"quiz", "choice", "trivia", "question", "answer"},
    "crossword": {"crossword", "word", "letters", "spelling", "clue"},
    "adventure": {"adventure", "quest", "explore", "relic", "temple", "journey"},
    "platform-hub": {"platform", "hub", "portal", "door", "task", "world", "stage", "map", "vertical", "tower", "climb", "ledge", "blocks"},
    "variety": {"mix", "mixed", "variety", "gauntlet", "multi", "festival", "all"},
    "duel": {"boxing", "fight", "duel", "punch", "battle"},
    "runner": {"jump", "runner", "obstacle", "survival", "dodge"},
    "car": {"car", "race", "driving", "road", "traffic"},
}

NON_GAME_COMPONENTS = {
    "HelloWorld",
    "Client",
    "Paused",
    "GameStatsBar",
    "Timer",
    "Envelope",
    "Youtube",
    "Map",
    "MapTest",
    "CofeeMachine",
    "CarltonDancing",
    "DancingDog",
    "DancingDogs",
    "DancingPerson",
}

PREFERRED_ENGINE_BONUS = {
    "learning": 5,
    "self-development": 5,
    "diagnostic": 5,
    "pick-one": 2,
    "reaction": 2,
    "memory": 3,
    "pattern": 1,
    "physics": 3,
    "quiz": 4,
    "crossword": 4,
    "adventure": 3,
    "platform-hub": 4,
    "variety": 4,
    "duel": 1,
    "runner": -1,
    "car": 1,
}

RECENT_ENGINE_PENALTY = 3
FEEDBACK_ENGINE_WEIGHT = 2
REJECTED_ENGINE_PENALTY = 6


def infer_category_from_engine(engine_name: str) -> str:
    for category, engines in EXPERIENCE_CATEGORIES.items():
        if engine_name in engines:
            return category
    return "event"


def list_suggestion_families() -> list[str]:
    return list(SUGGESTION_FAMILIES.keys())


def get_prompt_suggestions(family: str | None = None) -> dict[str, list[str]]:
    if family:
        return {family: SUGGESTION_FAMILIES.get(family, [])}
    return SUGGESTION_FAMILIES


def _choose_auto_category(
    rng: random.Random,
    recent_counts: dict[str, int],
    feedback_scores: dict[str, int],
    rejected_engines: set[str],
) -> str:
    scored_categories: list[tuple[int, str]] = []
    for category, engines in EXPERIENCE_CATEGORIES.items():
        recent_score = sum(recent_counts.get(engine, 0) for engine in engines)
        feedback_score = sum(feedback_scores.get(engine, 0) for engine in engines)
        rejected_score = sum(1 for engine in engines if engine in rejected_engines)
        score = recent_score + rejected_score - feedback_score
        scored_categories.append((score, category))

    scored_categories.sort(key=lambda item: (item[0], item[1]))
    best_band = [category for score, category in scored_categories[:2]]
    return rng.choice(best_band)


def _existing_component_names(repo_path: str | None = None) -> set[str]:
    if not repo_path:
        return set()

    components_path = Path(repo_path) / "src" / "components"
    if not components_path.exists():
        return set()

    return {
        file_path.stem.lower()
        for file_path in components_path.glob("*.vue")
        if file_path.is_file() and file_path.stem not in NON_GAME_COMPONENTS
    }


def _infer_existing_engines(existing_names: set[str]) -> dict[str, int]:
    counts = {engine: 0 for engine in ENGINE_IDEAS}
    for name in existing_names:
        for engine, keywords in ENGINE_KEYWORDS.items():
            if any(keyword in name for keyword in keywords):
                counts[engine] += 1
    return counts


def _infer_engine_from_name(name: str) -> str | None:
    lowered = name.lower()
    best_engine = None
    best_score = 0
    for engine, keywords in ENGINE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_engine = engine
            best_score = score
    return best_engine


def _recent_engine_counts(repo_path: str | None, limit: int = 8) -> dict[str, int]:
    counts = {engine: 0 for engine in ENGINE_IDEAS}
    if not repo_path:
        return counts

    components_path = Path(repo_path) / "src" / "components"
    if not components_path.exists():
        return counts

    recent_files = sorted(
        (
            file_path
            for file_path in components_path.glob("*.vue")
            if file_path.is_file() and file_path.stem not in NON_GAME_COMPONENTS
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:limit]

    for file_path in recent_files:
        engine = _infer_engine_from_name(file_path.stem)
        if engine:
            counts[engine] += 1

    return counts


def _feedback_engine_scores() -> dict[str, int]:
    settings = get_settings()
    store = FeedbackStore(settings.feedback_store_path, settings.last_generation_path)
    feedback = store.get_feedback()
    scores = {engine: 0 for engine in ENGINE_IDEAS}
    for engine, stats in feedback.get("engines", {}).items():
        if engine in scores:
            scores[engine] = stats.get("approved", 0) - stats.get("rejected", 0)
    return scores


def _recent_feedback_history(limit: int = 8) -> list[dict]:
    settings = get_settings()
    store = FeedbackStore(settings.feedback_store_path, settings.last_generation_path)
    feedback = store.get_feedback()
    return feedback.get("history", [])[-limit:]


def _recent_rejected_engines() -> set[str]:
    rejected: set[str] = set()
    for entry in _recent_feedback_history():
        if entry.get("outcome") == "rejected" and entry.get("engine_name"):
            rejected.add(entry["engine_name"])
    return rejected


def _recently_generated_engines() -> set[str]:
    engines: set[str] = set()
    for entry in _recent_feedback_history(limit=4):
        if entry.get("engine_name"):
            engines.add(entry["engine_name"])
    return engines


def _used_ideas_from_feedback() -> set[str]:
    settings = get_settings()
    store = FeedbackStore(settings.feedback_store_path, settings.last_generation_path)
    feedback = store.get_feedback()
    ideas = {
        entry["idea"].strip().lower()
        for entry in feedback.get("history", [])
        if entry.get("idea")
    }
    last_generation = store.get_last_generation()
    if last_generation and last_generation.get("idea"):
        ideas.add(last_generation["idea"].strip().lower())
    return ideas


def _is_too_similar_to_used_ideas(idea: str, used_ideas: set[str]) -> bool:
    normalized = idea.strip().lower()
    idea_tokens = set(normalized.split())
    if normalized in used_ideas:
        return True

    for used in used_ideas:
        used_tokens = set(used.split())
        if not used_tokens:
            continue
        overlap = len(idea_tokens & used_tokens)
        similarity = overlap / max(1, min(len(idea_tokens), len(used_tokens)))
        if similarity >= 0.75:
            return True

    return False


def _candidate_ideas(
    rng: random.Random,
    existing_names: set[str],
    repo_path: str | None = None,
    category: str | None = None,
) -> list[str]:
    counts = _infer_existing_engines(existing_names)
    recent_counts = _recent_engine_counts(repo_path)
    feedback_scores = _feedback_engine_scores()
    rejected_engines = _recent_rejected_engines()
    recent_history_engines = _recently_generated_engines()
    allowed_engines = EXPERIENCE_CATEGORIES.get(category, list(ENGINE_IDEAS.keys()))
    ordered_engines = sorted(
        allowed_engines,
        key=lambda engine: (
            counts[engine]
            + (recent_counts[engine] * RECENT_ENGINE_PENALTY)
            - PREFERRED_ENGINE_BONUS[engine]
            - (feedback_scores[engine] * FEEDBACK_ENGINE_WEIGHT),
            (REJECTED_ENGINE_PENALTY if engine in rejected_engines else 0),
            (2 if engine in recent_history_engines else 0),
            counts[engine],
            engine,
        ),
    )
    median_count = counts[ordered_engines[len(ordered_engines) // 2]]
    priority_engines = [
        engine
        for engine in ordered_engines
        if counts[engine] <= median_count
        and recent_counts[engine] == 0
        and engine not in rejected_engines
        and engine not in recent_history_engines
    ]
    if not priority_engines:
        priority_engines = ordered_engines[:]
    rng.shuffle(priority_engines)
    trailing_engines = [engine for engine in ordered_engines if engine not in priority_engines]
    rng.shuffle(trailing_engines)
    ordered_engines = priority_engines + trailing_engines

    shuffled_by_engine: dict[str, list[str]] = {}
    max_len = 0
    for engine in ordered_engines:
        engine_ideas = ENGINE_IDEAS[engine][:]
        rng.shuffle(engine_ideas)
        shuffled_by_engine[engine] = engine_ideas
        max_len = max(max_len, len(engine_ideas))

    ideas: list[str] = []
    for index in range(max_len):
        for engine in ordered_engines:
            engine_ideas = shuffled_by_engine[engine]
            if index < len(engine_ideas):
                ideas.append(engine_ideas[index])

    return ideas


def generate_idea(seed: str | None = None, repo_path: str | None = None) -> str:
    rng = random.Random(seed)
    existing_names = _existing_component_names(repo_path)
    used_ideas = _used_ideas_from_feedback()
    recent_counts = _recent_engine_counts(repo_path)
    feedback_scores = _feedback_engine_scores()
    rejected_engines = _recent_rejected_engines()
    category = _choose_auto_category(rng, recent_counts, feedback_scores, rejected_engines)
    viable_ideas: list[str] = []

    for idea in _candidate_ideas(rng, existing_names, repo_path=repo_path, category=category):
        request = build_generation_request(idea)
        if request.game_name.lower() not in existing_names and not _is_too_similar_to_used_ideas(idea, used_ideas):
            viable_ideas.append(idea)
        if len(viable_ideas) >= 12:
            break

    if viable_ideas:
        return rng.choice(viable_ideas)

    fallback_engine = rng.choice(EXPERIENCE_CATEGORIES.get(category, list(ENGINE_IDEAS.keys())))
    fallback_idea = rng.choice(ENGINE_IDEAS[fallback_engine])
    suffix = rng.randint(2, 99)
    return f"{fallback_idea} variant {suffix}"


def generate_idea_for_category(
    category: str,
    seed: str | None = None,
    repo_path: str | None = None,
) -> str:
    normalized_category = category.strip().lower()
    if normalized_category not in EXPERIENCE_CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. Use one of: {', '.join(EXPERIENCE_CATEGORIES)}"
        )

    rng = random.Random(seed)
    existing_names = _existing_component_names(repo_path)
    used_ideas = _used_ideas_from_feedback()
    viable_ideas: list[str] = []

    for idea in _candidate_ideas(
        rng,
        existing_names,
        repo_path=repo_path,
        category=normalized_category,
    ):
        request = build_generation_request(idea)
        if request.game_name.lower() not in existing_names and not _is_too_similar_to_used_ideas(idea, used_ideas):
            viable_ideas.append(idea)
        if len(viable_ideas) >= 12:
            break

    if viable_ideas:
        return rng.choice(viable_ideas)

    fallback_engine = rng.choice(EXPERIENCE_CATEGORIES[normalized_category])
    fallback_idea = rng.choice(ENGINE_IDEAS[fallback_engine])
    suffix = rng.randint(2, 99)
    return f"{fallback_idea} variant {suffix}"
