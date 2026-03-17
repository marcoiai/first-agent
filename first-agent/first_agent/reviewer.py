from dataclasses import dataclass
import re

from first_agent.game_generator import GeneratedGame

GENERIC_IDEA_TOKENS = {
    "game",
    "component",
    "challenge",
    "quick",
    "rounds",
    "mobile",
    "on",
    "for",
    "with",
    "replayability",
    "participants",
    "participant",
    "instant",
    "limited",
}

GENERIC_IDEA_PHRASES = (
    "quick rounds",
    "on mobile",
    "for mobile",
    "instant feedback",
    "event participants",
    "live audience screen",
)


@dataclass
class ReviewCheck:
    name: str
    passed: bool
    details: str


@dataclass
class ReviewScorecard:
    clarity: int
    interactivity: int
    originality: int
    visual: int
    theme_fit: int
    utility: int

    @property
    def average(self) -> float:
        values = [
            self.clarity,
            self.interactivity,
            self.originality,
            self.visual,
            self.theme_fit,
            self.utility,
        ]
        return round(sum(values) / len(values), 1)


@dataclass
class ReviewResult:
    game: GeneratedGame
    checks: list[ReviewCheck]
    refinements: list[str]
    scorecard: ReviewScorecard
    recommendation: str

    @property
    def passed(self) -> bool:
      return all(check.passed for check in self.checks)


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _fix_common_vue_binding_issues(component_code: str) -> tuple[str, list[str]]:
    refinements: list[str] = []
    replacements = [
        (':style="{{{{ obstacleStyle }}}}"', ':style="obstacleStyle"'),
        (':class="{{{{ isJumping ? \'runner-player--jumping\' : \'\' }}}}"', ':class="isJumping ? \'runner-player--jumping\' : \'\'"'),
        (':style="{{ obstacleStyle }}"', ':style="obstacleStyle"'),
        (':class="{{ isJumping ? \'runner-player--jumping\' : \'\' }}"', ':class="isJumping ? \'runner-player--jumping\' : \'\'"'),
    ]
    updated = component_code
    for source, target in replacements:
        if source in updated:
            updated = updated.replace(source, target)
            refinements.append(f"Fixed invalid Vue binding: {source}")
    return updated, refinements


def _review_checks(game: GeneratedGame) -> list[ReviewCheck]:
    code = game.component_code
    engine_parts = set(game.engine_name.split("+"))
    checks = [
        ReviewCheck(
            name="instructions",
            passed=_has_any(code, ["Como jogar", "How to play"]),
            details="Game should explain the core loop clearly.",
        ),
        ReviewCheck(
            name="primary-action",
            passed=_has_any(code, ["@click=\"start", "@click=\"play", "@click=\"jump", "@click=\"pick", "@click=\"choose", "@click=\"answer", "@click=\"tap", "@click=\"select", "@click=\"fireShot", "@click=\"enterMap"]),
            details="Game should expose a visible primary action.",
        ),
        ReviewCheck(
            name="objective",
            passed=_has_any(code, ["Objetivo", "targetScore", "Vida rival", "Nivel", "Distancia", "roundNumber", "Fase atual"]),
            details="Game should show a visible objective or progress target.",
        ),
        ReviewCheck(
            name="loss-condition",
            passed=_has_any(code, ["losses >=", "playerHealth <=", "maxLives", "gameOver"]),
            details="Game should define a real losing condition.",
        ),
        ReviewCheck(
            name="valid-vue-bindings",
            passed=not _has_any(code, [':style="{{', ':class="{{']),
            details="Generated Vue bindings should not include nested moustaches.",
        ),
        ReviewCheck(
            name="shared-session-support",
            passed=not _has_any(code, ["../GameStatsBar", "../mixins/GameSessionMixin"]),
            details="Generated games should not reference fragile shared helper paths.",
        ),
        ReviewCheck(
            name="event-friendly-loop",
            passed=_has_any(code, ["saveGame(", "GameStatsBar", "session.score", "session.wins", "leader", "ranking", "participants"]),
            details="Games should be event-friendly, with a score/result loop that works well for many online participants.",
        ),
    ]

    if "memory" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="memory-sequence-visible",
                    passed=_has_any(code, ["Sequencia alvo", "highlightedSymbol", "playerProgressText"]),
                    details="Memory games should visibly show the sequence phase and player progress.",
                ),
                ReviewCheck(
                    name="memory-reveal-flow",
                    passed=_has_any(code, ["revealSequenceStep", "revealMode"]),
                    details="Memory games should include a reveal phase before input.",
                ),
            ]
        )
    if "runner" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="runner-jump-affordance",
                    passed=_has_any(code, ['@click="jump"', "runner-hint", "Pular"]),
                    details="Runner games should make the jump action visually obvious.",
                ),
                ReviewCheck(
                    name="runner-obstacle-loop",
                    passed=_has_any(code, ["obstaclePosition", "advanceGame", "runner-obstacle"]),
                    details="Runner games should have a clear obstacle loop.",
                ),
            ]
        )
    if "car" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="car-lane-controls",
                    passed=_has_any(code, ["moveLeft", "moveRight", "Esquerda", "Direita"]),
                    details="Car games should expose lane-changing controls.",
                ),
                ReviewCheck(
                    name="car-road-loop",
                    passed=_has_any(code, ["trafficLane", "trafficY", "road-stage", "player-car", "traffic-car"]),
                    details="Car games should show a road and moving traffic loop.",
                ),
            ]
        )
    if "quiz" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="quiz-question-visible",
                    passed=_has_any(code, ["Pergunta atual", "currentQuestion", "options"]),
                    details="Quiz games should show a readable question and answer options.",
                ),
                ReviewCheck(
                    name="quiz-answer-feedback",
                    passed=_has_any(code, ["Resposta correta", "answer(", "optionColor", "currentQuestion.answer"]),
                    details="Quiz games should give immediate right-or-wrong feedback.",
                ),
            ]
        )
    if "crossword" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="crossword-clue-visible",
                    passed=_has_any(code, ["Dica", "currentWord.clue", "letter-slot"]),
                    details="Crossword-style games should show a clue and visible answer slots.",
                ),
                ReviewCheck(
                    name="crossword-letter-loop",
                    passed=_has_any(code, ["pickLetter", "guess", "currentWord.answer"]),
                    details="Crossword-style games should have a letter-picking loop tied to the answer.",
                ),
            ]
        )
    if "physics" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="physics-aim-controls",
                    passed=_has_any(code, ["Angulo", "Potencia", "v-slider", "fireShot"]),
                    details="Physics games should expose aim controls such as angle and power.",
                ),
                ReviewCheck(
                    name="physics-target-zone",
                    passed=_has_any(code, ["targetZone", "targetCenter", "trajectory-preview", "impact-marker"]),
                    details="Physics games should show a visible landing target and impact feedback.",
                ),
            ]
        )
    if "streetview-adventure" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="streetview-panorama-visible",
                    passed=_has_any(code, ["street-stage__media", "panoramaStyle", "hotspotStyle", "Panorama explorável"]),
                    details="StreetView adventure games should show a panorama-style exploration area.",
                ),
                ReviewCheck(
                    name="streetview-hotspot-loop",
                    passed=_has_any(code, ["inspectHotspot", "street-hotspot", "currentRoundData.hotspots"]),
                    details="StreetView adventure games should let players inspect hotspots in the environment.",
                ),
            ]
        )
    if "platform-hub" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="platform-hub-world-visible",
                    passed=_has_any(code, ["phaser-stage", "new PhaserProxy.Game", "this.load.image('ground'", "hero: { x:"]),
                    details="Platform hub games should show a visible world or stage with doors, portals, or nodes.",
                ),
                ReviewCheck(
                    name="platform-hub-task-doors",
                    passed=_has_any(code, ["openFocusedDoor", "openTask", "taskTimeline", "taskId", "Abrir porta"]),
                    details="Platform hub games should connect world entry points to concrete tasks.",
                ),
                ReviewCheck(
                    name="platform-hub-data-driven",
                    passed=_has_any(code, ["buildLevels", "platforms:", "doors:", "pickups:", "currentLevel"]),
                    details="Platform hub games should be configured from level/task data, not only hardcoded button stacks.",
                ),
            ]
        )
    if "adventure" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="adventure-scene-visible",
                    passed=_has_any(code, ["currentScene", "Mapa", "explore", "scene-card", "relicsFound"]),
                    details="Adventure games should show a visible scene or journey state.",
                ),
                ReviewCheck(
                    name="adventure-scene-visuals",
                    passed=_has_any(code, ["scene-hero", "scene-hero__art", "backgroundImage", "action-card"]),
                    details="Adventure games should represent the scene visually, not only as text and buttons.",
                ),
                ReviewCheck(
                    name="adventure-decision-loop",
                    passed=_has_any(code, ["choosePath", "searchRelic", "restCamp", "energyLeft"]),
                    details="Adventure games should offer meaningful exploration decisions.",
                ),
            ]
        )
    if "variety" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="variety-phase-rotation",
                    passed=_has_any(code, ["currentMode", "phaseTitle", "nextPhase", "modeOrder"]),
                    details="Variety games should rotate between distinct mechanics.",
                ),
                ReviewCheck(
                    name="variety-mixed-actions",
                    passed=_has_any(code, ["answer(", "pickChoice(", "tapReaction", "selectMemorySymbol"]),
                    details="Variety games should expose more than one type of player action.",
                ),
            ]
        )
    if "duel" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="duel-response-options",
                    passed=_has_any(code, ["Esquivar", "Bloquear", "Contra-atacar"]),
                    details="Duel games should offer readable combat choices.",
                ),
                ReviewCheck(
                    name="duel-health",
                    passed=_has_any(code, ["playerHealth", "rivalHealth"]),
                    details="Duel games should show both sides' health.",
                ),
            ]
        )
    if "pick-one" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="pick-one-reveal",
                    passed=_has_any(code, ["pickCard", "cardClass", "choice-card"]),
                    details="Pick-one games should reveal a result immediately after one choice.",
                ),
            ]
        )
    if "reaction" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="reaction-stage",
                    passed=_has_any(code, ["reaction-stage", "handleStageClick", "readyAt"]),
                    details="Reaction games should revolve around a visible stage and timing event.",
                ),
            ]
        )
    if "learning" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="learning-interpretation",
                    passed=_has_any(code, ["nextStep", "interpretation", "Aprendizado", "prática"]),
                    details="Learning components should interpret the result and suggest a next action.",
                ),
            ]
        )
    if "self-development" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="self-development-guidance",
                    passed=_has_any(code, ["result", "strength", "nextStep", "autoconsciência", "melhoria"]),
                    details="Self-development components should identify strengths and improvement actions.",
                ),
            ]
        )
    if "diagnostic" in engine_parts:
        checks.extend(
            [
                ReviewCheck(
                    name="diagnostic-interpretation",
                    passed=_has_any(code, ["diagnosis", "improvement", "strength", "nextStep", "Interpretação"]),
                    details="Diagnostic components should explain the diagnosis and what to improve next.",
                ),
            ]
        )
    return checks


def _clamp_score(value: int) -> int:
    return max(1, min(10, value))


def _score_from_checks(game: GeneratedGame, checks: list[ReviewCheck]) -> tuple[ReviewScorecard, str]:
    code = game.component_code
    idea = game.request.idea.lower()
    engine_parts = set(game.engine_name.split("+"))
    passed = {check.name for check in checks if check.passed}
    failed = {check.name for check in checks if not check.passed}

    clarity = 3
    for name in ("instructions", "primary-action", "objective", "loss-condition"):
        if name in passed:
            clarity += 2
    if "quiz-question-visible" in passed or "crossword-clue-visible" in passed:
        clarity += 1
    clarity = _clamp_score(clarity)

    action_markers = [
        '@click="jump',
        '@click="pick',
        '@click="choose',
        '@click="answer',
        '@click="tap',
        '@click="select',
        '@click="fireShot',
        '@click="enterMap',
        '@click="moveLeft',
        '@click="moveRight',
        '@keydown',
    ]
    interactions_found = sum(1 for marker in action_markers if marker in code)
    interactivity = _clamp_score(3 + min(interactions_found, 4) + (2 if "primary-action" in passed else 0))

    originality = 4
    if "+" in game.engine_name or "variety" in engine_parts:
        originality += 2
    if "variety-mixed-actions" in passed or "variety-phase-rotation" in passed:
        originality += 2
    if "adventure" in engine_parts or "duel" in engine_parts or "physics" in engine_parts or "platform-hub" in engine_parts:
        originality += 1
    if "pick-one" in engine_parts and len(engine_parts) == 1:
        originality -= 1
    generic_token_hits = sum(1 for token in GENERIC_IDEA_TOKENS if token in idea.split())
    generic_phrase_hits = sum(1 for phrase in GENERIC_IDEA_PHRASES if phrase in idea)
    originality -= min(generic_token_hits, 2)
    originality -= min(generic_phrase_hits, 2)
    if any(token in idea for token in ("temple", "relic", "vault", "signal", "orbit", "mirror", "ladder", "arena", "storm", "chase")):
        originality += 1
    originality = _clamp_score(originality)

    visual = 3
    visual_markers = ["v-card", "v-row", "v-progress", "v-alert", "game-shell", "game-surface", "trajectory-preview", "impact-marker", "target-zone"]
    visual += min(sum(1 for marker in visual_markers if marker in code), 5)
    visual = _clamp_score(visual)

    engine_specific_checks = [
        check for check in checks
        if any(
            part in check.name
            for part in (
                "memory-",
                "runner-",
                "car-",
                "quiz-",
                "crossword-",
                "platform-hub-",
                "adventure-",
                "physics-",
                "streetview-",
                "variety-",
                "duel-",
                "pick-one",
                "reaction-",
                "learning-",
                "self-development",
                "diagnostic-",
            )
        )
    ]
    if engine_specific_checks:
        theme_ratio = sum(1 for check in engine_specific_checks if check.passed) / len(engine_specific_checks)
        theme_fit = _clamp_score(round(4 + (theme_ratio * 6)))
    else:
        theme_fit = _clamp_score(5 + (1 if "primary-action" in passed else 0))

    utility = 4
    if any(part in engine_parts for part in ("learning", "self-development", "diagnostic", "quiz", "crossword")):
        utility += 2
    if "learning-interpretation" in passed or "self-development-guidance" in passed or "diagnostic-interpretation" in passed:
        utility += 2
    if "objective" in passed:
        utility += 1
    if "event-friendly-loop" in passed:
        utility += 1
    if failed.intersection({"instructions", "objective"}):
        utility -= 1
    utility = _clamp_score(utility)

    scorecard = ReviewScorecard(
        clarity=clarity,
        interactivity=interactivity,
        originality=originality,
        visual=visual,
        theme_fit=theme_fit,
        utility=utility,
    )

    if scorecard.average >= 8:
        recommendation = "approved"
    elif scorecard.average >= 6.5:
        recommendation = "good-but-needs-polish"
    elif scorecard.average >= 5:
        recommendation = "weak"
    else:
        recommendation = "regenerate"

    if failed.intersection({"primary-action", "objective", "loss-condition"}):
        recommendation = "regenerate" if scorecard.average < 6.5 else "good-but-needs-polish"

    return scorecard, recommendation


def review_and_refine_game(game: GeneratedGame) -> ReviewResult:
    component_code, refinements = _fix_common_vue_binding_issues(game.component_code)
    refined_game = GeneratedGame(
        request=game.request,
        engine_name=game.engine_name,
        component_code=component_code,
        screen_code=game.screen_code,
        main_import=game.main_import,
        task_entry=game.task_entry,
        route_entry=game.route_entry,
        screen_render=game.screen_render,
        screen_component=game.screen_component,
        client_render=game.client_render,
        client_component=game.client_component,
    )
    checks = _review_checks(refined_game)
    scorecard, recommendation = _score_from_checks(refined_game, checks)
    return ReviewResult(
        game=refined_game,
        checks=checks,
        refinements=refinements,
        scorecard=scorecard,
        recommendation=recommendation,
    )
