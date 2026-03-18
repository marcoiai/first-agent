import re
from dataclasses import dataclass

from first_agent.reference_library import GameReference

GENERIC_IDEA_TOKENS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "for",
    "of",
    "to",
    "in",
    "on",
    "with",
    "that",
    "game",
    "component",
    "challenge",
    "quick",
    "round",
    "rounds",
    "mobile",
    "players",
    "player",
    "participants",
    "participant",
    "replayability",
    "instant",
    "limited",
}

GENERIC_IDEA_PHRASES = (
    "quick rounds",
    "on mobile",
    "for mobile",
    "event participants",
    "live audience screen",
    "instant feedback",
    "limited lives",
)


@dataclass
class GameGenerationRequest:
    idea: str
    game_name: str
    component_key: str
    variant_seed: int = 0


@dataclass
class GeneratedGame:
    request: GameGenerationRequest
    engine_name: str
    component_code: str
    screen_code: str
    main_import: str
    task_entry: str
    route_entry: str
    screen_render: str
    screen_component: str
    client_render: str
    client_component: str


def _idea_tokens(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return [part for part in "".join(ch if ch.isalnum() else " " for ch in normalized).split() if part]


def _meaningful_idea_tokens(value: str) -> list[str]:
    tokens = _idea_tokens(value)
    filtered = [token for token in tokens if token.lower() not in GENERIC_IDEA_TOKENS]
    if len(filtered) >= 2:
        return filtered[:8]
    return tokens[:8]


def to_pascal_case(value: str) -> str:
    parts = _meaningful_idea_tokens(value)
    return "".join(part.capitalize() for part in parts) or "GeneratedGame"


def to_component_key(value: str) -> str:
    parts = _meaningful_idea_tokens(value)
    return "".join(part.lower() for part in parts) or "generatedgame"


def to_kebab_case(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("-")
        chars.append(char.lower())
    return "".join(chars)


def _variant_index(request: GameGenerationRequest, engine_name: str, variant_count: int) -> int:
    seed = f"{request.idea.lower()}::{request.game_name.lower()}::{engine_name}::{request.variant_seed}"
    return sum(ord(char) for char in seed) % variant_count


def build_generation_request(idea: str, variant_seed: int = 0) -> GameGenerationRequest:
    game_name = to_pascal_case(idea)
    return GameGenerationRequest(
        idea=idea,
        game_name=game_name,
        component_key=to_component_key(idea),
        variant_seed=variant_seed,
    )


def build_system_prompt() -> str:
    return (
        "You generate new mini-games for a Vue 2 + Vuetify project named entert2. "
        "Output concise but complete code in the established project pattern. "
        "Every game must include a main component, a thin Screens wrapper, and "
        "integration snippets for main.js, Screen.vue, and Client.vue. "
        "Use the shared session contract with score, wins, losses, rounds, streak, and status. "
        "Avoid generic placeholder framing, and prefer a clear fantasy, situation, or hook that makes the game feel intentional. "
        "Push for showmanship when appropriate: strong visual identity, one dramatic interaction, and a satisfying reveal or payoff. "
        "Treat event-wide simultaneous play as a situational preference, not a hard rule: use it when the idea, references, or category suggest event, presentation, audience, or showtime contexts."
    )


def build_user_prompt(request: GameGenerationRequest, references: list[GameReference] | None = None) -> str:
    reference_lines = ""
    if references:
        reference_lines = "\nReferences from entert2:\n" + "\n".join(
            [
                f"- {reference.name} [{reference.template_hint}/{reference.layout_profile}]: {reference.excerpt}"
                for reference in references
            ]
        )
    streetview_hint = ""
    if references and any(reference.name == "StreetView" for reference in references):
        streetview_hint = (
            "\nA StreetView-style exploration reference is available. "
            "If it fits the idea, prefer embedded panorama, location discovery, visual clues, landmarks, and environmental reveals over static illustration cards."
        )
    platform_hint = ""
    if references and any(reference.name == "Platform" for reference in references):
        platform_hint = (
            "\nA Platform-style task hub reference is available. "
            "If it fits the idea, prefer a Phaser-driven side-scroller with stable level templates for hero, platforms, doors, houses, keys, coins, trees, and poles. "
            "Map real event tasks into pre-existing door slots instead of inventing a new geometry per task. "
            "Use a full-bleed playable stage, doors that open task modals over the map, and a secondary panel that can move below the stage when the map needs more room. "
            "Lean toward JSON-like level configuration and door-to-task navigation instead of a generic card or board layout."
        )
    vertical_platform_hint = ""
    if any(token in request.idea.lower() for token in ("vertical", "tower", "climb", "ledge", "stacked blocks", "upper blocks")):
        vertical_platform_hint = (
            "\nThis platform hub should lean vertical: reachable block stacks, ladders of platforms, and some buildings placed on higher ledges that are still achievable by jumping."
        )
    return (
        f"Game idea: {request.idea}\n"
        f"Game component name: {request.game_name}\n"
        f"Component key: {request.component_key}\n"
        "Target stack: Vue 2, Vuetify 2, Firebase-ready app.\n"
        "Reference pattern: standalone component + screen wrapper + integration snippets.\n"
        "Use a self-contained game loop, mobile-friendly layout, and shared session stats.\n"
        "Make the concept feel specific instead of generic: avoid filler title words like quick, mobile, challenge, component, replayability.\n"
        "Prefer a bold interaction model over a static questionnaire whenever the idea supports it. Include a visible payoff moment, not just text feedback.\n"
        "If the concept leans toward event, presentation, audience, or showtime use, prefer many people online at once, easy onboarding, low-friction input, and a result that can be compared across participants."
        f"{streetview_hint}"
        f"{platform_hint}"
        f"{vertical_platform_hint}"
        f"{reference_lines}"
    )


def _select_template(request: GameGenerationRequest, references: list[GameReference] | None = None) -> str:
    idea = request.idea.lower()
    if (
        "diagnostic" in idea
        or "assessment" in idea
        or "strength" in idea
        or "weakness" in idea
        or "what can i do better" in idea
        or "checkup" in idea
        or "radar" in idea
        or "blocker" in idea
    ):
        return "diagnostic"
    if (
        "self development" in idea
        or "self-development" in idea
        or "reflection" in idea
        or "habit" in idea
        or "confidence" in idea
        or "self awareness" in idea
        or "mirror" in idea
        or "blind spot" in idea
        or "growth advice" in idea
    ):
        return "self-development"
    if (
        "learning" in idea
        or "teach" in idea
        or "teaches" in idea
        or "skill builder" in idea
        or "lesson" in idea
        or "practice" in idea
        or "coaching" in idea
        or "listening" in idea
        or "triage" in idea
        or "decision lab" in idea
    ):
        return "learning"
    if (
        "platform" in idea
        or "portal" in idea
        or "doors" in idea
        or "hub" in idea
        or "task hub" in idea
        or "task world" in idea
        or "task map" in idea
    ):
        return "platform-hub"
    if (
        "streetview" in idea
        or "street view" in idea
        or "panorama" in idea
        or "landmark" in idea
        or "location clue" in idea
        or "guess the place" in idea
    ):
        return "streetview-adventure"
    if (
        "catapult" in idea
        or "cannon" in idea
        or "trajectory" in idea
        or "launch" in idea
        or "projectile" in idea
        or "angle" in idea
        or "power meter" in idea
        or "skill shot" in idea
    ):
        return "physics"
    if "mix" in idea or "mixed" in idea or "variety" in idea or "gauntlet" in idea or "all in one" in idea or "multi stage" in idea:
        return "variety"
    if (
        ("adventure" in idea or "quest" in idea or "explore" in idea or "journey" in idea or "relic" in idea or "temple" in idea)
        and ("quiz" in idea or "multiple choice" in idea or "trivia" in idea or "question" in idea or "answer" in idea)
    ):
        return "adventure+quiz"
    if (
        ("memory" in idea or "symbol" in idea or "hidden order" in idea or "sequence" in idea)
        and ("reaction" in idea or "tap" in idea or "timed" in idea or "fast" in idea)
    ):
        return "memory+reaction"
    if "adventure" in idea or "quest" in idea or "explore" in idea or "journey" in idea or "relic" in idea or "temple" in idea:
        return "adventure"
    if "punch" in idea or "box" in idea or "fight" in idea or "battle" in idea or "duel" in idea:
        return "duel"
    if "car" in idea or "race" in idea or "drive" in idea or "drift" in idea or "road" in idea:
        return "car"
    if "jump" in idea or "runner" in idea or "obstacle" in idea or "avoid" in idea or "survive" in idea:
        return "runner"
    if "reaction" in idea or "tap" in idea or "timed" in idea:
        return "reaction"
    if "memory" in idea or "symbol" in idea or "hidden order" in idea:
        return "memory"
    if "crossword" in idea or "word" in idea or "letters" in idea or "spelling" in idea or "clue" in idea:
        return "crossword"
    if (
        "quiz" in idea
        or "multiple choice" in idea
        or "trivia" in idea
        or "question" in idea
        or "answer" in idea
        or "four choice" in idea
        or "four options" in idea
        or "choice showdown" in idea
    ):
        return "quiz"
    if "pattern" in idea or "sequence" in idea or "sorting" in idea:
        return "pattern"

    if references:
        for reference in references:
            if reference.template_hint in {"pick-one", "reaction", "memory", "pattern", "physics", "quiz", "crossword", "adventure", "streetview-adventure", "platform-hub", "variety", "duel", "runner", "car"}:
                return reference.template_hint

    return "pick-one"


def _screen_code(request: GameGenerationRequest) -> str:
    tag_name = to_kebab_case(request.game_name)
    return f"""<template>
  <v-row>
    <v-col cols="12">
      <h1>{request.game_name}</h1>
      <{tag_name} />
    </v-col>
  </v-row>
</template>

<script>
export default {{
  name: '{request.game_name}Screen',
  components: {{
    {request.game_name}: () => import('../{request.game_name}')
  }}
}}
</script>
"""


def _select_layout_profile(
    request: GameGenerationRequest,
    engine_name: str,
    references: list[GameReference] | None = None,
) -> str:
    if references:
        for reference in references:
            if reference.template_hint == engine_name:
                return reference.layout_profile
        if references:
            return references[0].layout_profile

    if engine_name == "quiz":
        return "question-stack"
    if engine_name == "crossword":
        return "workbench"
    if engine_name == "reaction":
        return "hud-stage"
    if engine_name == "physics":
        return "control-panel"
    if engine_name == "streetview-adventure":
        return "split-board"
    if engine_name == "platform-hub":
        return "task-world"
    if engine_name == "adventure":
        return "split-board"
    return "game-surface"


def _build_component_code(request: GameGenerationRequest, references: list[GameReference] | None = None) -> str:
    template_name = _select_template(request, references=references)
    if template_name == "learning":
        return _build_learning_component(request)
    if template_name == "self-development":
        return _build_self_development_component(request)
    if template_name == "diagnostic":
        return _build_diagnostic_component(request)
    if template_name == "physics":
        return _build_physics_component(request)
    if template_name == "streetview-adventure":
        return _build_streetview_adventure_component(request)
    if template_name == "platform-hub":
        return _build_platform_hub_component(request)
    if template_name == "variety":
        return _build_variety_component(request)
    if template_name == "adventure+quiz":
        return _build_adventure_quiz_component(request)
    if template_name == "memory+reaction":
        return _build_memory_reaction_component(request)
    if template_name == "adventure":
        return _build_adventure_component(request)
    if template_name == "duel":
        return _build_duel_component(request)
    if template_name == "car":
        return _build_car_component(request)
    if template_name == "runner":
        return _build_runner_component(request)
    if template_name == "reaction":
        return _build_reaction_component(request)
    if template_name == "memory":
        return _build_memory_component(request)
    if template_name == "quiz":
        return _build_quiz_component(request, references=references)
    if template_name == "crossword":
        return _build_crossword_component(request, references=references)
    if template_name == "pattern":
        return _build_pattern_component(request)
    return _build_pick_one_component(request)


def _is_vertical_platform_hub_idea(request: GameGenerationRequest) -> bool:
    idea = request.idea.lower()
    return any(token in idea for token in ("vertical", "tower", "climb", "ledge", "stacked blocks", "upper blocks"))


def _build_learning_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Learning challenge</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Uma experiência curta para ensinar um conceito e reforçar uma habilidade prática.</p>
          </div>

          <v-row>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Objetivo</div>
                <p class="mb-2">Aprender um conceito na prática e sair com um próximo passo claro.</p>
                <ul class="mb-0">
                  <li>Responda as situações.</li>
                  <li>Ganhe pontos ao escolher a melhor prática.</li>
                  <li>Veja a interpretação final.</li>
                </ul>
              </v-card>

              <v-card outlined class="pa-4">
                <div class="text-caption">Progresso</div>
                <div class="text-h5 mb-2">{{{{ currentIndex + 1 }}}}/{{{{ scenarios.length }}}}</div>
                <v-progress-linear :value="progressValue" color="primary" height="10"></v-progress-linear>
                <div class="text-caption mt-3">Pontos</div>
                <div class="text-h5">{{{{ score }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="pa-5 mb-4">
                <div v-if="!finished">
                  <div class="text-overline mb-2">Situação prática</div>
                  <div class="text-h5 mb-4">{{{{ currentScenario.prompt }}}}</div>
                  <v-row dense>
                    <v-col v-for="option in currentScenario.options" :key="option.label" cols="12">
                      <v-btn block large color="primary" class="justify-start" :disabled="locked" @click="answer(option)">
                        {{{{ option.label }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <div v-else>
                  <div class="text-overline mb-2">Resultado</div>
                  <div class="text-h5 mb-2">{{{{ interpretation.title }}}}</div>
                  <p>{{{{ interpretation.summary }}}}</p>
                  <v-alert type="success" outlined>
                    Próximo passo: {{{{ interpretation.nextStep }}}}
                  </v-alert>
                </div>
              </v-card>

              <v-alert v-if="message" :type="alertType" dense text class="mb-4">
                {{{{ message }}}}
              </v-alert>

              <div class="text-right">
                <v-btn text @click="resetGame">Reiniciar</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {{
  name: '{request.game_name}',
  data: () => ({{
    currentIndex: 0,
    score: 0,
    locked: false,
    finished: false,
    message: '',
    alertType: 'info',
    interpretation: {{
      title: '',
      summary: '',
      nextStep: ''
    }},
    scenarios: [
      {{
        prompt: 'Durante uma conversa importante, qual atitude ajuda mais no aprendizado e na escuta?',
        options: [
          {{ label: 'Interromper para mostrar que sabe', correct: false, feedback: 'Interromper reduz a qualidade da escuta.' }},
          {{ label: 'Ouvir até o fim e então responder', correct: true, feedback: 'Boa prática. Isso melhora compreensão e respeito.' }},
          {{ label: 'Responder sem confirmar o entendimento', correct: false, feedback: 'Confirmar entendimento evita ruídos.' }}
        ]
      }},
      {{
        prompt: 'Ao aprender algo novo no trabalho, qual ação ajuda mais a consolidar o conteúdo?',
        options: [
          {{ label: 'Aplicar em uma pequena tarefa real', correct: true, feedback: 'Ótimo. Prática consolida aprendizado.' }},
          {{ label: 'Ler e não testar nada', correct: false, feedback: 'Sem prática, o conteúdo fixa menos.' }},
          {{ label: 'Esperar até alguém cobrar', correct: false, feedback: 'Esperar demais reduz o avanço.' }}
        ]
      }},
      {{
        prompt: 'Quando você erra, qual resposta tende a gerar mais desenvolvimento?',
        options: [
          {{ label: 'Esconder o erro', correct: false, feedback: 'Esconder atrasa o aprendizado.' }},
          {{ label: 'Revisar a causa e definir um ajuste', correct: true, feedback: 'Excelente. Aprender com o erro acelera evolução.' }},
          {{ label: 'Culpar apenas o contexto', correct: false, feedback: 'Contexto importa, mas ajuste pessoal também.' }}
        ]
      }}
    ]
  }}),
  computed: {{
    currentScenario () {{
      return this.scenarios[this.currentIndex]
    }},
    progressValue () {{
      return ((this.currentIndex + (this.finished ? 1 : 0)) / this.scenarios.length) * 100
    }}
  }},
  methods: {{
    answer (option) {{
      if (this.locked || this.finished) return
      this.locked = true
      this.message = option.feedback
      this.alertType = option.correct ? 'success' : 'warning'
      if (option.correct) {{
        this.score += 1
      }}
      window.setTimeout(() => {{
        if (this.currentIndex >= this.scenarios.length - 1) {{
          this.finishGame()
          return
        }}
        this.currentIndex += 1
        this.locked = false
        this.message = ''
      }}, 900)
    }},
    finishGame () {{
      this.finished = true
      if (this.score >= 3) {{
        this.interpretation = {{
          title: 'Aprendizado forte',
          summary: 'Você mostrou boa leitura das melhores práticas e tendência a transformar conteúdo em ação.',
          nextStep: 'Escolha uma habilidade desta rodada e aplique em uma situação real hoje.'
        }}
      }} else if (this.score == 2) {{
        this.interpretation = {{
          title: 'Boa base, com espaço para consolidar',
          summary: 'Você já reconhece parte das melhores decisões, mas ainda pode ganhar consistência.',
          nextStep: 'Revise os feedbacks e treine uma ação concreta nas próximas 24 horas.'
        }}
      }} else {{
        this.interpretation = {{
          title: 'Ponto de atenção para desenvolver',
          summary: 'Você pode evoluir bastante com prática guiada e revisão de hábitos de aprendizagem.',
          nextStep: 'Repita o desafio e escolha um único comportamento para melhorar primeiro.'
        }}
      }}
      this.message = ''
      this.locked = false
    }},
    resetGame () {{
      this.currentIndex = 0
      this.score = 0
      this.locked = false
      this.finished = false
      this.message = ''
      this.alertType = 'info'
      this.interpretation = {{ title: '', summary: '', nextStep: '' }}
    }}
  }}
}}
</script>
"""


def _build_self_development_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Self development</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Um componente de autopercepção com leitura de perfil e ações práticas de melhoria.</p>
          </div>

          <v-row>
            <v-col cols="12" md="5">
              <v-card outlined class="pa-4 mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Como funciona</div>
                <ul class="mb-0">
                  <li>Avalie seu comportamento em cada afirmação.</li>
                  <li>Some pontos de constância e autoconsciência.</li>
                  <li>Receba um retrato rápido e um próximo passo.</li>
                </ul>
              </v-card>

              <v-card outlined class="pa-4">
                <div class="text-caption">Afirmação</div>
                <div class="text-h5 mb-2">{{{{ currentIndex + 1 }}}}/{{{{ prompts.length }}}}</div>
                <v-progress-linear :value="progressValue" color="primary" height="10"></v-progress-linear>
                <div class="text-caption mt-3">Pontuação atual</div>
                <div class="text-h5">{{{{ score }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="7">
              <v-card outlined class="pa-5 mb-4">
                <div v-if="!finished && currentPrompt">
                  <div class="text-overline mb-2">Autoavaliação</div>
                  <div class="text-h5 mb-4">{{{{ currentPrompt.statement }}}}</div>
                  <v-row dense>
                    <v-col v-for="option in options" :key="option.label" cols="12" sm="6">
                      <v-btn block large color="primary" class="confidence-option" @click="selectOption(option)">
                        {{{{ option.label }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <v-alert v-else-if="!finished" type="warning" outlined>
                  Nenhuma afirmação disponível no momento. Reinicie o componente.
                </v-alert>

                <div v-else>
                  <div class="text-overline mb-2">Leitura do momento</div>
                  <div class="text-h5 mb-2">{{{{ result.title }}}}</div>
                  <p>{{{{ result.summary }}}}</p>
                  <v-alert type="info" outlined class="mb-3">
                    Você já faz bem: {{{{ result.strength }}}}
                  </v-alert>
                  <v-alert type="success" outlined>
                    O que pode fazer melhor: {{{{ result.nextStep }}}}
                  </v-alert>
                </div>
              </v-card>
              <div class="text-right">
                <v-btn text @click="resetGame">Recomeçar</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {{
  name: '{request.game_name}',
  data: () => ({{
    currentIndex: 0,
    score: 0,
    finished: false,
    options: [
      {{ label: 'Quase nunca', points: 0 }},
      {{ label: 'Às vezes', points: 1 }},
      {{ label: 'Com frequência', points: 2 }},
      {{ label: 'Quase sempre', points: 3 }}
    ],
    prompts: [
      {{ statement: 'Eu paro para refletir sobre como minhas atitudes impactam outras pessoas.' }},
      {{ statement: 'Quando algo dá errado, eu reviso meu comportamento antes de culpar apenas o contexto.' }},
      {{ statement: 'Eu transformo feedback em uma ação concreta de melhoria.' }},
      {{ statement: 'Eu consigo perceber rapidamente um hábito que preciso ajustar.' }}
    ],
    result: {{
      title: '',
      summary: '',
      strength: '',
      nextStep: ''
    }}
  }}),
  computed: {{
    currentPrompt () {{
      return this.prompts[this.currentIndex]
    }},
    progressValue () {{
      return ((this.currentIndex + (this.finished ? 1 : 0)) / this.prompts.length) * 100
    }}
  }},
  methods: {{
    selectOption (option) {{
      if (this.finished) return
      this.score += option.points
      if (this.currentIndex >= this.prompts.length - 1) {{
        this.finishGame()
        return
      }}
      this.currentIndex += 1
    }},
    finishGame () {{
      this.finished = true
      if (this.score >= 9) {{
        this.result = {{
          title: 'Boa base de autodesenvolvimento',
          summary: 'Você demonstra consciência do próprio comportamento e boa abertura para evolução.',
          strength: 'Transformar percepção em ajuste prático.',
          nextStep: 'Escolha um hábito específico para reforçar diariamente nesta semana.'
        }}
      }} else if (this.score >= 5) {{
        this.result = {{
          title: 'Potencial claro de crescimento',
          summary: 'Você já percebe sinais importantes, mas ainda pode ganhar consistência na aplicação.',
          strength: 'Capacidade de reconhecer oportunidades de melhoria.',
          nextStep: 'Registre um comportamento para observar em si mesmo pelos próximos 3 dias.'
        }}
      }} else {{
        this.result = {{
          title: 'Espaço importante para fortalecer a autoconsciência',
          summary: 'Este é um bom ponto de partida para desenvolver reflexão e ajuste intencional.',
          strength: 'Disposição para olhar para si com mais clareza.',
          nextStep: 'Peça um feedback simples a alguém de confiança e compare com sua autoavaliação.'
        }}
      }}
    }},
    resetGame () {{
      this.currentIndex = 0
      this.score = 0
      this.finished = false
      this.result = {{ title: '', summary: '', strength: '', nextStep: '' }}
    }}
  }}
}}
</script>

<style scoped>
.confidence-option {{
  min-height: 72px;
  white-space: normal;
}}
</style>
"""


def _build_diagnostic_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Diagnostic</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Um diagnóstico rápido para encontrar forças e o próximo ponto de melhoria.</p>
          </div>

          <v-row>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4">
                <div class="text-caption">Diagnóstico</div>
                <div class="text-h5 mb-2">{{{{ currentIndex + 1 }}}}/{{{{ questions.length }}}}</div>
                <v-progress-linear :value="progressValue" color="primary" height="10"></v-progress-linear>
                <div class="text-caption mt-3">Score de prontidão</div>
                <div class="text-h4">{{{{ score }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="pa-5">
                <div v-if="!finished">
                  <div class="text-overline mb-2">Pergunta diagnóstica</div>
                  <div class="text-h5 mb-4">{{{{ currentQuestion.prompt }}}}</div>
                  <v-row dense>
                    <v-col v-for="option in currentQuestion.options" :key="option.label" cols="12">
                      <v-btn block large color="primary" class="justify-start" @click="answer(option)">
                        {{{{ option.label }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <div v-else>
                  <div class="text-overline mb-2">Interpretação</div>
                  <div class="text-h5 mb-2">{{{{ diagnosis.title }}}}</div>
                  <p>{{{{ diagnosis.summary }}}}</p>
                  <v-alert type="info" outlined class="mb-3">
                    Ponto forte identificado: {{{{ diagnosis.strength }}}}
                  </v-alert>
                  <v-alert type="warning" outlined class="mb-3">
                    Oportunidade de melhoria: {{{{ diagnosis.improvement }}}}
                  </v-alert>
                  <v-alert type="success" outlined>
                    Próxima ação: {{{{ diagnosis.nextStep }}}}
                  </v-alert>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {{
  name: '{request.game_name}',
  data: () => ({{
    currentIndex: 0,
    score: 0,
    finished: false,
    diagnosis: {{
      title: '',
      summary: '',
      strength: '',
      improvement: '',
      nextStep: ''
    }},
    questions: [
      {{
        prompt: 'Quando precisa melhorar algo importante, qual é sua reação mais comum?',
        options: [
          {{ label: 'Escolho um ponto específico e ajo logo', points: 3 }},
          {{ label: 'Entendo o problema, mas demoro a agir', points: 2 }},
          {{ label: 'Percebo tarde e reajo sem plano', points: 1 }},
          {{ label: 'Evito olhar para isso', points: 0 }}
        ]
      }},
      {{
        prompt: 'Ao receber feedback, qual atitude te ajuda mais a evoluir?',
        options: [
          {{ label: 'Traduzo o feedback em um teste prático', points: 3 }},
          {{ label: 'Guardo mentalmente para depois', points: 2 }},
          {{ label: 'Fico defensivo antes de refletir', points: 1 }},
          {{ label: 'Ignoro e sigo igual', points: 0 }}
        ]
      }},
      {{
        prompt: 'Como você mede se realmente melhorou em algo?',
        options: [
          {{ label: 'Defino um sinal claro de progresso', points: 3 }},
          {{ label: 'Percebo de forma intuitiva', points: 2 }},
          {{ label: 'Raramente acompanho', points: 1 }},
          {{ label: 'Nunca verifico', points: 0 }}
        ]
      }}
    ]
  }}),
  computed: {{
    currentQuestion () {{
      return this.questions[this.currentIndex]
    }},
    progressValue () {{
      return ((this.currentIndex + (this.finished ? 1 : 0)) / this.questions.length) * 100
    }}
  }},
  methods: {{
    answer (option) {{
      if (this.finished) return
      this.score += option.points
      if (this.currentIndex >= this.questions.length - 1) {{
        this.finishDiagnosis()
        return
      }}
      this.currentIndex += 1
    }},
    finishDiagnosis () {{
      this.finished = true
      if (this.score >= 8) {{
        this.diagnosis = {{
          title: 'Prontidão alta para melhorar',
          summary: 'Você tende a transformar percepção em ação e a medir evolução com mais clareza.',
          strength: 'Execução consciente de melhorias.',
          improvement: 'Ganhar ainda mais consistência ao repetir boas práticas.',
          nextStep: 'Escolha uma habilidade e defina um indicador simples para acompanhar por 7 dias.'
        }}
      }} else if (this.score >= 4) {{
        this.diagnosis = {{
          title: 'Bom potencial, com gaps de consistência',
          summary: 'Você já tem base para evoluir, mas ainda perde força na continuidade ou no acompanhamento.',
          strength: 'Capacidade de reconhecer o que precisa mudar.',
          improvement: 'Converter intenção em rotina observável.',
          nextStep: 'Pegue um ponto de melhoria e transforme em uma prática diária pequena.'
        }}
      }} else {{
        this.diagnosis = {{
          title: 'Diagnóstico inicial de desenvolvimento',
          summary: 'Existe bastante espaço para avançar com mais clareza, estrutura e prática guiada.',
          strength: 'Ter agora um ponto de partida visível.',
          improvement: 'Sair do modo reativo e criar um método simples de evolução.',
          nextStep: 'Escolha uma área só para melhorar primeiro e peça um feedback externo objetivo.'
        }}
      }}
    }},
    resetGame () {{
      this.currentIndex = 0
      this.score = 0
      this.finished = false
      this.diagnosis = {{ title: '', summary: '', strength: '', improvement: '', nextStep: '' }}
    }}
  }}
}}
</script>
"""


def _build_variety_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Um gauntlet com fases diferentes: escolha, quiz, memoria e reflexo.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-row>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
                <ul class="mb-0">
                  <li>Cada rodada muda de mecanica.</li>
                  <li>Sobreviva a escolha, quiz, memoria e reflexo.</li>
                  <li>Acertos rendem pontos e avancam o gauntlet.</li>
                  <li>Erros custam vidas.</li>
                  <li>Feche 6 fases antes de perder 3 vidas.</li>
                </ul>
              </v-card>

              <game-stats-bar :session="session" />

              <v-card outlined class="pa-4 mt-4">
                <div class="text-caption">Fase atual</div>
                <div class="text-h5 mb-2">{{{{ phaseTitle }}}}</div>
                <div class="text-caption">Rodada</div>
                <div class="text-h5">{{{{ roundNumber }}}}/6</div>
                <div class="text-caption mt-3">Vidas</div>
                <div class="text-h5">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="pa-5 mb-4 stage-card">
                <div class="text-overline mb-2">Arena mista</div>

                <div v-if="currentMode === 'pick-one'">
                  <div class="text-h6 mb-4">Escolha um baú. So um traz o premio certo.</div>
                  <v-row dense>
                    <v-col v-for="choice in choices" :key="choice.id" cols="12" sm="4">
                      <v-btn block x-large color="primary" :disabled="locked" @click="pickChoice(choice.id)">
                        Bau {{{{ choice.id }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <div v-else-if="currentMode === 'quiz'">
                  <div class="text-h6 mb-4">{{{{ currentQuestion.prompt }}}}</div>
                  <v-row dense>
                    <v-col v-for="option in currentQuestion.options" :key="option" cols="12" sm="6">
                      <v-btn block large color="primary" :disabled="locked" @click="answer(option)">
                        {{{{ option }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <div v-else-if="currentMode === 'memory'">
                  <div class="text-h6 mb-4">Memorize o simbolo alvo e escolha o correto.</div>
                  <v-card outlined class="pa-4 text-center mb-4">
                    <div class="text-caption">Alvo</div>
                    <div class="display-1">{{{{ targetSymbol }}}}</div>
                  </v-card>
                  <v-row dense>
                    <v-col v-for="symbol in symbols" :key="symbol" cols="6" sm="3">
                      <v-btn block x-large color="primary" :disabled="locked" @click="selectMemorySymbol(symbol)">
                        {{{{ symbol }}}}
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <div v-else>
                  <div class="text-h6 mb-4">Espere o painel ativar e toque no momento certo.</div>
                  <div class="reaction-pad mb-4" :class="reactionReady ? 'reaction-pad--ready' : ''" @click="tapReaction">
                    <div class="text-h5">{{{{ reactionReady ? 'Agora' : 'Espere' }}}}</div>
                  </div>
                  <div class="text-body-2">Toques antecipados contam como erro.</div>
                </div>
              </v-card>

              <div class="text-right">
                <v-btn text large @click="resetGame">Reiniciar</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    modeOrder: ['pick-one', 'quiz', 'memory', 'reaction'],
    modeIndex: 0,
    roundNumber: 1,
    maxLives: 3,
    locked: false,
    message: 'Gauntlet iniciado. Encare a primeira fase.',
    alertType: 'info',
    choices: [
      {{ id: 1, good: false }},
      {{ id: 2, good: true }},
      {{ id: 3, good: false }}
    ],
    currentQuestion: {{
      prompt: 'Qual palavra combina mais com conhecimento rapido?',
      answer: 'quiz',
      options: ['quiz', 'neve', 'janela', 'garfo']
    }},
    symbols: ['▲', '●', '■', '★'],
    targetSymbol: '★',
    reactionReady: false,
    timerId: null
  }}),
  computed: {{
    currentMode () {{
      return this.modeOrder[this.modeIndex]
    }},
    phaseTitle () {{
      if (this.currentMode === 'pick-one') return 'Escolha'
      if (this.currentMode === 'quiz') return 'Quiz'
      if (this.currentMode === 'memory') return 'Memoria'
      return 'Reflexo'
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives || this.roundNumber > 6
    }}
  }},
  beforeDestroy () {{
    if (this.timerId) {{
      clearTimeout(this.timerId)
    }}
  }},
  mounted () {{
    this.preparePhase()
  }},
  methods: {{
    preparePhase () {{
      this.locked = false
      if (this.currentMode === 'pick-one') {{
        this.choices = this.shuffle([
          {{ id: 1, good: true }},
          {{ id: 2, good: false }},
          {{ id: 3, good: false }}
        ])
      }} else if (this.currentMode === 'quiz') {{
        this.currentQuestion = {{
          prompt: 'Qual dessas palavras lembra um desafio mental?',
          answer: 'memoria',
          options: ['memoria', 'tapete', 'chuva', 'escada']
        }}
      }} else if (this.currentMode === 'memory') {{
        this.targetSymbol = this.symbols[Math.floor(Math.random() * this.symbols.length)]
      }} else {{
        this.reactionReady = false
        this.timerId = setTimeout(() => {{
          this.reactionReady = true
        }}, 900)
      }}
    }},
    shuffle (items) {{
      const copy = [...items]
      for (let index = copy.length - 1; index > 0; index -= 1) {{
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = copy[index]
        copy[index] = copy[randomIndex]
        copy[randomIndex] = temp
      }}
      return copy
    }},
    pickChoice (choiceId) {{
      if (this.locked) return
      const selected = this.choices.find((entry) => entry.id === choiceId)
      if (selected && selected.good) {{
        this.completePhase(true, 'Boa escolha. Premio encontrado.')
      }} else {{
        this.completePhase(false, 'Escolha ruim. Esse bau nao ajudou.')
      }}
    }},
    answer (option) {{
      if (this.locked) return
      this.completePhase(option === this.currentQuestion.answer, option === this.currentQuestion.answer ? 'Resposta certa.' : 'Resposta errada.')
    }},
    selectMemorySymbol (symbol) {{
      if (this.locked) return
      this.completePhase(symbol === this.targetSymbol, symbol === this.targetSymbol ? 'Memoria correta.' : 'Simbolo errado.')
    }},
    tapReaction () {{
      if (this.locked) return
      this.completePhase(this.reactionReady, this.reactionReady ? 'Reflexo no tempo certo.' : 'Muito cedo no toque.')
    }},
    completePhase (success, message) {{
      this.locked = true
      this.startSessionRound(this.currentMode)
      if (success) {{
        this.registerWin(20, 'won')
        this.message = message
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = message
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        this.nextPhase()
      }}, 800)
    }},
    nextPhase () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
      this.modeIndex = (this.modeIndex + 1) % this.modeOrder.length
      this.roundNumber += 1
      if (this.gameOver) {{
        this.message = this.session.losses >= this.maxLives
          ? 'Fim do gauntlet. As vidas acabaram.'
          : 'Gauntlet completo. Boa mistura de habilidades.'
        this.alertType = this.session.losses >= this.maxLives ? 'error' : 'success'
        return
      }}
      this.preparePhase()
    }},
    resetGame () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
      this.resetSession()
      this.modeIndex = 0
      this.roundNumber = 1
      this.locked = false
      this.message = 'Gauntlet iniciado. Encare a primeira fase.'
      this.alertType = 'info'
      this.preparePhase()
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1500px;
}}

.game-surface {{
  border-radius: 28px;
}}

.stage-card {{
  min-height: 360px;
}}

.reaction-pad {{
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: #607d8b;
  color: #fff;
  cursor: pointer;
}}

.reaction-pad--ready {{
  background: #2e7d32;
}}
</style>
"""


def _build_pick_one_component(request: GameGenerationRequest) -> str:
    variant = _variant_index(request, "pick-one", 2)
    if variant == 1:
        return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Encontre o cofre seguro em uma das tentativas de cada rodada.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Escolha um entre quatro cofres por rodada.</li>
              <li>Apenas um cofre e seguro e rende pontos altos.</li>
              <li>Cofres vazios nao rendem nada.</li>
              <li>O cofre-bomba custa uma vida.</li>
              <li>Ganhe 3 rodadas antes de perder 3 vidas.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Rodadas vencidas</div>
                <div class="text-h4">{{{{ session.wins }}}}/3</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Melhor premio</div>
                <div class="text-h4">{{{{ bestReward }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mb-4">
            <v-btn color="primary" large :disabled="gameOver || roundLocked" @click="startRound">
              {{{{ roundStarted ? 'Nova rodada' : 'Comecar' }}}}
            </v-btn>
          </div>

          <v-row dense>
            <v-col v-for="vault in vaults" :key="vault.id" cols="6" sm="3">
              <v-card class="choice-card text-center pa-4" :class="cardClass(vault)" elevation="4" @click="pickVault(vault.id)">
                <div class="text-overline mb-2">Cofre {{{{ vault.id }}}}</div>
                <div class="text-h3 mb-3">{{{{ cardSymbol(vault) }}}}</div>
                <div class="text-body-2">{{{{ cardText(vault) }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mt-6">
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    roundStarted: false,
    maxLives: 3,
    bestReward: 0,
    roundLocked: false,
    message: 'Comece a rodada e abra um cofre.',
    alertType: 'info',
    vaults: []
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= 3 || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    startRound () {{
      if (this.gameOver || this.roundLocked) {{
        return
      }}
      const contents = this.shuffle([
        {{ kind: 'safe', value: 60 }},
        {{ kind: 'empty', value: 0 }},
        {{ kind: 'empty', value: 0 }},
        {{ kind: 'bomb', value: 0 }}
      ])
      this.vaults = contents.map((content, index) => ({{
        id: index + 1,
        opened: false,
        kind: content.kind,
        value: content.value
      }}))
      this.roundStarted = true
      this.roundLocked = false
      this.message = 'Escolha um cofre.'
      this.alertType = 'info'
    }},
    shuffle (items) {{
      const copy = [...items]
      for (let index = copy.length - 1; index > 0; index -= 1) {{
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = copy[index]
        copy[index] = copy[randomIndex]
        copy[randomIndex] = temp
      }}
      return copy
    }},
    pickVault (vaultId) {{
      if (!this.roundStarted || this.roundLocked || this.gameOver) {{
        return
      }}
      const vault = this.vaults.find((entry) => entry.id === vaultId)
      if (!vault || vault.opened) {{
        return
      }}
      this.startSessionRound('revealed')
      this.roundLocked = true
      vault.opened = true
      if (vault.kind === 'safe') {{
        this.bestReward = Math.max(this.bestReward, vault.value)
        this.registerWin(vault.value, 'won')
        this.message = `Boa. Cofre seguro encontrado e +${{vault.value}} pontos.`
        this.alertType = 'success'
      }} else if (vault.kind === 'bomb') {{
        this.registerLoss('lost')
        this.message = this.gameOver ? 'Fim de jogo. O cofre-bomba encerrou a partida.' : 'Bomba. Voce perdeu uma vida.'
        this.alertType = 'error'
      }} else {{
        this.message = 'Cofre vazio. Tente outra rodada.'
        this.alertType = 'warning'
      }}
      this.vaults.forEach((entry) => {{
        entry.opened = true
      }})
    }},
    cardClass (vault) {{
      if (!vault.opened) {{
        return ''
      }}
      if (vault.kind === 'safe') {{
        return 'choice-card--good'
      }}
      if (vault.kind === 'bomb') {{
        return 'choice-card--bad'
      }}
      return 'choice-card--neutral'
    }},
    cardSymbol (vault) {{
      if (!vault.opened) {{
        return '🔒'
      }}
      if (vault.kind === 'safe') {{
        return '💎'
      }}
      if (vault.kind === 'bomb') {{
        return '💥'
      }}
      return '📭'
    }},
    cardText (vault) {{
      if (!vault.opened) {{
        return 'Toque para abrir'
      }}
      if (vault.kind === 'safe') {{
        return `Premio de ${{vault.value}}`
      }}
      if (vault.kind === 'bomb') {{
        return 'Perde uma vida'
      }}
      return 'Nada aqui'
    }},
    resetGame () {{
      this.resetSession()
      this.roundStarted = false
      this.bestReward = 0
      this.roundLocked = false
      this.vaults = []
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.choice-card {{
  cursor: pointer;
  min-height: 180px;
  transition: transform 0.2s ease, border-color 0.2s ease;
}}
.choice-card:hover {{
  transform: translateY(-4px);
}}
.choice-card--good {{
  border: 2px solid #2e7d32;
}}
.choice-card--bad {{
  border: 2px solid #c62828;
}}
.choice-card--neutral {{
  border: 2px solid #ef6c00;
}}
</style>
"""
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Escolha uma opcao por rodada e descubra se ela vale pontos ou prejuizo.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Escolha uma carta por rodada.</li>
              <li>Uma carta rende premio alto, uma rende premio baixo e uma e armadilha.</li>
              <li>Acertos aumentam a pontuacao e a sequencia.</li>
              <li>A armadilha consome uma vida.</li>
              <li>Chegue a 150 pontos antes de perder 3 vidas.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Objetivo</div>
                <div class="text-h4">{{{{ targetScore }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Melhor premio</div>
                <div class="text-h4">{{{{ bestReward }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mb-4">
            <v-btn
              color="primary"
              large
              class="mb-2"
              :disabled="gameOver || roundLocked"
              @click="startRound"
            >
              {{{{ roundLocked ? 'Revelando...' : 'Nova rodada' }}}}
            </v-btn>
          </div>

          <v-row class="mb-4" dense>
            <v-col
              v-for="card in cards"
              :key="card.id"
              cols="12"
              sm="4"
            >
              <v-card
                class="choice-card text-center pa-4"
                :class="cardClass(card)"
                elevation="4"
                @click="pickCard(card.id)"
              >
                <div class="text-overline mb-2">Escolha {{{{ card.id }}}}</div>
                <div class="text-h3 mb-3">{{{{ cardSymbol(card) }}}}</div>
                <div class="text-body-2">{{{{ cardText(card) }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center">
            <v-btn text large @click="resetGame">
              Reiniciar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    targetScore: 150,
    maxLives: 3,
    bestReward: 0,
    roundLocked: false,
    message: 'Comece uma rodada e escolha uma carta.',
    alertType: 'info',
    cards: [],
    timerId: null
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.score >= this.targetScore || this.session.losses >= this.maxLives
    }}
  }},
  beforeDestroy () {{
    if (this.timerId) {{
      clearTimeout(this.timerId)
    }}
  }},
  methods: {{
    startRound () {{
      if (this.gameOver || this.roundLocked) {{
        return
      }}
      const contents = this.shuffle([
        {{ kind: 'big', value: 80 }},
        {{ kind: 'small', value: 35 }},
        {{ kind: 'trap', value: 0 }}
      ])
      this.cards = contents.map((content, index) => ({{
        id: index + 1,
        opened: false,
        kind: content.kind,
        value: content.value
      }}))
      this.roundLocked = false
      this.message = 'Escolha uma carta.'
      this.alertType = 'info'
    }},
    shuffle (items) {{
      const copy = [...items]
      for (let index = copy.length - 1; index > 0; index -= 1) {{
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = copy[index]
        copy[index] = copy[randomIndex]
        copy[randomIndex] = temp
      }}
      return copy
    }},
    pickCard (cardId) {{
      if (this.roundLocked || this.gameOver || this.cards.length === 0) {{
        return
      }}
      const card = this.cards.find((entry) => entry.id === cardId)
      if (!card || card.opened) {{
        return
      }}
      this.roundLocked = true
      this.startSessionRound('revealed')
      this.cards = this.cards.map((entry) => ({{
        ...entry,
        opened: true
      }}))

      if (card.kind === 'trap') {{
        this.registerLoss('lost')
        this.alertType = 'warning'
        this.message = this.gameOver
          ? 'Fim de jogo. A armadilha tirou sua ultima vida.'
          : 'Armadilha. Voce perdeu uma vida.'
      }} else {{
        this.registerWin(card.value, 'won')
        this.bestReward = Math.max(this.bestReward, card.value)
        this.alertType = card.kind === 'big' ? 'success' : 'info'
        this.message = this.session.score >= this.targetScore
          ? `Vitoria. Voce chegou a ${{this.session.score}} pontos.`
          : `Boa. Esta escolha rendeu ${{card.value}} pontos.`
      }}

      if (!this.gameOver) {{
        this.timerId = window.setTimeout(() => {{
          this.cards = []
          this.roundLocked = false
          this.message = 'Nova rodada. Escolha outra carta.'
          this.alertType = 'info'
        }}, 1400)
      }}
    }},
    cardClass (card) {{
      if (!card.opened) {{
        return 'choice-card--closed'
      }}
      if (card.kind === 'big') {{
        return 'choice-card--big'
      }}
      if (card.kind === 'small') {{
        return 'choice-card--small'
      }}
      return 'choice-card--trap'
    }},
    cardSymbol (card) {{
      if (!card.opened) {{
        return '🎴'
      }}
      if (card.kind === 'big') {{
        return '💎'
      }}
      if (card.kind === 'small') {{
        return '⭐'
      }}
      return '💥'
    }},
    cardText (card) {{
      if (!card.opened) {{
        return 'Toque para revelar'
      }}
      if (card.kind === 'big') {{
        return 'Premio alto'
      }}
      if (card.kind === 'small') {{
        return 'Premio seguro'
      }}
      return 'Armadilha'
    }},
    resetGame () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
      this.resetSession()
      this.bestReward = 0
      this.roundLocked = false
      this.cards = []
      this.message = 'Jogo reiniciado. Comece uma rodada.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.choice-card {{
  min-height: 210px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}}

.choice-card:hover {{
  transform: translateY(-3px);
}}

.choice-card--closed {{
  background: linear-gradient(135deg, #1f3b63, #2e5b92);
  color: #fff;
}}

.choice-card--big {{
  background: linear-gradient(135deg, #0f8a5f, #1fbd84);
  color: #fff;
}}

.choice-card--small {{
  background: linear-gradient(135deg, #4e6d8f, #6f91b8);
  color: #fff;
}}

.choice-card--trap {{
  background: linear-gradient(135deg, #8a2d2d, #bf4c4c);
  color: #fff;
}}
</style>
"""


def _build_memory_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Memorize a sequencia de simbolos e repita na ordem correta.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Clique em comecar para revelar uma sequencia curta de simbolos.</li>
              <li>Memorize a ordem enquanto ela estiver visivel.</li>
              <li>Depois toque nos simbolos na mesma ordem.</li>
              <li>Cada rodada correta aumenta a dificuldade e a pontuacao.</li>
              <li>Erre 3 vezes e a partida termina.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Nivel</div>
                <div class="text-h4">{{{{ level }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Sequencia</div>
                <div class="text-h4">{{{{ sequence.length }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mb-4">
            <v-chip class="mb-2" color="indigo" dark>
              {{{{ revealMode ? 'Memorize a sequencia' : 'Repita a sequencia' }}}}
            </v-chip>
          </div>

          <v-card outlined class="pa-4 mb-4 text-center sequence-panel">
            <div class="text-caption mb-2">Sequencia alvo</div>
            <div v-if="revealMode" class="text-h2 font-weight-bold mb-2 sequence-current">
              {{{{ highlightedSymbol || '...' }}}}
            </div>
            <div v-else class="text-h5 font-weight-bold mb-2">
              {{{{ playerProgressText }}}}
            </div>
            <div class="d-flex justify-center flex-wrap">
              <v-chip
                v-for="(item, index) in sequence"
                :key="`${{item}}-${{index}}`"
                class="ma-1"
                :color="chipColor(item, index)"
                :outlined="!isChipFilled(index)"
                dark
              >
                {{{{ chipLabel(item, index) }}}}
              </v-chip>
            </div>
          </v-card>

          <v-row dense class="mb-4">
            <v-col
              v-for="symbol in symbols"
              :key="symbol"
              cols="6"
            >
              <v-btn
                block
                x-large
                class="memory-button"
                :color="buttonColor(symbol)"
                :disabled="gameOver || revealMode || !roundActive"
                @click="chooseSymbol(symbol)"
              >
                {{{{ symbol }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center">
            <v-btn
              color="primary"
              large
              class="mr-2"
              :disabled="roundActive && revealMode"
              @click="startRound"
            >
              {{{{ roundActive ? 'Nova sequencia' : 'Comecar jogo' }}}}
            </v-btn>
            <v-btn text large @click="resetGame">
              Reiniciar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    symbols: ['▲', '●', '■', '★'],
    sequence: [],
    playerInput: [],
    level: 1,
    maxLives: 3,
    revealMode: false,
    roundActive: false,
    highlightedSymbol: null,
    timerId: null,
    message: 'Comece quando estiver pronto para memorizar.',
    alertType: 'info'
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives
    }},
    playerProgressText () {{
      if (this.sequence.length === 0) {{
        return 'Nenhuma sequencia carregada'
      }}
      return `${{this.playerInput.length}} / ${{this.sequence.length}} simbolos`
    }}
  }},
  beforeDestroy () {{
    this.clearTimer()
  }},
  methods: {{
    clearTimer () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
    }},
    buildSequence () {{
      return Array.from({{ length: Math.min(this.level + 2, 7) }}, () => (
        this.symbols[Math.floor(Math.random() * this.symbols.length)]
      ))
    }},
    startRound () {{
      if (this.gameOver) {{
        return
      }}
      this.clearTimer()
      this.sequence = this.buildSequence()
      this.playerInput = []
      this.highlightedSymbol = null
      this.revealMode = true
      this.roundActive = true
      this.startSessionRound('memorizing')
      this.message = 'Memorize a ordem e prepare-se para repetir.'
      this.alertType = 'warning'
      this.revealSequenceStep(0)
    }},
    revealSequenceStep (index) {{
      if (index >= this.sequence.length) {{
        this.highlightedSymbol = null
        this.timerId = setTimeout(() => {{
          this.revealMode = false
          this.setSessionStatus('playing')
          this.message = 'Agora repita a sequencia.'
          this.alertType = 'info'
          this.timerId = null
        }}, 500)
        return
      }}

      this.highlightedSymbol = this.sequence[index]
      this.timerId = setTimeout(() => {{
        this.highlightedSymbol = null
        this.timerId = setTimeout(() => {{
          this.revealSequenceStep(index + 1)
        }}, 250)
      }}, 600)
    }},
    chooseSymbol (symbol) {{
      if (this.revealMode || !this.roundActive || this.gameOver) {{
        return
      }}
      this.playerInput.push(symbol)
      const currentIndex = this.playerInput.length - 1
      if (symbol !== this.sequence[currentIndex]) {{
        this.registerLoss('lost')
        this.roundActive = false
        this.message = this.gameOver
          ? 'Fim de jogo. Suas vidas acabaram.'
          : 'Sequencia errada. Estude melhor e tente outra vez.'
        this.alertType = 'error'
        return
      }}

      if (this.playerInput.length === this.sequence.length) {{
        const points = this.sequence.length * 10
        this.registerWin(points, 'won')
        this.level += 1
        this.roundActive = false
        this.message = `Boa memoria. Voce ganhou ${{points}} pontos e subiu para o nivel ${{this.level}}.`
        this.alertType = 'success'
      }}
    }},
    buttonColor (symbol) {{
      if (this.highlightedSymbol === symbol) {{
        return 'success'
      }}
      return 'primary'
    }},
    isChipFilled (index) {{
      return this.revealMode || index < this.playerInput.length
    }},
    chipLabel (symbol, index) {{
      if (this.revealMode || index < this.playerInput.length) {{
        return symbol
      }}
      return '?'
    }},
    chipColor (symbol, index) {{
      if (this.highlightedSymbol === symbol && this.revealMode) {{
        return 'success'
      }}
      if (index < this.playerInput.length) {{
        return 'primary'
      }}
      return 'grey darken-1'
    }},
    resetGame () {{
      this.clearTimer()
      this.resetSession()
      this.sequence = []
      this.playerInput = []
      this.level = 1
      this.revealMode = false
      this.roundActive = false
      this.highlightedSymbol = null
      this.message = 'Jogo reiniciado. Comece uma nova sequencia.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.memory-button {{
  min-height: 92px;
  font-size: 2rem;
}}

.sequence-panel {{
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
}}

.sequence-current {{
  min-height: 72px;
}}
</style>
"""


def _build_reaction_component(request: GameGenerationRequest) -> str:
    variant = _variant_index(request, "reaction", 2)
    if variant == 1:
        return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10" xl="9">
        <v-card class="pa-6 pa-md-8 text-center game-surface" elevation="6">
          <div class="text-overline mb-2">Generated game</div>
          <h1 class="text-h4 mb-2">{request.game_name}</h1>
          <p class="mb-6">
            Espere o sinal correto e toque apenas no alvo verde para construir uma sequencia limpa.
          </p>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Comece a rodada e observe os paines piscando.</li>
              <li>So toque quando o painel central ficar verde.</li>
              <li>Toques em vermelho contam como erro.</li>
              <li>Faça 4 acertos para vencer a partida.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4" justify="center">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Acertos</div>
                <div class="text-h5">{{{{ session.wins }}}}/4</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Erros</div>
                <div class="text-h5">{{{{ session.losses }}}}/3</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Streak</div>
                <div class="text-h5">{{{{ session.streak }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="signal-board mb-6">
            <div class="signal-lamp" :class="leftLamp"></div>
            <div class="signal-lamp signal-lamp--center" :class="centerLamp" @click="tapSignal"></div>
            <div class="signal-lamp" :class="rightLamp"></div>
          </div>

          <v-btn color="primary" large :disabled="gameOver || roundActive" @click="startRound">
            {{{{ roundActive ? 'Rodada ativa' : 'Comecar jogo' }}}}
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    roundActive: false,
    canTap: false,
    timerId: null,
    leftLamp: 'signal-lamp--idle',
    centerLamp: 'signal-lamp--idle',
    rightLamp: 'signal-lamp--idle',
    message: 'Comece a rodada e espere o sinal certo.',
    alertType: 'info'
  }}),
  computed: {{
    gameOver () {{
      return this.session.wins >= 4 || this.session.losses >= 3
    }}
  }},
  beforeDestroy () {{
    this.clearTimer()
  }},
  methods: {{
    clearTimer () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
    }},
    startRound () {{
      if (this.gameOver || this.roundActive) {{
        return
      }}
      this.roundActive = true
      this.canTap = false
      this.startSessionRound('waiting')
      this.leftLamp = 'signal-lamp--warn'
      this.centerLamp = 'signal-lamp--warn'
      this.rightLamp = 'signal-lamp--warn'
      this.message = 'Observe os sinais.'
      this.alertType = 'warning'
      this.timerId = setTimeout(() => {{
        this.leftLamp = 'signal-lamp--idle'
        this.rightLamp = 'signal-lamp--idle'
        this.centerLamp = 'signal-lamp--go'
        this.canTap = true
        this.message = 'Toque agora.'
        this.alertType = 'success'
      }}, 1000 + Math.floor(Math.random() * 1200))
    }},
    tapSignal () {{
      if (!this.roundActive || this.gameOver) {{
        return
      }}
      if (this.canTap) {{
        this.registerWin(20 + (this.session.streak * 5), 'won')
        this.message = 'Boa. Sinal correto.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = 'Muito cedo. Esse sinal ainda nao valia.'
        this.alertType = 'error'
      }}
      this.finishRound()
    }},
    finishRound () {{
      this.clearTimer()
      this.roundActive = false
      this.canTap = false
      this.leftLamp = 'signal-lamp--idle'
      this.centerLamp = 'signal-lamp--idle'
      this.rightLamp = 'signal-lamp--idle'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1400px;
}}

.game-surface {{
  border-radius: 28px;
}}

.signal-board {{
  display: grid;
  grid-template-columns: repeat(3, minmax(72px, 1fr));
  gap: 16px;
  align-items: center;
}}
.signal-lamp {{
  min-height: 140px;
  border-radius: 24px;
  background: #546e7a;
  transition: transform 0.2s ease, background-color 0.2s ease;
}}
.signal-lamp--center {{
  cursor: pointer;
}}
.signal-lamp--idle {{
  background: #607d8b;
}}
.signal-lamp--warn {{
  background: #fb8c00;
}}
.signal-lamp--go {{
  background: #2e7d32;
  transform: scale(1.03);
}}
</style>
"""
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10" xl="9">
        <v-card class="pa-6 pa-md-8 text-center game-surface" elevation="6">
          <div class="text-overline mb-2">Generated game</div>
          <h1 class="text-h4 mb-2">{request.game_name}</h1>
          <p class="mb-6">
            Espere o painel mudar e toque no momento certo para marcar pontos.
          </p>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Clique em comecar para iniciar a espera.</li>
              <li>Quando o painel ficar verde, toque o mais rapido que puder.</li>
              <li>Se clicar cedo demais, perde a rodada.</li>
              <li>Acertos rapidos rendem mais pontos.</li>
              <li>Erre 3 vezes e a partida termina.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <div
            class="reaction-stage d-flex align-center justify-center mb-6"
            :class="stageClass"
            @click="handleStageClick"
          >
            <div>
              <div class="text-h5 font-weight-bold mb-2">{{{{ stageTitle }}}}</div>
              <div class="text-body-1">{{{{ stageSubtitle }}}}</div>
            </div>
          </div>

          <v-row class="mb-4" justify="center">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Melhor tempo</div>
                <div class="text-h5">{{{{ bestTimeText }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Ultima rodada</div>
                <div class="text-h5">{{{{ lastTimeText }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Vidas</div>
                <div class="text-h5">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-btn color="primary" large :disabled="gameOver" @click="startRound">
            {{{{ hasStarted ? 'Jogar novamente' : 'Comecar jogo' }}}}
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    state: 'idle',
    timerId: null,
    readyAt: null,
    lastTime: null,
    bestTime: null,
    maxLives: 3,
    message: 'Clique em comecar para iniciar.',
    alertType: 'info',
    hasStarted: false
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives
    }},
    stageClass () {{
      return `reaction-stage--${{this.state}}`
    }},
    stageTitle () {{
      if (this.state === 'waiting') return 'Espere'
      if (this.state === 'ready') return 'Agora'
      if (this.state === 'result') return 'Boa'
      return 'Pronto'
    }},
    stageSubtitle () {{
      if (this.state === 'waiting') return 'Toque apenas quando ficar verde.'
      if (this.state === 'ready') return 'Clique agora.'
      if (this.state === 'result') return this.lastTimeText
      return 'Teste seu tempo de reacao.'
    }},
    lastTimeText () {{
      return this.lastTime === null ? '--' : `${{this.lastTime}} ms`
    }},
    bestTimeText () {{
      return this.bestTime === null ? '--' : `${{this.bestTime}} ms`
    }}
  }},
  beforeDestroy () {{
    this.clearTimer()
  }},
  methods: {{
    clearTimer () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
    }},
    startRound () {{
      if (this.gameOver) {{
        return
      }}
      this.clearTimer()
      this.hasStarted = true
      this.state = 'waiting'
      this.readyAt = null
      this.startSessionRound('waiting')
      this.message = 'Espere a cor mudar.'
      this.alertType = 'warning'

      const delay = 1200 + Math.floor(Math.random() * 2200)
      this.timerId = setTimeout(() => {{
        this.state = 'ready'
        this.setSessionStatus('ready')
        this.readyAt = Date.now()
        this.message = 'Clique agora.'
        this.alertType = 'success'
        this.timerId = null
      }}, delay)
    }},
    handleStageClick () {{
      if (this.state === 'idle') {{
        this.startRound()
        return
      }}
      if (this.state === 'waiting') {{
        this.clearTimer()
        this.state = 'idle'
        this.registerLoss('early')
        this.message = this.gameOver
          ? 'Fim de jogo. Voce queimou sua ultima rodada.'
          : 'Muito cedo. Espere a cor mudar.'
        this.alertType = 'error'
        return
      }}
      if (this.state !== 'ready' || this.readyAt === null) {{
        return
      }}
      const reactionTime = Date.now() - this.readyAt
      const points = Math.max(10, 900 - reactionTime)
      this.lastTime = reactionTime
      this.bestTime = this.bestTime === null ? reactionTime : Math.min(this.bestTime, reactionTime)
      this.registerWin(points, 'won')
      this.state = 'result'
      this.message = `Seu tempo foi ${{reactionTime}} ms e voce ganhou ${{points}} pontos.`
      this.alertType = 'success'
    }},
    resetGame () {{
      this.clearTimer()
      this.resetSession()
      this.state = 'idle'
      this.readyAt = null
      this.lastTime = null
      this.bestTime = null
      this.hasStarted = false
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1400px;
}}

.game-surface {{
  border-radius: 28px;
}}

.reaction-stage {{
  min-height: 240px;
  border-radius: 24px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease;
}}

.reaction-stage--idle {{
  background: linear-gradient(135deg, #1e3a5f, #315d8a);
}}

.reaction-stage--waiting {{
  background: linear-gradient(135deg, #8a5a00, #c78500);
}}

.reaction-stage--ready {{
  background: linear-gradient(135deg, #0b7a4b, #16a765);
}}

.reaction-stage--result {{
  background: linear-gradient(135deg, #5c2d91, #7d4ac7);
}}
</style>
"""


def _build_adventure_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Adventure run</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Explore ruinas, leia a cena, escolha sua postura e tente sair com reliquias antes da energia acabar.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-row class="mt-2">
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 mb-4 text-left sidebar-card">
                <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
                <ul class="mb-0">
                  <li>Leia a cena e escolha uma postura para esta etapa.</li>
                  <li>Explorar revela caminho, buscar reliquia aumenta risco e descansar compra folego.</li>
                  <li>Encontre 4 reliquias para vencer.</li>
                  <li>Se a energia chegar a zero, a expedicao termina.</li>
                </ul>
              </v-card>

              <game-stats-bar :session="session" />

              <v-card outlined class="pa-4 mt-4 mb-4">
                <div class="d-flex justify-space-between mb-2">
                  <div>
                    <div class="text-caption">Mapa</div>
                    <div class="text-h5">{{{{ step }}}}/{{{{ maxSteps }}}}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-caption">Reliquias</div>
                    <div class="text-h5">{{{{ relicsFound }}}}/4</div>
                  </div>
                </div>
                <div class="text-caption mb-2">Energia</div>
                <v-progress-linear
                  :value="(energyLeft / maxEnergy) * 100"
                  color="success"
                  height="12"
                  rounded
                />
                <div class="text-body-2 mt-2">Energia restante: {{{{ energyLeft }}}}</div>
              </v-card>

              <v-card outlined class="pa-4 mb-4 text-left">
                <div class="text-caption mb-2">Ultimo evento</div>
                <div class="text-body-1">{{{{ lastEvent }}}}</div>
              </v-card>

              <v-card outlined class="pa-4 text-left">
                <div class="text-caption mb-2">Status</div>
                <div class="text-body-1">{{{{ gameOver ? finalStatus : 'A aventura continua' }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="mb-4 scene-card">
                <div class="scene-hero">
                  <div class="scene-hero__art" :style="sceneArtStyle"></div>
                  <div class="scene-hero__veil"></div>
                  <div class="scene-hero__content">
                    <div class="text-overline mb-2">Cena atual</div>
                    <div class="text-h5 mb-3">{{{{ currentScene.title }}}}</div>
                    <p class="mb-0 text-body-1">{{{{ currentScene.description }}}}</p>
                  </div>
                </div>
              </v-card>

              <v-card outlined class="pa-4 mb-4 discovery-card">
                <div class="text-overline mb-2">Resposta da cena</div>
                <div class="discovery-card__stage">
                  <div class="discovery-card__visual">{{{{ currentDiscovery.emoji }}}}</div>
                  <div>
                    <div class="text-h6 mb-1">{{{{ currentDiscovery.title }}}}</div>
                    <div class="text-body-2">{{{{ currentDiscovery.description }}}}</div>
                  </div>
                </div>
              </v-card>

              <v-row dense class="mb-4">
                <v-col cols="12" sm="4">
                  <v-card class="action-card action-card--explore" :class="gameOver ? 'action-card--disabled' : ''" elevation="4" @click="choosePath('left')">
                    <div class="action-card__emoji">🧭</div>
                    <div class="action-card__title">Explorar trilha</div>
                    <div class="action-card__copy">Empurra a jornada para frente e pode revelar atalhos ou salas novas.</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card class="action-card action-card--relic" :class="gameOver ? 'action-card--disabled' : ''" elevation="4" @click="searchRelic">
                    <div class="action-card__emoji">💎</div>
                    <div class="action-card__title">Buscar reliquia</div>
                    <div class="action-card__copy">Força uma busca intensa na cena atual com risco maior e payoff alto.</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card class="action-card action-card--rest" :class="gameOver ? 'action-card--disabled' : ''" elevation="4" @click="restCamp">
                    <div class="action-card__emoji">⛺</div>
                    <div class="action-card__title">Descansar</div>
                    <div class="action-card__copy">Recupera energia, mas faz o relógio da expedição continuar avançando.</div>
                  </v-card>
                </v-col>
              </v-row>

              <v-card outlined class="pa-5 exploration-board">
                <div class="text-overline mb-3">Mapa da expedicao</div>
                <div class="node-track">
                  <div
                    v-for="node in maxSteps"
                    :key="node"
                    class="node-track__item"
                    :class="node <= step ? 'node-track__item--active' : ''"
                  >
                    {{{{ node }}}}
                  </div>
                </div>
                <div class="relic-strip mt-4">
                  <div
                    v-for="slot in 4"
                    :key="`slot-${{slot}}`"
                    class="relic-strip__item"
                    :class="slot <= relicsFound ? 'relic-strip__item--active' : ''"
                  >
                    💠
                  </div>
                </div>
                <div class="text-body-2 mt-4">
                  Cada escolha move voce um passo no mapa. Leia a cena, aja e acompanhe a expedicao visualmente.
                </div>
              </v-card>

              <div class="text-right mt-6">
                <v-btn text large @click="resetGame">
                  Reiniciar
                </v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxEnergy: 10,
    energyLeft: 10,
    relicsFound: 0,
    step: 1,
    maxSteps: 9,
    lastEvent: 'A expedicao comecou.',
    lastAction: 'arrival',
    message: 'Escolha sua primeira acao de exploracao.',
    alertType: 'info',
    sceneIndex: 0,
    scenes: [
      {{
        title: 'Entrada do templo',
        description: 'Voce encontra tochas apagadas, pegadas e uma passagem estreita.',
        image: 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1400&q=80'
      }},
      {{
        title: 'Sala das estatuas',
        description: 'As estatuas apontam para caminhos diferentes e uma delas esconde um brilho.',
        image: 'https://images.unsplash.com/photo-1539650116574-75c0c6d73f4e?auto=format&fit=crop&w=1400&q=80'
      }},
      {{
        title: 'Ponte quebrada',
        description: 'A travessia balanca e voce precisa decidir se forca a passagem ou procura ao redor.',
        image: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1400&q=80'
      }},
      {{
        title: 'Camara central',
        description: 'A parte mais profunda das ruinas parece esconder a melhor reliquia da jornada.',
        image: 'https://images.unsplash.com/photo-1549893074-4bc0f5a9b8d8?auto=format&fit=crop&w=1400&q=80'
      }},
      {{
        title: 'Arquivo subterraneo',
        description: 'Paredes gravadas e nichos vazios sugerem que alguem removeu artefatos importantes ha pouco tempo.',
        image: 'https://images.unsplash.com/photo-1518998053901-5348d3961a04?auto=format&fit=crop&w=1400&q=80'
      }},
      {{
        title: 'Santuario final',
        description: 'O ultimo salao concentra simbolos raros, ecos e a promessa de uma reliquia digna de encerramento.',
        image: 'https://images.unsplash.com/photo-1577717903315-1691ae25ab3f?auto=format&fit=crop&w=1400&q=80'
      }}
    ]
  }}),
  computed: {{
    currentScene () {{
      return this.scenes[this.sceneIndex] || this.scenes[0]
    }},
    sceneArtStyle () {{
      return {{
        backgroundImage: `url(${{this.currentScene.image}})`
      }}
    }},
    currentDiscovery () {{
      if (this.lastAction === 'explore') {{
        return {{
          emoji: '🏛️',
          title: 'Estrutura revelada',
          description: 'Depois de explorar a trilha, uma construção antiga aparece no horizonte e abre novas possibilidades de rota.'
        }}
      }}
      if (this.lastAction === 'search') {{
        return {{
          emoji: '🗝️',
          title: 'Pista examinada',
          description: 'A busca deixa marcas no ambiente, revela compartimentos e sugere que algo valioso está escondido por perto.'
        }}
      }}
      if (this.lastAction === 'rest') {{
        return {{
          emoji: '🔥',
          title: 'Acampamento montado',
          description: 'Uma pequena base improvisada dá segurança temporária, mas o mundo ao redor continua em movimento.'
        }}
      }}
      return {{
        emoji: '🗺️',
        title: 'Mapa aberto',
        description: 'A expedição está começando e o cenário ainda guarda suas melhores revelações.'
      }}
    }},
    gameOver () {{
      return this.energyLeft <= 0 || this.relicsFound >= 4 || this.step > this.maxSteps
    }},
    finalStatus () {{
      if (this.relicsFound >= 4) {{
        return 'Vitoria. A equipe saiu com reliquias suficientes.'
      }}
      if (this.energyLeft <= 0) {{
        return 'Fim da jornada. A energia acabou.'
      }}
      return 'A expedicao terminou sem o suficiente para vencer.'
    }}
  }},
  methods: {{
    choosePath (direction) {{
      if (this.gameOver) {{
        return
      }}
      this.startSessionRound('exploring')
      const foundRelic = (this.step + this.relicsFound) % 3 === 0
      this.lastAction = 'explore'
      this.energyLeft = Math.max(this.energyLeft - 2, 0)
      this.step += 1
      this.sceneIndex = (this.sceneIndex + 1) % this.scenes.length
      if (foundRelic) {{
        this.relicsFound += 1
        this.registerWin(25, 'won')
        this.lastEvent = direction === 'left' ? 'A trilha revelou uma reliquia escondida.' : 'O caminho alternativo levou a um artefato raro.'
        this.message = 'Boa exploracao. Voce encontrou uma reliquia.'
        this.alertType = 'success'
      }} else {{
        this.session.rounds += 1
        this.lastEvent = 'O caminho trouxe poeira e risco, mas nada valioso.'
        this.message = 'Voce avancou no mapa, mas ainda sem premio.'
        this.alertType = 'info'
      }}
    }},
    searchRelic () {{
      if (this.gameOver) {{
        return
      }}
      this.startSessionRound('searching')
      const success = this.step % 2 === 1
      this.lastAction = 'search'
      this.energyLeft = Math.max(this.energyLeft - 3, 0)
      this.step += 1
      if (success) {{
        this.relicsFound += 1
        this.registerWin(35, 'won')
        this.lastEvent = 'A busca cuidadosa revelou uma reliquia enterrada.'
        this.message = 'Busca bem-sucedida. Reliquia encontrada.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.lastEvent = 'A busca acionou armadilhas e drenou energia.'
        this.message = 'A busca falhou e custou recursos.'
        this.alertType = 'error'
      }}
      this.sceneIndex = (this.sceneIndex + 1) % this.scenes.length
    }},
    restCamp () {{
      if (this.gameOver) {{
        return
      }}
      this.startSessionRound('resting')
      this.lastAction = 'rest'
      this.energyLeft = Math.min(this.energyLeft + 2, this.maxEnergy)
      this.step += 1
      this.session.rounds += 1
      this.lastEvent = 'A equipe descansou e recuperou folego para seguir.'
      this.message = 'Energia recuperada, mas o tempo da aventura avanca.'
      this.alertType = 'warning'
      this.sceneIndex = (this.sceneIndex + 1) % this.scenes.length
    }},
    resetGame () {{
      this.resetSession()
      this.energyLeft = this.maxEnergy
      this.relicsFound = 0
      this.step = 1
      this.lastAction = 'arrival'
      this.lastEvent = 'A expedicao comecou.'
      this.message = 'Escolha sua primeira acao de exploracao.'
      this.alertType = 'info'
      this.sceneIndex = 0
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1500px;
}}

.game-surface {{
  border-radius: 28px;
}}

.sidebar-card {{
  position: sticky;
  top: 16px;
}}

.scene-card {{
  overflow: hidden;
  min-height: 240px;
  background: #0f172a;
}}

.scene-hero {{
  position: relative;
  min-height: 240px;
}}

.scene-hero__art {{
  position: absolute;
  inset: 0;
  background-position: center;
  background-size: cover;
  transform: scale(1.04);
}}

.scene-hero__veil {{
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.16), rgba(15, 23, 42, 0.82));
}}

.scene-hero__content {{
  position: relative;
  z-index: 1;
  padding: 24px;
  color: #fff;
}}

.action-card {{
  min-height: 172px;
  padding: 20px;
  border-radius: 22px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}}

.action-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.22);
}}

.action-card--disabled {{
  opacity: 0.55;
  pointer-events: none;
}}

.action-card--explore {{
  background: linear-gradient(135deg, #1d4ed8, #0f766e);
}}

.action-card--relic {{
  background: linear-gradient(135deg, #b45309, #ea580c);
}}

.action-card--rest {{
  background: linear-gradient(135deg, #0f766e, #155e75);
}}

.action-card__emoji {{
  font-size: 2rem;
  line-height: 1;
}}

.action-card__title {{
  margin-top: 16px;
  font-size: 1.08rem;
  font-weight: 800;
}}

.action-card__copy {{
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.45;
}}

.discovery-card {{
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.98), rgba(239, 246, 255, 0.98));
}}

.discovery-card__stage {{
  display: flex;
  align-items: center;
  gap: 16px;
}}

.discovery-card__visual {{
  width: 72px;
  height: 72px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.18), rgba(37, 99, 235, 0.14));
  font-size: 2rem;
  flex: 0 0 auto;
}}

.exploration-board {{
  min-height: 190px;
}}

.node-track {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  gap: 10px;
}}

.node-track__item {{
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
  font-weight: 700;
  transition: transform 0.2s ease, background 0.2s ease;
}}

.node-track__item--active {{
  background: #2e7d32;
  color: #fff;
  transform: scale(1.04);
}}

.relic-strip {{
  display: flex;
  gap: 12px;
}}

.relic-strip__item {{
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.08);
  font-size: 1.2rem;
  opacity: 0.45;
  transition: transform 0.2s ease, opacity 0.2s ease;
}}

.relic-strip__item--active {{
  opacity: 1;
  transform: translateY(-2px);
  background: linear-gradient(135deg, rgba(250, 204, 21, 0.28), rgba(59, 130, 246, 0.18));
}}
</style>
"""


def _build_adventure_quiz_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Avance pela aventura respondendo perguntas para abrir os proximos caminhos.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Cada etapa da aventura traz uma pergunta para destravar o caminho.</li>
              <li>Acertos rendem progresso e reliquias.</li>
              <li>Erros custam energia.</li>
              <li>Encontre 3 reliquias antes de ficar sem energia.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Etapa</div>
                <div class="text-h4">{{{{ step }}}}/{{{{ questions.length }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Reliquias</div>
                <div class="text-h4">{{{{ relicsFound }}}}/3</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Energia</div>
                <div class="text-h4">{{{{ energyLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card outlined class="pa-4 mb-4 scene-card">
            <div class="text-overline mb-2">Cena</div>
            <div class="text-h6 mb-1">{{{{ currentQuestion.scene }}}}</div>
            <p class="mb-0">{{{{ currentQuestion.prompt }}}}</p>
          </v-card>

          <v-row dense>
            <v-col v-for="option in currentQuestion.options" :key="option" cols="12" sm="6">
              <v-btn
                block
                large
                class="mb-2 quiz-option"
                :disabled="gameOver || roundLocked"
                :color="optionColor(option)"
                @click="answer(option)"
              >
                {{{{ option }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center mt-4">
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxEnergy: 6,
    energyLeft: 6,
    relicsFound: 0,
    step: 1,
    roundLocked: false,
    selectedOption: null,
    message: 'A primeira pergunta da aventura esta pronta.',
    alertType: 'info',
    questions: [
      {{ scene: 'Portao do templo', prompt: 'Qual item ajuda a iluminar um corredor antigo?', answer: 'tocha', options: ['tocha', 'almofada', 'garfo', 'quadro'] }},
      {{ scene: 'Sala das pistas', prompt: 'Que tipo de desafio combina com descobrir respostas?', answer: 'quiz', options: ['quiz', 'janela', 'tapete', 'trilho'] }},
      {{ scene: 'Camara da reliquia', prompt: 'O que voce espera encontrar no fim da jornada?', answer: 'tesouro', options: ['tesouro', 'chuva', 'cadeira', 'planta'] }},
      {{ scene: 'Saida secreta', prompt: 'Qual palavra lembra lembrar simbolos na ordem?', answer: 'memoria', options: ['memoria', 'panela', 'martelo', 'garagem'] }}
    ]
  }}),
  computed: {{
    currentQuestion () {{
      return this.questions[this.step - 1] || this.questions[this.questions.length - 1]
    }},
    gameOver () {{
      return this.relicsFound >= 3 || this.energyLeft <= 0 || this.step > this.questions.length
    }}
  }},
  methods: {{
    optionColor (option) {{
      if (!this.roundLocked || this.selectedOption !== option) {{
        return 'primary'
      }}
      return option === this.currentQuestion.answer ? 'success' : 'error'
    }},
    answer (option) {{
      if (this.roundLocked || this.gameOver) {{
        return
      }}
      this.roundLocked = true
      this.selectedOption = option
      this.startSessionRound('adventure-quiz')
      if (option === this.currentQuestion.answer) {{
        this.relicsFound += 1
        this.registerWin(30, 'won')
        this.message = 'Caminho liberado. Voce ganhou uma reliquia.'
        this.alertType = 'success'
      }} else {{
        this.energyLeft = Math.max(this.energyLeft - 2, 0)
        this.registerLoss('lost')
        this.message = `Resposta errada. A energia caiu e a certa era "${{this.currentQuestion.answer}}".`
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        this.step += 1
        this.roundLocked = false
        this.selectedOption = null
        if (!this.gameOver) {{
          this.message = 'Nova cena desbloqueada.'
          this.alertType = 'info'
        }}
      }}, 900)
    }},
    resetGame () {{
      this.resetSession()
      this.energyLeft = this.maxEnergy
      this.relicsFound = 0
      this.step = 1
      this.roundLocked = false
      this.selectedOption = null
      this.message = 'A primeira pergunta da aventura esta pronta.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1480px;
}}

.game-surface {{
  border-radius: 28px;
}}

.scene-card {{
  min-height: 120px;
}}
.quiz-option {{
  min-height: 72px;
  white-space: normal;
}}
</style>
"""


def _build_streetview_adventure_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">StreetView adventure</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Navegue pela cena, leia a pista e encontre a relíquia escondida no ambiente.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-row>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
                <ul class="mb-0">
                  <li>Observe a pista da rodada.</li>
                  <li>Navegue pela cena panorâmica e identifique o melhor ponto.</li>
                  <li>Escolha o hotspot que combina com a pista.</li>
                  <li>Encontre 3 relíquias antes de errar 3 vezes.</li>
                </ul>
              </v-card>

              <game-stats-bar :session="session" />

              <v-card outlined class="pa-4 mt-4 mb-4">
                <div class="d-flex justify-space-between mb-2">
                  <div>
                    <div class="text-caption">Rodada</div>
                    <div class="text-h5">{{{{ currentRound + 1 }}}}/{{{{ rounds.length }}}}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-caption">Relíquias</div>
                    <div class="text-h5">{{{{ relicsFound }}}}/3</div>
                  </div>
                </div>
                <div class="text-caption mb-2">Pista ativa</div>
                <div class="text-body-1 font-weight-medium">{{{{ currentRoundData.clue }}}}</div>
                <div class="text-caption mt-4 mb-2">Objetivo</div>
                <div class="text-body-2">Entre no Street View, observe o ambiente e toque no hotspot que melhor responde à pista.</div>
              </v-card>

              <v-card outlined class="pa-4 mb-4">
                <div class="text-caption mb-2">Ambiente</div>
                <div class="text-body-1">{{{{ currentRoundData.location }}}}</div>
                <div class="text-body-2 mt-2">{{{{ currentRoundData.story }}}}</div>
              </v-card>

              <v-card outlined class="pa-4">
                <div class="text-caption mb-2">Última descoberta</div>
                <div class="text-body-1">{{{{ lastDiscovery }}}}</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="street-stage mb-4">
                <div class="street-stage__media">
                  <div :id="panoramaElementId" class="street-stage__panorama"></div>
                  <div class="street-stage__veil"></div>
                  <div class="street-stage__hud">
                    <div class="street-stage__label">Street View explorável</div>
                    <div class="street-stage__title">{{{{ currentRoundData.location }}}}</div>
                  </div>

                  <div v-if="!mapEntered" class="street-stage__entry">
                    <div class="street-stage__entry-card">
                      <div class="text-overline mb-2">Ação principal</div>
                      <div class="text-h6 mb-3">Entre no mapa para começar a exploração</div>
                      <p class="mb-4">Abra o Street View desta rodada e então escolha o hotspot que melhor responde à pista.</p>
                      <v-btn color="amber darken-2" dark large @click="enterMap">
                        Entrar no mapa
                      </v-btn>
                    </div>
                  </div>

                  <button
                    v-for="hotspot in currentRoundData.hotspots"
                    :key="hotspot.id"
                    type="button"
                    class="street-hotspot"
                    :style="hotspotStyle(hotspot)"
                    :disabled="roundLocked || gameOver || !mapEntered"
                    @click="inspectHotspot(hotspot)"
                  >
                    <span class="street-hotspot__dot"></span>
                    <span class="street-hotspot__label">{{{{ hotspot.label }}}}</span>
                  </button>
                </div>
              </v-card>

              <v-row dense class="mb-4">
                <v-col cols="12" sm="4">
                  <v-card outlined class="pa-4 support-card">
                    <div class="text-overline mb-2">Direção</div>
                    <div class="text-h6 mb-2">{{{{ currentRoundData.heading }}}}</div>
                    <div class="text-body-2">Use os hotspots como pontos de observação na cena.</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card outlined class="pa-4 support-card">
                    <div class="text-overline mb-2">Alvo</div>
                    <div class="text-h6 mb-2">{{{{ currentRoundData.targetLabel }}}}</div>
                    <div class="text-body-2">A pista sempre descreve um sinal visual do ambiente.</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card outlined class="pa-4 support-card">
                    <div class="text-overline mb-2">Status</div>
                    <div class="text-h6 mb-2">{{{{ gameOver ? finalStatus : 'Exploração ativa' }}}}</div>
                    <div class="text-body-2">Acerte para avançar e acumular relíquias.</div>
                  </v-card>
                </v-col>
              </v-row>

              <div class="text-right">
                <v-btn text large @click="resetGame">Reiniciar</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

/*global google */

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    currentRound: 0,
    relicsFound: 0,
    lastDiscovery: 'A exploração está prestes a começar.',
    message: 'Observe a pista e toque no ponto certo do panorama.',
    alertType: 'info',
    roundLocked: false,
    mapEntered: false,
    googleCredentials: '',
    panoramaInstance: null,
    rounds: [
      {{
        location: 'Pátio histórico',
        heading: 'Olhe para o edifício principal',
        clue: 'A relíquia está perto da fachada mais imponente da cena.',
        story: 'Uma construção dominante parece esconder o primeiro sinal útil.',
        targetLabel: 'Fachada principal',
        lat: 37.86926,
        lng: -122.254811,
        headingValue: 151.78,
        pitch: -0.76,
        correctId: 'building',
        hotspots: [
          {{ id: 'lamp', label: 'Poste antigo', top: '42%', left: '18%' }},
          {{ id: 'building', label: 'Prédio histórico', top: '36%', left: '58%' }},
          {{ id: 'stairs', label: 'Escadaria', top: '70%', left: '72%' }}
        ]
      }},
      {{
        location: 'Praça com monumentos',
        heading: 'Procure a estrutura vertical mais marcante',
        clue: 'A pista aponta para o elemento alto que organiza todo o espaço.',
        story: 'O centro da praça sugere um marco usado como referência pelos exploradores.',
        targetLabel: 'Monumento central',
        lat: 48.85837,
        lng: 2.294481,
        headingValue: 210,
        pitch: 2,
        correctId: 'monument',
        hotspots: [
          {{ id: 'tree', label: 'Árvore lateral', top: '40%', left: '22%' }},
          {{ id: 'monument', label: 'Monumento', top: '30%', left: '55%' }},
          {{ id: 'bench', label: 'Banco', top: '73%', left: '38%' }}
        ]
      }},
      {{
        location: 'Corredor de ruínas',
        heading: 'Encontre a passagem com aparência mais secreta',
        clue: 'A relíquia final está associada ao acesso que parece levar mais fundo.',
        story: 'A última cena pede leitura espacial antes do toque decisivo.',
        targetLabel: 'Arco de entrada',
        lat: 41.89021,
        lng: 12.492231,
        headingValue: 110,
        pitch: 0,
        correctId: 'arch',
        hotspots: [
          {{ id: 'column', label: 'Coluna', top: '34%', left: '24%' }},
          {{ id: 'arch', label: 'Arco antigo', top: '42%', left: '60%' }},
          {{ id: 'stone', label: 'Pedra marcada', top: '76%', left: '48%' }}
        ]
      }}
    ]
  }}),
  computed: {{
    currentRoundData () {{
      return this.rounds[this.currentRound] || this.rounds[this.rounds.length - 1]
    }},
    panoramaElementId () {{
      return '{request.component_key}-streetview'
    }},
    gameOver () {{
      return this.relicsFound >= 3 || this.session.losses >= 3 || this.currentRound >= this.rounds.length
    }},
    finalStatus () {{
      if (this.relicsFound >= 3) {{
        return 'Vitória de exploração'
      }}
      if (this.session.losses >= 3) {{
        return 'Expedição comprometida'
      }}
      return 'Rota concluída'
    }}
  }},
  methods: {{
    resolveGoogleCredentials () {{
      if (typeof window !== 'undefined') {{
        const runtimeKey = window.ENTERT_GOOGLE_MAPS_API_KEY
        const storedKey = window.localStorage.getItem('entert_google_maps_api_key')
        return runtimeKey || storedKey || 'AIzaSyBW5Jl98AP2kj-Fo9_j-mZQPrJ1gADY-08'
      }}
      return 'AIzaSyBW5Jl98AP2kj-Fo9_j-mZQPrJ1gADY-08'
    }},
    ensureGoogleMaps () {{
      return new Promise((resolve, reject) => {{
        if (typeof window !== 'undefined' && window.google && window.google.maps && window.google.maps.StreetViewPanorama) {{
          resolve(window.google)
          return
        }}

        const existingScript = document.getElementById('streetview-adventure-google-maps')
        if (existingScript) {{
          const previousCallback = window.__initStreetViewAdventure
          window.__initStreetViewAdventure = () => {{
            if (typeof previousCallback === 'function') {{
              previousCallback()
            }}
            resolve(window.google)
          }}
          return
        }}

        const scriptTag = document.createElement('script')
        scriptTag.src = `https://maps.googleapis.com/maps/api/js?callback=__initStreetViewAdventure&key=${{this.googleCredentials}}`
        scriptTag.id = 'streetview-adventure-google-maps'
        scriptTag.async = true
        scriptTag.defer = true

        window.__initStreetViewAdventure = () => resolve(window.google)
        scriptTag.onerror = () => reject(new Error('Nao foi possivel carregar o Google Street View.'))
        document.head.appendChild(scriptTag)
      }})
    }},
    async renderPanorama () {{
      const element = document.getElementById(this.panoramaElementId)
      if (!element) {{
        return
      }}

      await this.ensureGoogleMaps()
      this.panoramaInstance = new google.maps.StreetViewPanorama(element, {{
        position: {{ lat: this.currentRoundData.lat, lng: this.currentRoundData.lng }},
        pov: {{ heading: this.currentRoundData.headingValue, pitch: this.currentRoundData.pitch }},
        zoom: 1,
        motionTracking: false,
        addressControl: false,
        linksControl: true,
        panControl: true,
        fullscreenControl: false
      }})
    }},
    enterMap () {{
      this.mapEntered = true
      this.message = 'Mapa aberto. Agora explore o Street View e escolha um hotspot.'
      this.alertType = 'info'
      this.renderPanorama().catch(() => null)
    }},
    hotspotStyle (hotspot) {{
      return {{
        top: hotspot.top,
        left: hotspot.left
      }}
    }},
    inspectHotspot (hotspot) {{
      if (this.roundLocked || this.gameOver) {{
        return
      }}
      this.roundLocked = true
      this.startSessionRound('streetview-adventure')

      if (hotspot.id === this.currentRoundData.correctId) {{
        this.relicsFound += 1
        this.registerWin(40, 'found')
        this.lastDiscovery = `Você localizou ${{hotspot.label}} e revelou a relíquia desta área.`
        this.message = 'Boa leitura da cena. A relíquia foi encontrada.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.lastDiscovery = `O ponto ${{hotspot.label}} chamou atenção, mas não escondia a relíquia.`
        this.message = 'Ponto incorreto. Observe melhor o ambiente antes da próxima escolha.'
        this.alertType = 'error'
      }}

      window.setTimeout(() => {{
        this.currentRound += 1
        this.roundLocked = false
        this.mapEntered = false
        if (!this.gameOver) {{
          this.message = 'Nova pista liberada. Entre no mapa para continuar explorando.'
          this.alertType = 'info'
        }}
      }}, 900)
    }},
    resetGame () {{
      this.resetSession()
      this.currentRound = 0
      this.relicsFound = 0
      this.lastDiscovery = 'A exploração está prestes a começar.'
      this.message = 'Observe a pista e entre no mapa para começar.'
      this.alertType = 'info'
      this.roundLocked = false
      this.mapEntered = false
    }}
  }},
  watch: {{
    currentRound () {{
      this.mapEntered = false
    }}
  }},
  mounted () {{
    this.googleCredentials = this.resolveGoogleCredentials()
    this.$nextTick(() => {{
      this.ensureGoogleMaps().catch((error) => {{
        this.message = error && error.message ? error.message : 'Nao foi possivel abrir o Street View.'
        this.alertType = 'error'
      }})
    }})
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1500px;
}}

.game-surface {{
  border-radius: 28px;
}}

.street-stage {{
  overflow: hidden;
  border-radius: 26px;
  background: #0f172a;
}}

.street-stage__media {{
  position: relative;
  min-height: 420px;
}}

.street-stage__panorama {{
  position: absolute;
  inset: 0;
}}

.street-stage__veil {{
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.18), rgba(15, 23, 42, 0.72));
}}

.street-stage__hud {{
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1;
  color: #fff;
}}

.street-stage__entry {{
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}}

.street-stage__entry-card {{
  max-width: 420px;
  padding: 24px;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.86);
  color: #fff;
  text-align: center;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.28);
}}

.street-stage__label {{
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}}

.street-stage__title {{
  margin-top: 6px;
  font-size: 1.2rem;
  font-weight: 800;
}}

.street-hotspot {{
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -50%);
  background: transparent;
  border: 0;
  cursor: pointer;
}}

.street-hotspot__dot {{
  display: block;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #facc15;
  box-shadow: 0 0 0 8px rgba(250, 204, 21, 0.18);
}}

.street-hotspot__label {{
  display: inline-block;
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.78);
  color: #fff;
  font-size: 0.78rem;
  white-space: nowrap;
}}

.support-card {{
  min-height: 140px;
}}
</style>
"""


def _build_memory_reaction_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Memorize o simbolo alvo e toque rapido quando ele aparecer.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Primeiro memorize o simbolo alvo.</li>
              <li>Depois espere a rodada comecar.</li>
              <li>Toque apenas quando o simbolo correto aparecer.</li>
              <li>Erros ou atraso custam vida.</li>
              <li>Faça 4 acertos para vencer.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Alvo</div>
                <div class="text-h3">{{{{ targetSymbol }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Acertos</div>
                <div class="text-h4">{{{{ session.wins }}}}/4</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mb-4">
            <v-btn color="primary" large :disabled="gameOver || revealMode || roundActive" @click="startRound">
              {{{{ revealMode ? 'Memorizando...' : roundActive ? 'Rodada ativa' : 'Comecar rodada' }}}}
            </v-btn>
          </div>

          <v-card outlined class="pa-6 text-center reaction-stage" :class="stageClass" @click="tapStage">
            <div class="text-overline mb-2">Simbolo atual</div>
            <div class="display-2 mb-3">{{{{ currentSymbol }}}}</div>
            <div class="text-body-1">{{{{ stageHint }}}}</div>
          </v-card>

          <div class="text-center mt-4">
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    symbols: ['★', '◆', '●', '▲'],
    targetSymbol: '★',
    currentSymbol: '•',
    revealMode: false,
    roundActive: false,
    canTap: false,
    message: 'Memorize o alvo e inicie a rodada.',
    alertType: 'info',
    timerId: null
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= 4 || this.session.losses >= this.maxLives
    }},
    stageHint () {{
      if (this.revealMode) {{
        return 'Memorize este simbolo.'
      }}
      if (this.roundActive) {{
        return this.canTap ? 'Toque agora.' : 'Espere o alvo aparecer.'
      }}
      return 'Pronto para a proxima rodada.'
    }},
    stageClass () {{
      return this.canTap ? 'reaction-stage--active' : ''
    }}
  }},
  methods: {{
    startRound () {{
      if (this.gameOver || this.revealMode || this.roundActive) {{
        return
      }}
      this.targetSymbol = this.symbols[Math.floor(Math.random() * this.symbols.length)]
      this.currentSymbol = this.targetSymbol
      this.revealMode = true
      this.message = 'Memorize o simbolo alvo.'
      this.alertType = 'info'
      window.setTimeout(() => {{
        this.revealMode = false
        this.roundActive = true
        this.currentSymbol = this.randomSymbol()
        this.scheduleTarget()
      }}, 1000)
    }},
    randomSymbol () {{
      return this.symbols[Math.floor(Math.random() * this.symbols.length)]
    }},
    scheduleTarget () {{
      this.timerId = window.setTimeout(() => {{
        this.currentSymbol = this.targetSymbol
        this.canTap = true
        this.startSessionRound('memory-reaction')
        window.setTimeout(() => {{
          if (this.canTap) {{
            this.registerLoss('lost')
            this.finishRound('Voce demorou demais.')
          }}
        }}, 900)
      }}, 800)
    }},
    tapStage () {{
      if (!this.roundActive || this.revealMode || this.gameOver) {{
        return
      }}
      if (this.canTap && this.currentSymbol === this.targetSymbol) {{
        this.registerWin(25, 'won')
        this.finishRound('Boa. Reflexo certo no simbolo certo.', 'success')
        return
      }}
      this.registerLoss('lost')
      this.finishRound('Toque errado. Esse nao era o simbolo alvo.', 'error')
    }},
    finishRound (message, type = 'error') {{
      this.roundActive = false
      this.canTap = false
      this.currentSymbol = '•'
      this.message = message
      this.alertType = type
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
    }},
    resetGame () {{
      if (this.timerId) {{
        clearTimeout(this.timerId)
        this.timerId = null
      }}
      this.resetSession()
      this.targetSymbol = '★'
      this.currentSymbol = '•'
      this.revealMode = false
      this.roundActive = false
      this.canTap = false
      this.message = 'Memorize o alvo e inicie a rodada.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.reaction-stage {{
  cursor: pointer;
  min-height: 220px;
}}
.reaction-stage--active {{
  border: 3px solid #2e7d32;
}}
</style>
"""


def _build_duel_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} duel-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="10" xl="9">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Leia o rival, use o teclado e responda no timing certo para vencer a luta.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Cada round o rival prepara um ataque.</li>
              <li>Use <strong>A</strong> para esquivar, <strong>S</strong> para bloquear e <strong>D</strong> para contra-atacar.</li>
              <li>A resposta certa causa dano no rival e rende pontos.</li>
              <li>A resposta errada tira vida do seu lutador.</li>
              <li>Seta para esquerda, baixo e direita tambem funcionam.</li>
            </ul>
          </v-card>

          <v-row>
            <v-col cols="12" md="4">
              <game-stats-bar :session="session" />

              <v-card outlined class="pa-4 mt-4">
                <div class="text-caption">Sua vida</div>
                <v-progress-linear class="mb-3" color="green" :value="(playerHealth / 4) * 100" height="12" rounded />
                <div class="text-caption">Vida rival</div>
                <v-progress-linear class="mb-3" color="red" :value="(rivalHealth / 4) * 100" height="12" rounded />
                <div class="text-caption mb-1">Controle</div>
                <div class="text-body-2">A / ← Esquivar</div>
                <div class="text-body-2">S / ↓ Bloquear</div>
                <div class="text-body-2">D / → Contra</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card class="pa-4 mb-4 duel-stage" outlined>
                <div class="duel-hud d-flex justify-space-between align-center mb-4">
                  <div>
                    <div class="text-overline">Seu lutador</div>
                    <div class="text-h6">{{{{ playerPoseLabel }}}}</div>
                  </div>
                  <div class="text-center">
                    <div class="text-overline">Ataque do rival</div>
                    <div class="text-h5 mb-1">{{{{ currentCue.label }}}}</div>
                    <div class="text-body-2">{{{{ currentCue.hint }}}}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-overline">Rival</div>
                    <div class="text-h6">{{{{ rivalPoseLabel }}}}</div>
                  </div>
                </div>

                <div class="fighters mb-4" :class="ringShake ? 'fighters--shake' : ''">
                  <div class="fighter fighter--player" :style="{{{{ transform: `translateX(${{playerOffset}}px)` }}}}" :class="`fighter--${{{{ playerPose }}}}`">
                    <div class="fighter-head"></div>
                    <div class="fighter-body"></div>
                    <div class="fighter-arm fighter-arm--left"></div>
                    <div class="fighter-arm fighter-arm--right"></div>
                    <div class="fighter-leg fighter-leg--left"></div>
                    <div class="fighter-leg fighter-leg--right"></div>
                  </div>
                  <div class="ring-center-badge">Round {{{{ session.rounds + 1 }}}}</div>
                  <div class="fighter fighter--rival" :style="{{{{ transform: `scaleX(-1) translateX(${{-rivalOffset}}px)` }}}}" :class="`fighter--${{{{ rivalPose }}}}`">
                    <div class="fighter-head"></div>
                    <div class="fighter-body"></div>
                    <div class="fighter-arm fighter-arm--left"></div>
                    <div class="fighter-arm fighter-arm--right"></div>
                    <div class="fighter-leg fighter-leg--left"></div>
                    <div class="fighter-leg fighter-leg--right"></div>
                  </div>
                </div>

                <v-row dense class="mb-2">
                  <v-col cols="12" sm="4">
                    <v-btn block x-large color="primary" :disabled="roundLocked || gameOver" @click="playMove('dodge')">
                      A / ← Esquivar
                    </v-btn>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-btn block x-large color="warning" :disabled="roundLocked || gameOver" @click="playMove('block')">
                      S / ↓ Bloquear
                    </v-btn>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-btn block x-large color="error" :disabled="roundLocked || gameOver" @click="playMove('counter')">
                      D / → Contra
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card>

              <div class="text-center">
                <v-btn color="primary" large class="mr-2" :disabled="roundLocked || gameOver" @click="nextRound">
                  Novo round
                </v-btn>
                <v-btn text large @click="resetGame">
                  Reiniciar
                </v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

const cues = [
  {{
    key: 'high-punch',
    label: 'Jab alto vindo pela esquerda',
    hint: 'Uma resposta rapida muda o round.',
    bestMove: 'dodge'
  }},
  {{
    key: 'body-shot',
    label: 'Golpe forte no corpo',
    hint: 'Absorver bem o impacto vale mais do que correr.',
    bestMove: 'block'
  }},
  {{
    key: 'slow-hook',
    label: 'Gancho lento e previsivel',
    hint: 'Esta e a chance de virar o round.',
    bestMove: 'counter'
  }}
]

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    playerHealth: 4,
    rivalHealth: 4,
    roundLocked: false,
    currentCue: cues[0],
    playerPose: 'idle',
    rivalPose: 'idle',
    playerOffset: 0,
    rivalOffset: 0,
    ringShake: false,
    actionTimer: null,
    message: 'Leia o ataque do rival e escolha sua resposta.',
    alertType: 'info'
  }}),
  computed: {{
    gameOver () {{
      return this.playerHealth <= 0 || this.rivalHealth <= 0
    }},
    playerPoseLabel () {{
      return this.playerPose === 'idle' ? 'Em guarda' : this.playerPose
    }},
    rivalPoseLabel () {{
      return this.rivalPose === 'idle' ? 'Lendo voce' : this.rivalPose
    }}
  }},
  created () {{
    window.addEventListener('keydown', this.handleKeydown)
    this.nextRound()
  }},
  beforeDestroy () {{
    window.removeEventListener('keydown', this.handleKeydown)
    if (this.actionTimer) {{
      clearTimeout(this.actionTimer)
    }}
  }},
  methods: {{
    handleKeydown (event) {{
      const key = event.key.toLowerCase()
      if (key === 'a' || event.key === 'ArrowLeft') {{
        this.playMove('dodge')
      }} else if (key === 's' || event.key === 'ArrowDown') {{
        this.playMove('block')
      }} else if (key === 'd' || event.key === 'ArrowRight') {{
        this.playMove('counter')
      }}
    }},
    setPoses (playerPose, rivalPose) {{
      this.playerPose = playerPose
      this.rivalPose = rivalPose
      if (this.actionTimer) {{
        clearTimeout(this.actionTimer)
      }}
      this.actionTimer = window.setTimeout(() => {{
        this.playerPose = 'idle'
        this.rivalPose = 'idle'
        this.playerOffset = 0
        this.rivalOffset = 0
        this.ringShake = false
        this.actionTimer = null
      }}, 800)
    }},
    nextRound () {{
      if (this.gameOver) {{
        return
      }}
      this.roundLocked = false
      this.currentCue = cues[Math.floor(Math.random() * cues.length)]
      this.playerPose = 'idle'
      this.playerOffset = 0
      this.rivalPose = this.currentCue.bestMove === 'dodge' ? 'punch-high' : this.currentCue.bestMove === 'block' ? 'body-shot' : 'hook'
      this.rivalOffset = 12
      this.message = 'Novo round. Leia o ataque e responda.'
      this.alertType = 'info'
    }},
    playMove (move) {{
      if (this.roundLocked || this.gameOver) {{
        return
      }}
      this.roundLocked = true
      this.startSessionRound('playing')
      if (move === this.currentCue.bestMove) {{
        this.rivalHealth -= 1
        this.playerOffset = 20
        this.rivalOffset = -18
        this.ringShake = true
        this.setPoses(move === 'counter' ? 'counter' : move, 'hit')
        this.registerWin(40, 'won')
        this.message = this.gameOver
          ? 'Nocaute. Voce venceu a luta.'
          : 'Boa leitura. O rival sentiu o golpe.'
        this.alertType = 'success'
      }} else {{
        this.playerHealth -= 1
        this.playerOffset = -14
        this.rivalOffset = 18
        this.ringShake = true
        this.setPoses(move, 'pressure')
        this.registerLoss('lost')
        this.message = this.gameOver
          ? 'Seu lutador caiu. Fim de luta.'
          : 'Voce respondeu mal e tomou dano.'
        this.alertType = 'error'
      }}
      if (!this.gameOver) {{
        window.setTimeout(() => {{
          this.nextRound()
        }}, 1100)
      }}
    }},
    resetGame () {{
      this.resetSession()
      this.playerHealth = 4
      this.rivalHealth = 4
      this.roundLocked = false
      this.playerPose = 'idle'
      this.rivalPose = 'idle'
      this.playerOffset = 0
      this.rivalOffset = 0
      this.ringShake = false
      this.message = 'Luta reiniciada. Leia o ataque do rival.'
      this.alertType = 'info'
      this.nextRound()
    }}
  }}
}}
</script>

<style scoped>
.duel-shell {{
  max-width: 1400px;
}}

.game-surface {{
  border-radius: 28px;
}}

.duel-stage {{
  background: linear-gradient(135deg, #1e293b, #334155);
  color: #fff;
  overflow: hidden;
}}

.fighters {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  align-items: end;
  min-height: 260px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at center, rgba(255,255,255,0.08), transparent 35%),
    linear-gradient(180deg, rgba(255,255,255,0.04), rgba(0,0,0,0.12));
}}

.ring-center-badge {{
  align-self: center;
  justify-self: center;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(255,255,255,0.14);
  font-weight: 700;
}}

.fighter {{
  position: relative;
  width: 120px;
  height: 200px;
  margin: 0 auto;
  transition: transform 0.18s ease;
}}

.fighter-head,
.fighter-body,
.fighter-arm,
.fighter-leg {{
  position: absolute;
  border-radius: 999px;
}}

.fighter-head {{
  top: 0;
  left: 42px;
  width: 36px;
  height: 36px;
  background: #f4c095;
}}

.fighter-body {{
  top: 34px;
  left: 40px;
  width: 40px;
  height: 78px;
  background: currentColor;
  border-radius: 18px;
}}

.fighter-arm {{
  top: 48px;
  width: 14px;
  height: 68px;
  background: currentColor;
  transform-origin: top center;
}}

.fighter-arm--left {{
  left: 25px;
}}

.fighter-arm--right {{
  right: 25px;
}}

.fighter-leg {{
  top: 104px;
  width: 14px;
  height: 82px;
  background: currentColor;
  transform-origin: top center;
}}

.fighter-leg--left {{
  left: 44px;
}}

.fighter-leg--right {{
  right: 44px;
}}

.fighter--player {{
  color: #38bdf8;
}}

.fighter--rival {{
  color: #f97316;
  transform: scaleX(-1);
}}

.fighter--dodge {{
  transform: translateX(-16px) rotate(-8deg);
}}

.fighter--block {{
  transform: translateY(-4px);
}}

.fighter--counter,
.fighter--punch-high,
.fighter--body-shot,
.fighter--hook,
.fighter--pressure {{
  transform: translateX(10px);
}}

.fighter--hit {{
  transform: translateX(-10px) rotate(-6deg);
}}

.fighter--dodge .fighter-arm--left,
.fighter--dodge .fighter-arm--right {{
  transform: rotate(18deg);
}}

.fighter--block .fighter-arm--left,
.fighter--block .fighter-arm--right {{
  transform: rotate(-58deg) translateY(-6px);
}}

.fighter--counter .fighter-arm--right,
.fighter--punch-high .fighter-arm--right,
.fighter--pressure .fighter-arm--right {{
  transform: rotate(74deg) translateY(-4px);
}}

.fighter--hook .fighter-arm--left {{
  transform: rotate(-96deg);
}}

.fighter--body-shot .fighter-arm--right {{
  transform: rotate(38deg) translateY(12px);
}}

@media (max-width: 959px) {{
  .fighters {{
    grid-template-columns: 1fr;
    justify-items: center;
  }}
  .ring-center-badge {{
    order: -1;
  }}
}}

.fighters--shake {{
  animation: ringShake 0.22s linear 2;
}}

@keyframes ringShake {{
  0% {{ transform: translateX(0); }}
  25% {{ transform: translateX(-4px); }}
  50% {{ transform: translateX(4px); }}
  75% {{ transform: translateX(-3px); }}
  100% {{ transform: translateX(0); }}
}}
</style>
"""


def _build_runner_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-6 text-center" elevation="6">
          <div class="text-overline mb-2">Generated game</div>
          <h1 class="text-h4 mb-2">{request.game_name}</h1>
          <p class="mb-6">
            Toque para pular os obstaculos e sobreviver o maximo de rodadas possivel.
          </p>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Clique em comecar para iniciar a corrida.</li>
              <li>Quando um obstaculo aparecer, toque em pular no momento certo.</li>
              <li>Se voce pular cedo demais ou tarde demais, perde uma vida.</li>
              <li>Cada obstaculo superado aumenta sua pontuacao.</li>
              <li>Sobreviva ate o fim das vidas para buscar recorde.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Distancia</div>
                <div class="text-h5">{{{{ distance }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Velocidade</div>
                <div class="text-h5">{{{{ speed }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Vidas</div>
                <div class="text-h5">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="runner-stage mb-6" :class="stageClass" @click="jump">
            <div class="runner-obstacle" :style="obstacleStyle"></div>
            <div class="runner-player" :class="isJumping ? 'runner-player--jumping' : ''"></div>
            <div class="runner-hint">{{{{ stageHint }}}}</div>
          </div>

          <div class="text-center">
            <v-btn color="primary" large class="mr-2 mb-2" :disabled="gameOver" @click="startGame">
              {{{{ running ? 'Jogar novamente' : 'Comecar corrida' }}}}
            </v-btn>
            <v-btn color="success" large class="mb-2" :disabled="!running || gameOver || isJumping" @click="jump">
              Pular
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    distance: 0,
    speed: 1,
    running: false,
    isJumping: false,
    obstacleCleared: false,
    obstaclePosition: 100,
    tickId: null,
    jumpTimeoutId: null,
    message: 'Comece a corrida e pule quando o bloco se aproximar.',
    alertType: 'info'
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives
    }},
    stageClass () {{
      return this.running ? 'runner-stage--running' : 'runner-stage--idle'
    }},
    stageHint () {{
      if (!this.running) {{
        return 'Toque em Comecar corrida'
      }}
      if (this.obstacleInJumpZone) {{
        return 'Pule agora'
      }}
      return 'Prepare o pulo'
    }},
    obstacleStyle () {{
      return {{
        left: `${{this.obstaclePosition}}%`
      }}
    }},
    obstacleInJumpZone () {{
      return this.obstaclePosition <= 38 && this.obstaclePosition >= 18
    }},
    obstacleInDangerZone () {{
      return this.obstaclePosition <= 24 && this.obstaclePosition >= 8
    }}
  }},
  beforeDestroy () {{
    this.clearTick()
    this.clearJumpTimeout()
  }},
  methods: {{
    clearTick () {{
      if (this.tickId) {{
        clearInterval(this.tickId)
        this.tickId = null
      }}
    }},
    clearJumpTimeout () {{
      if (this.jumpTimeoutId) {{
        clearTimeout(this.jumpTimeoutId)
        this.jumpTimeoutId = null
      }}
    }},
    startGame () {{
      if (this.gameOver) {{
        return
      }}
      this.clearTick()
      this.clearJumpTimeout()
      this.running = true
      this.distance = 0
      this.speed = 1
      this.obstaclePosition = 100
      this.isJumping = false
      this.obstacleCleared = false
      this.message = 'Obstaculo vindo. Prepare o pulo.'
      this.alertType = 'info'
      this.tickId = setInterval(this.advanceGame, 100)
    }},
    advanceGame () {{
      if (!this.running || this.gameOver) {{
        this.clearTick()
        return
      }}
      this.obstaclePosition -= 5 + this.speed
      this.distance += 1

      if (this.obstacleInDangerZone && !this.isJumping) {{
        this.registerLoss('lost')
        this.alertType = 'error'
        this.message = this.gameOver
          ? 'Fim de corrida. O obstaculo te derrubou.'
          : 'Voce bateu no obstaculo. Tente de novo.'
        this.running = false
        this.clearTick()
        return
      }}

      if (this.obstaclePosition < 8 && this.isJumping && !this.obstacleCleared) {{
        this.obstacleCleared = true
        this.startSessionRound('running')
        this.registerWin(15, 'won')
        this.speed = Math.min(this.speed + 1, 6)
        this.message = 'Boa. Obstaculo superado.'
        this.alertType = 'success'
      }}

      if (this.obstaclePosition < -10) {{
        this.obstaclePosition = 100
        this.obstacleCleared = false
        if (this.running) {{
          this.message = 'Novo obstaculo chegando.'
          this.alertType = 'info'
        }}
      }}
    }},
    jump () {{
      if (!this.running || this.isJumping || this.gameOver) {{
        return
      }}
      this.clearJumpTimeout()
      this.isJumping = true
      this.message = this.obstacleInJumpZone
        ? 'Boa hora para pular.'
        : 'Pulo acionado. Prepare a aterrissagem.'
      this.alertType = this.obstacleInJumpZone ? 'success' : 'warning'
      this.jumpTimeoutId = window.setTimeout(() => {{
        this.isJumping = false
        this.jumpTimeoutId = null
      }}, 700)
    }},
    resetGame () {{
      this.clearTick()
      this.clearJumpTimeout()
      this.resetSession()
      this.distance = 0
      this.speed = 1
      this.running = false
      this.isJumping = false
      this.obstacleCleared = false
      this.obstaclePosition = 100
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.runner-stage {{
  position: relative;
  min-height: 220px;
  border-radius: 24px;
  overflow: hidden;
  transition: background-color 0.2s ease;
}}

.runner-stage--idle {{
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
}}

.runner-stage--running {{
  background: linear-gradient(135deg, #93c5fd, #60a5fa);
}}

.runner-player {{
  position: absolute;
  left: 18%;
  bottom: 24px;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #0f172a;
  transition: transform 0.18s ease;
}}

.runner-player--jumping {{
  transform: translateY(-90px);
}}

.runner-obstacle {{
  position: absolute;
  bottom: 24px;
  width: 28px;
  height: 54px;
  border-radius: 8px;
  background: #dc2626;
  transform: translateX(-50%);
}}

.runner-hint {{
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  color: #0f172a;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.75);
  padding: 6px 12px;
  border-radius: 999px;
}}
</style>
"""


def _build_car_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-6 text-center" elevation="6">
          <div class="text-overline mb-2">Generated game</div>
          <h1 class="text-h4 mb-2">{request.game_name}</h1>
          <p class="mb-6">
            Troque de faixa, desvie do transito e chegue ao final da corrida sem acabar com o carro.
          </p>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Comece a corrida para colocar o carro na pista.</li>
              <li>Use esquerda e direita para trocar de faixa.</li>
              <li>Desvie dos outros carros para continuar acelerando.</li>
              <li>Cada carro evitado aumenta a distancia, a velocidade e os pontos.</li>
              <li>Chegue a 12 desvios para vencer a corrida.</li>
              <li>Ao perder 3 vidas, a corrida termina.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Desvios</div>
                <div class="text-h5">{{{{ avoidedCars }}}} / {{{{ targetAvoids }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Velocidade</div>
                <div class="text-h5">{{{{ speed.toFixed(1) }}}}x</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-3">
                <div class="text-caption">Vidas</div>
                <div class="text-h5">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-progress-linear
            class="mb-4"
            height="14"
            rounded
            color="success"
            :value="progressValue"
          />

          <div class="road-stage mb-6" :class="stageClass" @click="handleStageTap">
            <div class="lane-marker lane-marker--left"></div>
            <div class="lane-marker lane-marker--right"></div>
            <div class="player-car" :style="playerCarStyle"></div>
            <div class="traffic-car" :style="trafficCarStyle"></div>
            <div class="traffic-shadow" :style="trafficCarStyle"></div>
            <div class="road-hint">{{{{ stageHint }}}}</div>
          </div>

          <v-row dense class="mb-2">
            <v-col cols="6">
              <v-btn block large color="primary" :disabled="!running || gameOver || lane === 0" @click="moveLeft">
                Esquerda
              </v-btn>
            </v-col>
            <v-col cols="6">
              <v-btn block large color="primary" :disabled="!running || gameOver || lane === 2" @click="moveRight">
                Direita
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center">
            <v-btn color="success" large class="mr-2 mb-2" :disabled="gameOver" @click="startGame">
              {{{{ running ? 'Reiniciar corrida' : 'Comecar corrida' }}}}
            </v-btn>
            <v-btn text large class="mb-2" @click="resetGame">
              Resetar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    targetAvoids: 12,
    running: false,
    lane: 1,
    trafficLane: 1,
    trafficY: -90,
    speed: 1.2,
    avoidedCars: 0,
    distance: 0,
    tickId: null,
    flashState: 'idle',
    message: 'Comece a corrida e troque de faixa para evitar os carros.',
    alertType: 'info'
  }}),
  computed: {{
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives || this.avoidedCars >= this.targetAvoids
    }},
    progressValue () {{
      return (this.avoidedCars / this.targetAvoids) * 100
    }},
    stageHint () {{
      if (!this.running) {{
        return 'Toque em Comecar corrida'
      }}
      if (this.trafficLane === this.lane) {{
        return 'Mude de faixa agora'
      }}
      return 'Pista livre, mantenha o ritmo'
    }},
    stageClass () {{
      const base = this.running ? 'road-stage--running' : 'road-stage--idle'
      return `${{base}} road-stage--${{this.flashState}}`
    }},
    playerCarStyle () {{
      return {{
        left: `${{18 + this.lane * 28}}%`
      }}
    }},
    trafficCarStyle () {{
      return {{
        left: `${{18 + this.trafficLane * 28}}%`,
        top: `${{this.trafficY}}px`
      }}
    }}
  }},
  beforeDestroy () {{
    this.clearTick()
  }},
  methods: {{
    clearTick () {{
      if (this.tickId) {{
        clearInterval(this.tickId)
        this.tickId = null
      }}
    }},
    setFlashState (state) {{
      this.flashState = state
      window.setTimeout(() => {{
        if (this.flashState === state) {{
          this.flashState = this.running ? 'running' : 'idle'
        }}
      }}, 220)
    }},
    randomLane () {{
      return Math.floor(Math.random() * 3)
    }},
    startGame () {{
      this.clearTick()
      this.running = true
      this.lane = 1
      this.trafficLane = this.randomLane()
      this.trafficY = -90
      this.speed = 1.2
      this.avoidedCars = 0
      this.distance = 0
      this.flashState = 'running'
      this.message = 'Corrida iniciada. Fique de olho no transito.'
      this.alertType = 'info'
      this.tickId = setInterval(this.advanceGame, 90)
    }},
    advanceGame () {{
      if (!this.running || this.gameOver) {{
        this.clearTick()
        return
      }}
      this.trafficY += 10 + (this.speed * 2.2)
      this.distance += Math.round(this.speed * 3)

      const collisionWindow = this.trafficY >= 170 && this.trafficY <= 248
      if (collisionWindow && this.trafficLane === this.lane) {{
        this.registerLoss('lost')
        this.running = false
        this.clearTick()
        this.setFlashState('crash')
        this.alertType = 'error'
        this.message = this.session.losses >= this.maxLives
          ? 'Fim de corrida. O transito te parou.'
          : 'Batida. Tente trocar de faixa mais cedo.'
        return
      }}

      if (this.trafficY > 280) {{
        this.startSessionRound('driving')
        this.registerWin(18, 'won')
        this.avoidedCars += 1
        this.speed = Math.min(this.speed + 0.2, 3.8)
        this.trafficY = -90
        this.trafficLane = this.randomLane()
        this.setFlashState('boost')
        this.alertType = 'success'
        this.message = this.avoidedCars >= this.targetAvoids
          ? 'Vitoria. Voce cruzou a linha de chegada.'
          : 'Boa. Carro evitado, siga acelerando.'
        if (this.avoidedCars >= this.targetAvoids) {{
          this.running = false
          this.clearTick()
        }}
      }}
    }},
    handleStageTap (event) {{
      if (!this.running || this.gameOver) {{
        return
      }}
      const bounds = event.currentTarget.getBoundingClientRect()
      const relativeX = event.clientX - bounds.left
      if (relativeX < bounds.width / 2) {{
        this.moveLeft()
      }} else {{
        this.moveRight()
      }}
    }},
    moveLeft () {{
      if (!this.running || this.gameOver || this.lane === 0) {{
        return
      }}
      this.lane -= 1
      this.message = 'Mudou para a esquerda.'
      this.alertType = 'info'
    }},
    moveRight () {{
      if (!this.running || this.gameOver || this.lane === 2) {{
        return
      }}
      this.lane += 1
      this.message = 'Mudou para a direita.'
      this.alertType = 'info'
    }},
    resetGame () {{
      this.clearTick()
      this.resetSession()
      this.running = false
      this.lane = 1
      this.trafficLane = 1
      this.trafficY = -90
      this.speed = 1.2
      this.avoidedCars = 0
      this.distance = 0
      this.flashState = 'idle'
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.road-stage {{
  position: relative;
  min-height: 280px;
  border-radius: 24px;
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}}

.road-stage--idle {{
  background: linear-gradient(180deg, #94a3b8, #64748b);
}}

.road-stage--running {{
  background: linear-gradient(180deg, #475569, #1e293b);
}}

.road-stage--boost {{
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.35);
}}

.road-stage--crash {{
  transform: scale(0.99);
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.35);
}}

.lane-marker {{
  position: absolute;
  top: 0;
  bottom: 0;
  width: 6px;
  background: repeating-linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.85) 0,
    rgba(255, 255, 255, 0.85) 18px,
    transparent 18px,
    transparent 36px
  );
}}

.lane-marker--left {{
  left: 33.33%;
}}

.lane-marker--right {{
  left: 66.66%;
}}

.player-car,
.traffic-car {{
  position: absolute;
  width: 42px;
  height: 72px;
  transform: translateX(-50%);
  border-radius: 12px;
}}

.player-car {{
  bottom: 20px;
  background: linear-gradient(180deg, #22c55e, #15803d);
}}

.traffic-car {{
  background: linear-gradient(180deg, #ef4444, #b91c1c);
}}

.traffic-shadow {{
  position: absolute;
  width: 42px;
  height: 72px;
  transform: translateX(-50%);
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.18);
  filter: blur(10px);
}}

.road-hint {{
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.55);
  padding: 6px 12px;
  border-radius: 999px;
}}
</style>
"""


def _build_quiz_component(request: GameGenerationRequest, references: list[GameReference] | None = None) -> str:
    layout_profile = _select_layout_profile(request, "quiz", references=references)
    if layout_profile == "question-stack":
        return f"""<template>
  <v-container class="{request.component_key} py-8">
    <v-row class="text-center">
      <v-col cols="12">
        <div class="text-overline mb-2">Generated game</div>
        <h1 class="text-h4 mb-2">{request.game_name}</h1>
        <p class="mb-6">Uma pergunta por vez, com leitura simples e decisao rapida.</p>
      </v-col>
    </v-row>

    <v-row justify="center">
      <v-col cols="12" md="8" lg="7">
        <v-alert v-if="message" dense text :type="alertType" class="mb-4">
          {{{{ message }}}}
        </v-alert>

        <v-card outlined class="pa-5 mb-4">
          <div class="text-overline mb-2">Pergunta atual</div>
          <div class="text-h5">{{{{ currentQuestion.prompt }}}}</div>
        </v-card>

        <v-radio-group :value="selectedOption" class="question-stack">
          <v-radio
            v-for="option in currentQuestion.options"
            :key="option"
            :label="option"
            :value="option"
            :disabled="gameOver || roundLocked"
            @change="answer(option)"
          />
        </v-radio-group>

        <v-row class="mt-6">
          <v-col cols="12" sm="4">
            <v-card outlined class="pa-4 text-center">
              <div class="text-caption">Pergunta</div>
              <div class="text-h5">{{{{ currentIndex + 1 }}}}/{{{{ questions.length }}}}</div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card outlined class="pa-4 text-center">
              <div class="text-caption">Vidas</div>
              <div class="text-h5">{{{{ livesLeft }}}}</div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card outlined class="pa-4 text-center">
              <div class="text-caption">Pontos</div>
              <div class="text-h5">{{{{ session.score }}}}</div>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    currentIndex: 0,
    roundLocked: false,
    selectedOption: null,
    message: 'Escolha uma resposta.',
    alertType: 'info',
    questions: [
      {{ prompt: 'Qual cor era o cavalo branco de Napoleao?', answer: 'Branco', options: ['Azul', 'Branco', 'Verde', 'Preto'] }},
      {{ prompt: 'Qual palavra combina com um jogo de conhecimento rapido?', answer: 'Quiz', options: ['Quiz', 'Porta', 'Rua', 'Mochila'] }},
      {{ prompt: 'Qual dessas lembra um desafio de memoria?', answer: 'Sequencia', options: ['Janela', 'Sequencia', 'Trator', 'Tapete'] }}
    ]
  }}),
  computed: {{
    currentQuestion () {{
      return this.questions[this.currentIndex] || this.questions[0]
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives || this.session.wins >= 3
    }}
  }},
  methods: {{
    answer (option) {{
      if (this.roundLocked || this.gameOver) return
      this.roundLocked = true
      this.selectedOption = option
      this.startSessionRound('answering')
      if (option === this.currentQuestion.answer) {{
        this.registerWin(35, 'won')
        this.message = 'Resposta correta.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = `Errado. A correta era "${{this.currentQuestion.answer}}".`
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        this.currentIndex = (this.currentIndex + 1) % this.questions.length
        this.roundLocked = false
        this.selectedOption = null
      }}, 900)
    }}
  }}
}}
</script>

<style scoped>
.question-stack {{
  background: rgba(0, 0, 0, 0.02);
  border-radius: 20px;
  padding: 20px 24px;
}}
</style>
"""
    variant = _variant_index(request, "quiz", 2)
    if variant == 1:
        return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Escolha a melhor categoria para cada pista e construa sua sequencia de acertos.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Leia a pista da rodada.</li>
              <li>Escolha a categoria correta entre quatro opcoes.</li>
              <li>Acertos seguidos aumentam o bonus.</li>
              <li>Erros quebram a sequencia e custam uma vida.</li>
              <li>Alcance 120 pontos antes de perder 3 vidas.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Rodada</div>
                <div class="text-h4">{{{{ currentIndex + 1 }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Bonus atual</div>
                <div class="text-h4">x{{{{ streakMultiplier }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card outlined class="pa-4 mb-4">
            <div class="text-overline mb-2">Pista</div>
            <div class="text-h6">{{{{ currentQuestion.prompt }}}}</div>
          </v-card>

          <v-row dense>
            <v-col v-for="option in currentQuestion.options" :key="option" cols="12" sm="6">
              <v-btn
                block
                large
                class="mb-2 quiz-option"
                :disabled="gameOver || roundLocked"
                :color="optionColor(option)"
                @click="answer(option)"
              >
                {{{{ option }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center mt-4">
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    currentIndex: 0,
    roundLocked: false,
    selectedOption: null,
    message: 'Escolha a categoria certa para cada pista.',
    alertType: 'info',
    questions: [
      {{ prompt: 'Algo que voce pisaria para acelerar em uma corrida.', answer: 'veiculo', options: ['veiculo', 'cozinha', 'musica', 'roupa'] }},
      {{ prompt: 'Uma coisa que voce usaria para responder perguntas.', answer: 'quiz', options: ['quiz', 'jardim', 'praia', 'janela'] }},
      {{ prompt: 'Algo que pode aparecer numa cruzadinha.', answer: 'palavra', options: ['palavra', 'motor', 'chuveiro', 'cadeira'] }},
      {{ prompt: 'Um tipo de jogo com reflexo rapido.', answer: 'reacao', options: ['reacao', 'travesseiro', 'mapa', 'panela'] }}
    ]
  }}),
  computed: {{
    currentQuestion () {{
      return this.questions[this.currentIndex] || this.questions[this.questions.length - 1]
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    streakMultiplier () {{
      return Math.min(this.session.streak + 1, 4)
    }},
    gameOver () {{
      return this.session.score >= 120 || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    optionColor (option) {{
      if (!this.roundLocked || this.selectedOption !== option) {{
        return 'primary'
      }}
      return option === this.currentQuestion.answer ? 'success' : 'error'
    }},
    answer (option) {{
      if (this.roundLocked || this.gameOver) {{
        return
      }}
      this.roundLocked = true
      this.selectedOption = option
      this.startSessionRound('answering')
      if (option === this.currentQuestion.answer) {{
        this.registerWin(15 * this.streakMultiplier, 'won')
        this.message = 'Boa. Categoria correta.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.session.streak = 0
        this.message = `Errado. A resposta certa era "${{this.currentQuestion.answer}}".`
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        this.currentIndex = (this.currentIndex + 1) % this.questions.length
        this.roundLocked = false
        this.selectedOption = null
        if (!this.gameOver) {{
          this.message = 'Nova pista liberada.'
          this.alertType = 'info'
        }}
      }}, 900)
    }},
    resetGame () {{
      this.resetSession()
      this.currentIndex = 0
      this.roundLocked = false
      this.selectedOption = null
      this.message = 'Quiz reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1480px;
}}

.game-surface {{
  border-radius: 28px;
}}

.quiz-option {{
  min-height: 72px;
  white-space: normal;
}}
</style>
"""
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Responda rapido, acumule pontos e nao gaste todas as vidas.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Leia a pergunta no topo da rodada.</li>
              <li>Escolha uma entre quatro respostas.</li>
              <li>Acertos aumentam a pontuacao e a sequencia.</li>
              <li>Erros consomem uma vida.</li>
              <li>Chegue a 3 acertos para vencer a partida.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Pergunta</div>
                <div class="text-h4">{{{{ currentIndex + 1 }}}}/{{{{ questions.length }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Objetivo</div>
                <div class="text-h4">{{{{ targetWins }}}} acertos</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card outlined class="pa-4 mb-4">
            <div class="text-overline mb-2">Pergunta atual</div>
            <div class="text-h6">{{{{ currentQuestion.prompt }}}}</div>
          </v-card>

          <v-row dense>
            <v-col
              v-for="option in currentQuestion.options"
              :key="option"
              cols="12"
              sm="6"
            >
              <v-btn
                block
                large
                class="mb-2 quiz-option"
                :disabled="gameOver || roundLocked"
                :color="optionColor(option)"
                @click="answer(option)"
              >
                {{{{ option }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center mt-4">
            <v-btn text large @click="resetGame">
              Reiniciar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    targetWins: 3,
    maxLives: 3,
    currentIndex: 0,
    roundLocked: false,
    selectedOption: null,
    message: 'Escolha a resposta correta para ganhar a rodada.',
    alertType: 'info',
    questions: [
      {{
        prompt: 'Qual palavra combina melhor com velocidade?',
        answer: 'corrida',
        options: ['corrida', 'almofada', 'janela', 'plantas']
      }},
      {{
        prompt: 'Qual resposta indica algo que pode ser medido em segundos?',
        answer: 'tempo',
        options: ['tempo', 'tijolo', 'garfo', 'quadro']
      }},
      {{
        prompt: 'Qual dessas palavras lembra um desafio de conhecimento?',
        answer: 'quiz',
        options: ['chuva', 'quiz', 'cadeira', 'travesseiro']
      }},
      {{
        prompt: 'Qual opcao representa algo que voce pode memorizar?',
        answer: 'sequencia',
        options: ['neblina', 'sequencia', 'casaco', 'martelo']
      }}
    ]
  }}),
  computed: {{
    currentQuestion () {{
      return this.questions[this.currentIndex] || this.questions[this.questions.length - 1]
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= this.targetWins || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    optionColor (option) {{
      if (!this.roundLocked || this.selectedOption !== option) {{
        return 'primary'
      }}
      return option === this.currentQuestion.answer ? 'success' : 'error'
    }},
    answer (option) {{
      if (this.roundLocked || this.gameOver) {{
        return
      }}
      this.roundLocked = true
      this.selectedOption = option
      this.startSessionRound('answering')
      if (option === this.currentQuestion.answer) {{
        this.registerWin(40, 'won')
        this.message = 'Boa. Resposta correta.'
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = `Errado. A resposta certa era "${{this.currentQuestion.answer}}".`
        this.alertType = 'error'
      }}

      window.setTimeout(() => {{
        this.advanceRound()
      }}, 900)
    }},
    advanceRound () {{
      this.currentIndex = (this.currentIndex + 1) % this.questions.length
      this.roundLocked = false
      this.selectedOption = null
      if (this.gameOver) {{
        this.message = this.session.wins >= this.targetWins
          ? 'Vitoria. Voce dominou o quiz.'
          : 'Fim de jogo. Acabaram as vidas.'
        this.alertType = this.session.wins >= this.targetWins ? 'success' : 'error'
        return
      }}
      this.message = 'Proxima pergunta pronta.'
      this.alertType = 'info'
    }},
    resetGame () {{
      this.resetSession()
      this.currentIndex = 0
      this.roundLocked = false
      this.selectedOption = null
      this.message = 'Quiz reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.quiz-option {{
  min-height: 72px;
  white-space: normal;
}}
</style>
"""


def _build_crossword_component(request: GameGenerationRequest, references: list[GameReference] | None = None) -> str:
    layout_profile = _select_layout_profile(request, "crossword", references=references)
    if layout_profile == "workbench":
        return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Uma bancada de palavra e dica, com montagem visual mais aberta.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-row>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 mb-4">
                <div class="text-overline mb-2">Dica</div>
                <div class="text-h6">{{{{ currentWord.clue }}}}</div>
              </v-card>

              <v-card outlined class="pa-4 mb-4">
                <div class="text-caption">Palavras completas</div>
                <div class="text-h4">{{{{ session.wins }}}}/3</div>
                <div class="text-caption mt-3">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>

              <v-card outlined class="pa-4">
                <div class="text-subtitle-2 mb-2">Como jogar</div>
                <ul class="mb-0">
                  <li>Leia a dica.</li>
                  <li>Monte a palavra com as letras disponiveis.</li>
                  <li>Confirme para validar.</li>
                </ul>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card outlined class="pa-4 mb-4 workbench-answer">
                <div class="text-overline mb-2">Resposta</div>
                <div class="letter-slots">
                  <div v-for="(letter, index) in currentWord.answer.split('')" :key="index" class="letter-slot">
                    {{{{ guess[index] || '_' }}}}
                  </div>
                </div>
              </v-card>

              <v-card outlined class="pa-4 mb-4">
                <div class="text-overline mb-2">Letras disponiveis</div>
                <v-row dense>
                  <v-col v-for="(letter, index) in currentWord.letters" :key="letter + index" cols="3" sm="2">
                    <v-btn block large color="primary" :disabled="gameOver || roundLocked || usedIndices.includes(index)" @click="pickLetter(letter, index)">
                      {{{{ letter }}}}
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card>

              <div class="text-right">
                <v-btn color="primary" class="mr-2" :disabled="gameOver || roundLocked || !guess" @click="submitGuess">Confirmar</v-btn>
                <v-btn text large class="mr-2" @click="resetWord">Limpar</v-btn>
                <v-btn text large @click="resetGame">Reiniciar</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  mixins: [GameSessionMixin],
  data: () => ({{
    targetWins: 3,
    maxLives: 3,
    currentWordIndex: 0,
    guess: '',
    usedIndices: [],
    roundLocked: false,
    message: 'Monte a palavra com a dica ao lado.',
    alertType: 'info',
    words: [
      {{ clue: 'Jogo de perguntas com opcoes', answer: 'QUIZ', letters: ['Q', 'U', 'I', 'Z', 'A', 'O'] }},
      {{ clue: 'Escolha entre varias respostas', answer: 'OPCAO', letters: ['O', 'P', 'C', 'A', 'O', 'S'] }},
      {{ clue: 'Jogo de porta com premio escondido', answer: 'TESOURO', letters: ['T', 'E', 'S', 'O', 'U', 'R', 'O', 'L'] }}
    ]
  }}),
  computed: {{
    currentWord () {{
      return this.words[this.currentWordIndex] || this.words[this.words.length - 1]
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= this.targetWins || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    pickLetter (letter, index) {{
      if (this.gameOver || this.roundLocked) return
      this.startSessionRound('spelling')
      this.guess += letter
      this.usedIndices.push(index)
    }},
    submitGuess () {{
      if (this.gameOver || this.roundLocked || !this.guess) return
      this.roundLocked = true
      if (this.guess === this.currentWord.answer) {{
        this.registerWin(this.currentWord.answer.length * 10, 'won')
        this.message = `Boa. Palavra correta: ${{this.currentWord.answer}}.`
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = `Errado. A palavra era ${{this.currentWord.answer}}.`
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        if (!this.gameOver) {{
          this.currentWordIndex = (this.currentWordIndex + 1) % this.words.length
          this.resetWord()
        }}
      }}, 900)
    }},
    resetWord () {{
      this.guess = ''
      this.usedIndices = []
      this.roundLocked = false
    }},
    resetGame () {{
      this.resetSession()
      this.currentWordIndex = 0
      this.resetWord()
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1480px;
}}

.game-surface {{
  border-radius: 28px;
}}

.workbench-answer {{
  min-height: 150px;
}}

.letter-slots {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  gap: 10px;
}}

.letter-slot {{
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  font-size: 1.35rem;
  font-weight: 700;
}}
</style>
"""
    variant = _variant_index(request, "crossword", 2)
    if variant == 1:
        return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Monte a palavra embaralhada antes de acabar o limite de erros.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Leia a dica da palavra.</li>
              <li>Monte a resposta com as letras embaralhadas.</li>
              <li>Use limpar se quiser recomecar a montagem.</li>
              <li>Erros custam vidas.</li>
              <li>Complete 3 palavras para vencer.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Palavras</div>
                <div class="text-h4">{{{{ session.wins }}}}/3</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Clue</div>
                <div class="text-h4">{{{{ currentWord.answer.length }}}} letras</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card outlined class="pa-4 mb-4">
            <div class="text-overline mb-2">Dica</div>
            <div class="text-h6">{{{{ currentWord.clue }}}}</div>
          </v-card>

          <v-text-field
            v-model="guess"
            readonly
            outlined
            label="Sua palavra"
            class="mb-3"
          />

          <v-row dense class="mb-4">
            <v-col v-for="(letter, index) in shuffledLetters" :key="letter + index" cols="3" sm="2">
              <v-btn block large color="primary" :disabled="gameOver || roundLocked || usedIndices.includes(index)" @click="pickLetter(letter, index)">
                {{{{ letter }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center">
            <v-btn color="primary" class="mr-2" :disabled="gameOver || roundLocked || !guess" @click="submitGuess">
              Confirmar
            </v-btn>
            <v-btn text large class="mr-2" @click="resetWord">Limpar</v-btn>
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    maxLives: 3,
    currentWordIndex: 0,
    guess: '',
    usedIndices: [],
    roundLocked: false,
    message: 'Monte a palavra e confirme quando estiver pronto.',
    alertType: 'info',
    words: [
      {{ clue: 'Quem responde perguntas num jogo de conhecimento', answer: 'QUIZ', letters: ['I', 'Q', 'Z', 'U'] }},
      {{ clue: 'Algo escondido atras de uma porta com premio', answer: 'TESOURO', letters: ['O', 'T', 'R', 'E', 'S', 'U', 'O', 'R'] }},
      {{ clue: 'Lembrar a ordem correta de simbolos', answer: 'MEMORIA', letters: ['M', 'A', 'I', 'O', 'R', 'E', 'M', 'A'] }},
      {{ clue: 'Responder com uma entre varias opcoes', answer: 'ESCOLHA', letters: ['S', 'A', 'O', 'L', 'E', 'H', 'C', 'E'] }}
    ]
  }}),
  computed: {{
    currentWord () {{
      return this.words[this.currentWordIndex] || this.words[this.words.length - 1]
    }},
    shuffledLetters () {{
      return this.currentWord.letters
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= 3 || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    pickLetter (letter, index) {{
      if (this.gameOver || this.roundLocked) {{
        return
      }}
      this.startSessionRound('spelling')
      this.guess += letter
      this.usedIndices.push(index)
    }},
    submitGuess () {{
      if (this.gameOver || this.roundLocked || !this.guess) {{
        return
      }}
      this.roundLocked = true
      if (this.guess === this.currentWord.answer) {{
        this.registerWin(this.currentWord.answer.length * 10, 'won')
        this.message = `Boa. Palavra correta: ${{this.currentWord.answer}}.`
        this.alertType = 'success'
      }} else {{
        this.registerLoss('lost')
        this.message = `Errado. A resposta era ${{this.currentWord.answer}}.`
        this.alertType = 'error'
      }}
      window.setTimeout(() => {{
        if (!this.gameOver) {{
          this.currentWordIndex = (this.currentWordIndex + 1) % this.words.length
          this.resetWord()
          this.message = 'Nova palavra liberada.'
          this.alertType = 'info'
        }}
      }}, 900)
    }},
    resetWord () {{
      this.guess = ''
      this.usedIndices = []
      this.roundLocked = false
    }},
    resetGame () {{
      this.resetSession()
      this.currentWordIndex = 0
      this.resetWord()
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>
"""


def _build_platform_hub_component(request: GameGenerationRequest) -> str:
    vertical_variant = _is_vertical_platform_hub_idea(request)
    template = '''<template>
  <v-container fluid class="__COMP_KEY__ hub-shell py-6">
    <v-row justify="center">
      <v-col cols="12" xl="11">
        <v-card class="hub-surface overflow-hidden" elevation="8">
          <v-row no-gutters>
            <v-col cols="12">
              <div class="hub-stage pa-5 pa-md-6">
                <div class="d-flex flex-wrap align-center justify-space-between mb-5">
                  <div>
                    <div class="text-overline mb-2">Phaser task hub</div>
                    <h1 class="text-h4 mb-2">__GAME_NAME__</h1>
                    <p class="mb-0 stage-copy">
                      Um hub side-scroller em Phaser com casas, portas, chaves e moedas abrindo tasks reais.
                    </p>
                  </div>
                  <div class="stage-stats">
                    <div class="stage-stat">
                      <span class="stage-stat__label">Moedas</span>
                      <strong>{{ coins }}</strong>
                    </div>
                    <div class="stage-stat">
                      <span class="stage-stat__label">Chave</span>
                      <strong>{{ hasKey ? 'Sim' : 'Nao' }}</strong>
                    </div>
                  </div>
                </div>

                <v-alert v-if="message" dense text :type="alertType" class="mb-4">
                  {{ message }}
                </v-alert>

                <v-card class="world-card pa-3 pa-md-4 mb-4" outlined>
                  <div class="d-flex align-center justify-space-between mb-3">
                    <div>
                      <div class="text-caption">Cena ativa</div>
                      <div class="text-h5">{{ currentLevel.title }}</div>
                    </div>
                    <v-chip color="primary" outlined>{{ currentLevel.theme }}</v-chip>
                  </div>

                  <div ref="phaserHost" class="phaser-stage phaser-stage--bleed mb-4"></div>

                  <div class="stage-hud mb-4">
                    <div class="stage-hud__item">
                      <span>Porta em foco</span>
                      <strong>{{ currentDoor ? currentDoor.label : 'Nenhuma' }}</strong>
                    </div>
                    <div class="stage-hud__item">
                      <span>Item em foco</span>
                      <strong>{{ currentPickup ? currentPickup.label : 'Nenhum' }}</strong>
                    </div>
                    <div class="stage-hud__item">
                      <span>Task ativa</span>
                      <strong>{{ activeTask ? activeTask.title : 'Nenhuma' }}</strong>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap gap-12">
                    <v-btn color="primary" large @click="enterMap">
                      Entrar no mapa
                    </v-btn>
                    <v-btn outlined large @click="moveHero(-1)">
                      Andar esquerda
                    </v-btn>
                    <v-btn outlined large @click="jumpHero">
                      Pular
                    </v-btn>
                    <v-btn outlined large @click="moveHero(1)">
                      Andar direita
                    </v-btn>
                    <v-btn color="success" large :disabled="!currentDoor || !hasKey" @click="openFocusedDoor">
                      Abrir porta
                    </v-btn>
                    <v-btn text large color="amber darken-2" disabled>
                      Coleta automatica
                    </v-btn>
                    <v-btn text large @click="nextLevel">
                      Proxima fase
                    </v-btn>
                  </div>
                </v-card>

                <v-card outlined class="task-modal pa-0" v-if="activeTask">
                  <div class="task-modal__header pa-4 pa-md-5">
                    <div class="d-flex align-center justify-space-between">
                      <div>
                        <div class="text-overline mb-1">Transmissao da task</div>
                        <div class="text-h5">{{ activeTask.title }}</div>
                      </div>
                      <v-btn icon class="task-modal__close" @click="closeTask">
                        <v-icon>mdi-close</v-icon>
                      </v-btn>
                    </div>
                    <div class="task-modal__speaker mt-3">
                      <div class="task-modal__avatar">
                        <v-icon color="white" size="18">mdi-message-badge-outline</v-icon>
                      </div>
                      <div class="task-modal__bubble">
                        {{ activeTask.description }}
                      </div>
                    </div>
                  </div>
                  <v-row dense class="px-4 px-md-5 mb-4">
                    <v-col cols="12" sm="6" v-for="goal in activeTask.goals" :key="goal">
                      <v-sheet rounded class="task-goal pa-3">
                        {{ goal }}
                      </v-sheet>
                    </v-col>
                  </v-row>
                  <div class="d-flex flex-wrap gap-12 px-4 px-md-5 pb-4 pb-md-5">
                    <v-btn color="success" large @click="completeTask">
                      Concluir task
                    </v-btn>
                    <v-btn color="error" outlined large @click="failTask">
                      Falhar rodada
                    </v-btn>
                    <v-btn text large @click="closeTask">
                      Voltar ao hub
                    </v-btn>
                  </div>
                </v-card>
              </div>
            </v-col>

            <v-col cols="12">
              <div class="hub-sidebar pa-5 pa-md-6">
                <v-card outlined class="pa-4 mb-4 sidebar-card">
                  <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
                  <ul class="mb-0">
                    <li>Ande pelo mapa como no Platform original.</li>
                    <li>Colete moedas e pegue a chave da fase.</li>
                    <li>Fique sobre a porta certa e abra a task.</li>
                    <li>Conclua as {{ tasks.length }} tasks antes de atingir 3 perdas.</li>
                  </ul>
                </v-card>

                <v-card outlined class="pa-4 mb-4 sidebar-card">
                  <div class="text-subtitle-1 font-weight-bold mb-2">Objetivo</div>
                  <p class="mb-2">Atravesse as fases, abra as portas e conclua as {{ tasks.length }} tasks do hub.</p>
                  <div class="text-caption">Fase atual</div>
                  <div class="text-h6">{{ currentLevel.title }}</div>
                  <div class="text-caption mt-3">Session score</div>
                  <div class="text-h6">{{ session.score }}</div>
                </v-card>

                <v-card outlined class="pa-4 mb-4 sidebar-card">
                  <div class="text-subtitle-1 font-weight-bold mb-2">Leitura do mapa</div>
                  <ul class="mb-0">
                    <li>O level nasce de templates estaveis no estilo hero, platforms, doors e pickups.</li>
                    <li>As tasks reais do evento preenchem os slots das portas.</li>
                    <li>O modal abre por cima do mapa, sem desmontar o palco Phaser.</li>
                  </ul>
                </v-card>

                <v-card outlined class="pa-4 mb-4 sidebar-card">
                  <div class="text-caption">Progresso geral</div>
                  <div class="text-h5 mb-2">{{ completedTasks.length }}/{{ tasks.length }} tasks</div>
                  <v-progress-linear :value="completionValue" color="success" height="10" rounded />
                </v-card>

                <game-stats-bar :session="session" class="mb-4" />

                <v-card outlined class="pa-4 sidebar-card">
                  <div class="text-subtitle-1 font-weight-bold mb-3">Timeline das portas</div>
                  <v-timeline dense align-top>
                    <v-timeline-item
                      v-for="entry in taskTimeline"
                      :key="entry.id"
                      small
                      :color="entry.status === 'completed' ? 'success' : entry.status === 'active' ? 'primary' : 'grey'"
                    >
                      <div class="font-weight-bold">{{ entry.title }}</div>
                      <div class="text-caption">{{ entry.statusLabel }}</div>
                      <div class="text-body-2">{{ entry.summary }}</div>
                    </v-timeline-item>
                  </v-timeline>
                </v-card>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { db } from '../main'
import GameSessionMixin from './mixins/GameSessionMixin'

const FALLBACK_TASKS = [
  {
    id: 'task-1',
    title: 'Task de onboarding',
    description: 'Primeira task liberada pela rua principal.',
    goals: ['Entrar na primeira porta', 'Ler o briefing', 'Fechar a etapa'],
    completed: false,
    summary: 'Casa inicial do hub',
    component: 'welcome'
  },
  {
    id: 'task-2',
    title: 'Task de decisao rapida',
    description: 'Uma task curta com resposta imediata.',
    goals: ['Abrir a segunda casa', 'Concluir sem perder ritmo'],
    completed: false,
    summary: 'Porta lateral',
    component: 'vote'
  },
  {
    id: 'task-3',
    title: 'Task de puzzle',
    description: 'Uma fase de leitura e resolucao visual.',
    goals: ['Subir a colina', 'Entrar na porta elevada'],
    completed: false,
    summary: 'Casa alta',
    component: 'crosswords'
  },
  {
    id: 'task-4',
    title: 'Task final',
    description: 'Fechamento da jornada com mais pressao.',
    goals: ['Abrir a ultima porta', 'Fechar a rodada final'],
    completed: false,
    summary: 'Casa final',
    component: 'streetview'
  }
]

const GROUND_Y = 546
const HERO_Y = 525
const ELEVATED_PLATFORM_Y = 378
const MID_PLATFORM_Y = 336
const HIGH_PLATFORM_Y = 252
const ELEVATED_DOOR_Y = 378
const GROUND_DOOR_Y = 546
const TREE_Y = 546
const POLE_Y = 546
const BASE_GAME_WIDTH = 960
const BASE_GAME_HEIGHT = 600
const WORLD_SCALE = 1.2
const GAME_WIDTH = Math.round(BASE_GAME_WIDTH * WORLD_SCALE)
const GAME_HEIGHT = Math.round(BASE_GAME_HEIGHT * WORLD_SCALE)

const buildLevels = () => ([
  {
    id: 'level-0',
    title: 'Rua das portas',
    theme: 'Entrada principal',
    hero: { x: 21, y: HERO_Y },
    platforms: [
      { image: 'ground', x: 0, y: GROUND_Y, visible: true },
      { image: 'grass:4x1', x: 300, y: HIGH_PLATFORM_Y, visible: true },
      { image: 'grass:2x1', x: 520, y: MID_PLATFORM_Y, visible: true }
    ],
    doors: [
      { id: 'task-1', label: 'Porta 01', x: 180, y: GROUND_DOOR_Y, route: 'task-1', house: 'house1' },
      { id: 'task-2', label: 'Porta 02', x: 430, y: GROUND_DOOR_Y, route: 'task-2', house: 'house2' }
    ],
    pickups: [
      { id: 'coin-1', kind: 'coin', label: 'Moeda baixa', x: 320, y: 483 },
      { id: 'coin-2', kind: 'coin', label: 'Moeda alta', x: 560, y: 294 },
      { id: 'key-1', kind: 'key', label: 'Chave da rua', x: 680, y: 504 }
    ],
    trees: [
      { x: 100, y: TREE_Y },
      { x: 760, y: TREE_Y }
    ],
    poles: [
      { x: 30, y: POLE_Y }
    ]
  },
  {
    id: 'level-1',
    title: 'Colina das tasks',
    theme: 'Camada alta',
    hero: { x: 21, y: HERO_Y },
    platforms: [
      { image: 'ground', x: 0, y: GROUND_Y, visible: true },
      { image: 'grass:6x1', x: 260, y: ELEVATED_PLATFORM_Y, visible: true },
      { image: 'grass:4x1', x: 610, y: HIGH_PLATFORM_Y, visible: true }
    ],
    doors: [
      { id: 'task-3', label: 'Porta 03', x: 350, y: ELEVATED_DOOR_Y, route: 'task-3', house: 'house4' },
      { id: 'task-4', label: 'Porta 04', x: 720, y: GROUND_DOOR_Y, route: 'task-4', house: 'house5' }
    ],
    pickups: [
      { id: 'coin-3', kind: 'coin', label: 'Moeda do morro', x: 310, y: 336 },
      { id: 'coin-4', kind: 'coin', label: 'Moeda final', x: 670, y: 210 },
      { id: 'key-2', kind: 'key', label: 'Chave da colina', x: 790, y: 504 }
    ],
    trees: [
      { x: 170, y: TREE_Y },
      { x: 845, y: TREE_Y }
    ],
    poles: [
      { x: 520, y: POLE_Y }
    ]
  },
  {
    id: 'level-2',
    title: 'Bairro final',
    theme: 'Fechamento da jornada',
    hero: { x: 21, y: HERO_Y },
    platforms: [
      { image: 'ground', x: 0, y: GROUND_Y, visible: true },
      { image: 'grass:2x1', x: 220, y: 420, visible: true },
      { image: 'grass:4x1', x: 430, y: 370, visible: true },
      { image: 'grass:6x1', x: 690, y: HIGH_PLATFORM_Y, visible: true }
    ],
    doors: [
      { id: 'task-5', label: 'Porta 05', x: 500, y: 420, route: 'task-5', house: 'house1' },
      { id: 'task-6', label: 'Porta 06', x: 860, y: GROUND_DOOR_Y, route: 'task-6', house: 'house2' }
    ],
    pickups: [
      { id: 'coin-5', kind: 'coin', label: 'Moeda da escadaria', x: 250, y: 378 },
      { id: 'coin-6', kind: 'coin', label: 'Moeda do bairro final', x: 760, y: 210 },
      { id: 'key-3', kind: 'key', label: 'Chave do bairro final', x: 900, y: 504 }
    ],
    trees: [
      { x: 120, y: TREE_Y },
      { x: 620, y: TREE_Y }
    ],
    poles: [
      { x: 360, y: POLE_Y },
      { x: 980, y: POLE_Y }
    ]
  }
])

export default {
  name: '__GAME_NAME__',
  components: {
    GameStatsBar: () => import('./GameStatsBar')
  },
  mixins: [GameSessionMixin],
  data: () => ({
    levels: buildLevels(),
    levelIndex: 0,
    tasks: FALLBACK_TASKS,
    phaserGame: null,
    sceneState: null,
    eventRefUnsubscribe: null,
    eventLoadTimer: null,
    hasInitializedFromEvent: false,
    activeTaskId: null,
    currentDoorId: null,
    currentPickupId: null,
    collectedPickupIds: [],
    autoOpenedDoorId: null,
    levelTransitionLocked: false,
    hasKey: false,
    coins: 0,
    moveIntent: 0,
    jumpIntent: false,
    maxLives: 3,
    message: 'Mapa carregado. Use Phaser para chegar ate a porta certa.',
    alertType: 'info'
  }),
  computed: {
    currentLevel () {
      return this.levels[this.levelIndex]
    },
    activeTask () {
      return this.tasks.find((task) => task.id === this.activeTaskId) || null
    },
    currentDoor () {
      return this.currentLevel.doors.find((door) => door.id === this.currentDoorId) || null
    },
    currentPickup () {
      return this.currentLevel.pickups.find((pickup) => pickup.id === this.currentPickupId && !this.collectedPickupIds.includes(pickup.id)) || null
    },
    completedTasks () {
      return this.tasks.filter((task) => task.completed)
    },
    completionValue () {
      return this.tasks.length ? (this.completedTasks.length / this.tasks.length) * 100 : 0
    },
    gameOver () {
      return this.session.losses >= this.maxLives || this.completedTasks.length === this.tasks.length
    },
    taskTimeline () {
      return this.tasks.map((task) => {
        let status = 'locked'
        let statusLabel = 'Pendente'
        if (task.completed) {
          status = 'completed'
          statusLabel = 'Concluida'
        } else if (task.id === this.activeTaskId) {
          status = 'active'
          statusLabel = 'Ativa'
        } else if (this.currentLevel.doors.some((door) => door.id === task.id)) {
          status = 'open'
          statusLabel = 'Na fase atual'
        }
        return {
          id: task.id,
          title: task.title,
          status,
          statusLabel,
          summary: task.summary
        }
      })
    }
  },
  mounted () {
    this.bindEventTasks()
    if (!this.$route.params.id || !this.$route.params.user) {
      this.initPhaser()
    }
  },
  beforeDestroy () {
    if (this.eventLoadTimer) {
      window.clearTimeout(this.eventLoadTimer)
      this.eventLoadTimer = null
    }
    if (this.eventRefUnsubscribe) {
      this.eventRefUnsubscribe()
      this.eventRefUnsubscribe = null
    }
    this.destroyPhaser()
  },
  methods: {
    bindEventTasks () {
      if (!this.$route.params.id || !this.$route.params.user) return
      this.eventLoadTimer = window.setTimeout(() => {
        if (!this.hasInitializedFromEvent && !this.phaserGame) {
          this.message = 'Evento ainda nao respondeu. Carregando mapa base temporariamente.'
          this.alertType = 'info'
          this.initPhaser()
        }
      }, 1500)
      this.eventRefUnsubscribe = db.collection(`users/${this.$route.params.user}/e`).doc(this.$route.params.id)
        .onSnapshot((snapshot) => {
          const data = snapshot.data() || {}
          const sourceTasks = Array.isArray(data.tasks)
            ? data.tasks
            : Object.values(data.myTasks || {})
          const normalized = this.normalizeEventTasks(sourceTasks)
          if (normalized.length === 0) {
            if (!this.phaserGame) {
              this.message = 'Evento sem tasks disponiveis. Exibindo mapa base.'
              this.alertType = 'info'
              this.initPhaser()
            }
            return
          }
          this.hasInitializedFromEvent = true
          if (this.eventLoadTimer) {
            window.clearTimeout(this.eventLoadTimer)
            this.eventLoadTimer = null
          }
          this.tasks = normalized
          this.levels = this.buildLevelsFromTasks(normalized)
          this.levelIndex = 0
          this.currentDoorId = null
          this.currentPickupId = null
          this.autoOpenedDoorId = null
          this.collectedPickupIds = []
          this.hasKey = false
          this.activeTaskId = null
          this.message = `Mapa do evento carregado com ${normalized.length} tasks.`
          this.alertType = 'info'
          this.$nextTick(() => {
            this.initPhaser()
          })
        })
    },
    normalizeEventTasks (sourceTasks) {
      return sourceTasks.map((task, index) => {
        const taskId = String(task.id != null ? task.id : index + 1)
        const component = task.component || 'custom-task'
        const title = task.name || task.title || component || `Task ${index + 1}`
        const description = task.text || task.question || task.objective || `Task do evento usando o componente ${component}.`
        return {
          id: taskId,
          title,
          description,
          goals: [
            `Abrir o predio da task ${index + 1}`,
            component ? `Executar ${component}` : 'Executar a task',
            'Pontuar na rodada'
          ],
          completed: false,
          summary: component,
          component,
          rawTask: task
        }
      })
    },
    buildLevelsFromTasks (tasks) {
      const safeTasks = tasks.length ? tasks : FALLBACK_TASKS
      const templates = buildLevels()
      let taskIndex = 0
      const levels = []
      let sectorIndex = 0

      while (taskIndex < safeTasks.length) {
        const template = JSON.parse(JSON.stringify(templates[sectorIndex % templates.length]))
        const slotCount = template.doors.length
        const sectorTasks = safeTasks.slice(taskIndex, taskIndex + slotCount)
        taskIndex += slotCount

        const levelNumber = levels.length + 1
        template.id = `event-level-${sectorIndex}`
        template.title = `${template.title} ${levelNumber}`
        template.theme = `${sectorTasks.length} tasks do evento`

        template.doors = template.doors
          .slice(0, sectorTasks.length)
          .map((door, index) => {
            const task = sectorTasks[index]
            return {
              ...door,
              y: GROUND_DOOR_Y,
              id: task.id,
              label: task.title,
              route: task.id
            }
          })

        template.pickups = template.pickups.map((pickup, pickupIndex) => {
          if (pickup.kind === 'key') {
            const relatedDoor = template.doors[Math.min(pickupIndex, Math.max(template.doors.length - 1, 0))]
            return {
              ...pickup,
              id: relatedDoor ? `key-${relatedDoor.id}` : `key-${sectorIndex}-${pickupIndex}`,
              label: relatedDoor ? `Chave de ${relatedDoor.label}` : pickup.label
            }
          }

          return {
            ...pickup,
            id: `coin-${sectorIndex}-${pickupIndex}`,
            label: `Moeda do setor ${levelNumber}`
          }
        })

        levels.push(template)
        sectorIndex += 1
      }

      return levels
    },
    cloneLevel () {
      return JSON.parse(JSON.stringify(this.currentLevel))
    },
    scaleValue (value) {
      return Math.round(value * WORLD_SCALE)
    },
    enterMap () {
      this.startSessionRound('platform-hub')
      if (!this.phaserGame) {
        this.initPhaser()
      }
      this.message = `Mapa aberto: ${this.currentLevel.title}. Pegue a chave e abra uma porta.`
      this.alertType = 'info'
    },
    initPhaser () {
      const PhaserProxy = this.Phaser || window.Phaser
      if (!PhaserProxy) {
        this.message = 'Phaser nao esta disponivel na pagina.'
        this.alertType = 'error'
        return
      }

      this.destroyPhaser()

      const host = this.$refs.phaserHost
      if (!host) return
      host.innerHTML = ''

      const vm = this
      const levelData = this.cloneLevel()

      const state = {
        preload () {
          this.load.image('background0', '/images/background0.png')
          this.load.image('ground', '/images/ground.png')
          this.load.image('tree', '/images/tree.png')
          this.load.image('grass:6x1', '/images/grass_6x1.png')
          this.load.image('grass:4x1', '/images/grass_4x1.png')
          this.load.image('grass:2x1', '/images/grass_2x1.png')
          this.load.spritesheet('coin', '/images/coin_animated.png', 22, 22)
          this.load.spritesheet('door', '/images/door.png', 42, 66)
          this.load.image('key', '/images/key.png')
          this.load.image('pole', '/images/pole.png')
          this.load.image('hero', '/images/hero_stopped.png')
          this.load.image('house1', '/images/house1.png')
          this.load.image('house2', '/images/house2.png')
          this.load.image('house4', '/images/house4.png')
          this.load.image('house5', '/images/house5.png')
          this.load.audio('sfx:jump', '/audio/jump.wav')
          this.load.audio('sfx:coin', '/audio/coin.wav')
          this.load.audio('sfx:door', '/audio/door.wav')
        },
        create () {
          const worldWidth = vm.scaleValue(levelData.worldWidth || 1180)
          this.game.world.setBounds(0, 0, worldWidth, GAME_HEIGHT)
          const backgroundCopies = Math.max(1, Math.ceil(worldWidth / GAME_WIDTH))
          for (let index = 0; index < backgroundCopies; index += 1) {
            const background = this.game.add.image(index * GAME_WIDTH, 0, 'background0')
            background.scale.setTo(WORLD_SCALE, WORLD_SCALE)
          }
          this.game.physics.startSystem(PhaserProxy.Physics.ARCADE)
          this.game.physics.arcade.gravity.y = 1100

          this.platforms = this.game.add.group()
          this.coins = this.game.add.group()
          this.doorKeys = this.game.add.group()
          this.doors = this.game.add.group()
          this.houses = this.game.add.group()
          this.bgDecoration = this.game.add.group()

          levelData.platforms.forEach((platform) => {
            const sprite = this.platforms.create(vm.scaleValue(platform.x), vm.scaleValue(platform.y), platform.image)
            sprite.scale.setTo(WORLD_SCALE, WORLD_SCALE)
            sprite.visible = platform.visible
            this.game.physics.enable(sprite)
            sprite.body.allowGravity = false
            sprite.body.immovable = true
          })

          levelData.trees.forEach((tree) => {
            const sprite = this.bgDecoration.create(vm.scaleValue(tree.x), vm.scaleValue(tree.y), 'tree')
            sprite.anchor.setTo(0.5, 1)
            sprite.scale.setTo(WORLD_SCALE, WORLD_SCALE)
            this.game.physics.enable(sprite)
            sprite.body.allowGravity = false
          })

          levelData.poles.forEach((pole) => {
            const sprite = this.bgDecoration.create(vm.scaleValue(pole.x), vm.scaleValue(pole.y), 'pole')
            sprite.anchor.setTo(0.5, 1)
            sprite.scale.setTo(WORLD_SCALE, WORLD_SCALE)
            this.game.physics.enable(sprite)
            sprite.body.allowGravity = false
          })

          levelData.doors.forEach((door) => {
            const house = this.houses.create(vm.scaleValue(door.x), vm.scaleValue(door.y), door.house)
            house.anchor.setTo(0.5, 1)
            house.scale.setTo(WORLD_SCALE, WORLD_SCALE)
            this.game.physics.enable(house)
            house.body.allowGravity = false

            const sprite = this.doors.create(vm.scaleValue(door.x), vm.scaleValue(door.y), 'door')
            sprite.anchor.setTo(0.5, 1)
            sprite.scale.setTo(WORLD_SCALE, WORLD_SCALE)
            sprite.taskId = door.id
            sprite.doorLabel = door.label
            this.game.physics.enable(sprite)
            sprite.body.allowGravity = false
          })

          levelData.pickups.filter((pickup) => !vm.collectedPickupIds.includes(pickup.id)).forEach((pickup) => {
            if (pickup.kind === 'coin') {
              const sprite = this.coins.create(vm.scaleValue(pickup.x), vm.scaleValue(pickup.y), 'coin')
              sprite.pickupId = pickup.id
              sprite.pickupLabel = pickup.label
              sprite.scale.setTo(WORLD_SCALE, WORLD_SCALE)
              this.game.physics.enable(sprite)
              sprite.body.allowGravity = false
              sprite.anchor.set(0.5, 0.5)
              sprite.animations.add('rotate', [0, 1, 2, 1], 6, true)
              sprite.animations.play('rotate')
            } else {
              const key = this.doorKeys.create(vm.scaleValue(pickup.x), vm.scaleValue(pickup.y), 'key')
              key.pickupId = pickup.id
              key.pickupLabel = pickup.label
              key.scale.setTo(WORLD_SCALE, WORLD_SCALE)
              this.game.physics.enable(key)
              key.body.allowGravity = false
              key.anchor.set(0.5, 0.5)
              key.y -= 3
              this.game.add.tween(key)
                .to({ y: key.y + 6 }, 800, PhaserProxy.Easing.Sinusoidal.InOut)
                .yoyo(true)
                .loop()
                .start()
            }
          })

          this.hero = this.game.add.sprite(vm.scaleValue(levelData.hero.x), vm.scaleValue(levelData.hero.y), 'hero')
          this.hero.scale.setTo(WORLD_SCALE, WORLD_SCALE)
          this.game.physics.enable(this.hero)
          this.hero.anchor.set(0.5, 0.5)
          this.hero.body.collideWorldBounds = true
          this.game.camera.follow(this.hero)

          this.sfx = {
            jump: this.game.add.audio('sfx:jump'),
            coin: this.game.add.audio('sfx:coin'),
            door: this.game.add.audio('sfx:door')
          }

          this.keys = this.game.input.keyboard.addKeys({
            left: PhaserProxy.KeyCode.LEFT,
            right: PhaserProxy.KeyCode.RIGHT,
            up: PhaserProxy.KeyCode.UP
          })

          vm.sceneState = this
        },
        update () {
          vm.currentDoorId = null
          vm.currentPickupId = null

          this.game.physics.arcade.collide(this.hero, this.platforms)

          this.game.physics.arcade.overlap(this.hero, this.coins, (hero, coin) => {
            vm.currentPickupId = coin.pickupId
            if (!vm.collectedPickupIds.includes(coin.pickupId)) {
              vm.collectedPickupIds.push(coin.pickupId)
              vm.coins += 1
              vm.message = `Moeda coletada: ${coin.pickupLabel}.`
              vm.alertType = 'success'
              if (this.sfx.coin) {
                this.sfx.coin.play()
              }
            }
            coin.kill()
          })

          this.game.physics.arcade.overlap(this.hero, this.doorKeys, (hero, key) => {
            vm.currentPickupId = key.pickupId
            if (!vm.hasKey) {
              vm.hasKey = true
              if (!vm.collectedPickupIds.includes(key.pickupId)) {
                vm.collectedPickupIds.push(key.pickupId)
              }
              key.kill()
              vm.message = 'Chave coletada. Agora voce pode abrir uma porta.'
              vm.alertType = 'success'
              if (this.doors && this.doors.children) {
                this.doors.children.forEach((doorSprite) => {
                  doorSprite.frame = 1
                })
              }
            }
          })

          this.game.physics.arcade.overlap(this.hero, this.doors, (hero, door) => {
            vm.currentDoorId = door.taskId
            if (vm.hasKey && vm.autoOpenedDoorId !== door.taskId && !vm.activeTaskId) {
              vm.autoOpenedDoorId = door.taskId
              vm.openFocusedDoor()
            }
          })

          const leftDown = this.keys.left.isDown || vm.moveIntent < 0
          const rightDown = this.keys.right.isDown || vm.moveIntent > 0

          if (leftDown) {
            this.hero.body.velocity.x = -220
          } else if (rightDown) {
            this.hero.body.velocity.x = 220
          } else {
            this.hero.body.velocity.x = 0
          }

          if ((this.keys.up.justDown || vm.jumpIntent) && this.hero.body.touching.down) {
            this.hero.body.velocity.y = -520
            vm.jumpIntent = false
            if (this.sfx.jump) {
              this.sfx.jump.play()
            }
          } else if (vm.jumpIntent) {
            vm.jumpIntent = false
          }

          const endThreshold = this.game.world.bounds.width - vm.scaleValue(96)
          const readyToAdvance = this.hero.x >= endThreshold && rightDown && !vm.activeTaskId

          if (readyToAdvance && !vm.levelTransitionLocked) {
            vm.levelTransitionLocked = true
            vm.nextLevel()
          } else if (this.hero.x < endThreshold - vm.scaleValue(48)) {
            vm.levelTransitionLocked = false
          }
        }
      }

      this.phaserGame = new PhaserProxy.Game(GAME_WIDTH, GAME_HEIGHT, PhaserProxy.CANVAS, host, state)
    },
    destroyPhaser () {
      if (this.phaserGame) {
        this.phaserGame.destroy(true)
        this.phaserGame = null
      }
      this.sceneState = null
    },
    moveHero (direction) {
      this.moveIntent = direction
      window.setTimeout(() => {
        if (this.moveIntent === direction) {
          this.moveIntent = 0
        }
      }, 220)
    },
    jumpHero () {
      this.jumpIntent = true
    },
    openTask (taskId) {
      this.activeTaskId = taskId
      const task = this.tasks.find((entry) => entry.id === taskId)
      if (task) {
        this.message = `Porta aberta: ${task.title}.`
        this.alertType = 'info'
      }
    },
    openFocusedDoor () {
      if (!this.currentDoor || !this.hasKey) return
      this.startSessionRound('platform-hub-door')
      this.hasKey = false
      this.currentPickupId = null
      if (this.sceneState && this.sceneState.sfx && this.sceneState.sfx.door) {
        this.sceneState.sfx.door.play()
      }
      if (this.sceneState && this.sceneState.doors && this.sceneState.doors.children) {
        this.sceneState.doors.children.forEach((doorSprite) => {
          doorSprite.frame = 0
        })
      }
      this.openTask(this.currentDoor.id)
    },
    closeTask () {
      this.activeTaskId = null
      this.message = 'Voce voltou para o mapa principal.'
      this.alertType = 'info'
    },
    completeTask () {
      if (!this.activeTask) return
      this.startSessionRound('platform-hub-task')
      this.tasks = this.tasks.map((task) => task.id === this.activeTaskId ? { ...task, completed: true } : task)
      this.registerWin(25, 'won')
      this.message = `Task concluida: ${this.activeTask.title}.`
      this.alertType = 'success'
      this.activeTaskId = null
    },
    failTask () {
      this.startSessionRound('platform-hub-risk')
      this.registerLoss('lost')
      this.message = this.gameOver
        ? 'Fim do hub. O limite de perdas foi atingido.'
        : 'Falha registrada. Tente outra porta ou avance para a proxima fase.'
      this.alertType = 'error'
      this.activeTaskId = null
    },
    nextLevel () {
      const nextIndex = (this.levelIndex + 1) % this.levels.length
      const loopedToStart = nextIndex === 0
      this.levelIndex = nextIndex
      this.hasKey = false
      this.currentDoorId = null
      this.currentPickupId = null
      this.autoOpenedDoorId = null
      this.levelTransitionLocked = false
      this.message = loopedToStart
        ? 'Voltando ao inicio do hub.'
        : `Fase trocada para ${this.currentLevel.title}.`
      this.alertType = 'info'
      this.$nextTick(() => {
        this.initPhaser()
      })
    }
  }
}
</script>

<style scoped>
.hub-surface {
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.14), transparent 24%),
    linear-gradient(135deg, #0f172a 0%, #111827 55%, #1f2937 100%);
  color: #e5eefb;
}

.hub-stage {
  position: relative;
  min-height: 760px;
}

.stage-copy {
  max-width: 560px;
  color: rgba(226, 232, 240, 0.84);
}

.stage-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stage-stat {
  min-width: 112px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.stage-stat__label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(191, 219, 254, 0.8);
}

.world-card,
.sidebar-card,
.task-modal {
  background: rgba(15, 23, 42, 0.58) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
  color: #f8fafc;
}

.task-modal {
  position: absolute;
  top: 148px;
  left: 32px;
  right: 32px;
  z-index: 12;
  overflow: hidden;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.82)) !important;
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.34);
}

.task-modal__header {
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.58), rgba(15, 23, 42, 0.1));
}

.task-modal__close {
  background: rgba(15, 23, 42, 0.42);
}

.task-modal__speaker {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 12px;
  align-items: start;
}

.task-modal__avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2563eb, #0f766e);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.28);
}

.task-modal__bubble {
  position: relative;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(30, 41, 59, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.14);
  color: #e2e8f0;
  line-height: 1.55;
}

.task-modal__bubble::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 14px;
  width: 16px;
  height: 16px;
  transform: rotate(45deg);
  background: rgba(30, 41, 59, 0.78);
  border-left: 1px solid rgba(148, 163, 184, 0.14);
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

@media (max-width: 960px) {
  .task-modal {
    top: 132px;
    left: 12px;
    right: 12px;
  }
}

.phaser-stage {
  width: 100%;
  min-height: 720px;
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: linear-gradient(180deg, #10203a 0%, #13263f 38%, #0f172a 100%);
  margin: 0 auto;
}

.phaser-stage::v-deep canvas {
  width: 100% !important;
  height: 100% !important;
  max-width: none;
  display: block;
  image-rendering: auto;
}

.phaser-stage--bleed {
  margin-left: -16px;
  margin-right: -16px;
  width: calc(100% + 32px);
  border-left: 0;
  border-right: 0;
  border-radius: 0;
}

@media (min-width: 960px) {
  .phaser-stage--bleed {
    margin-left: -24px;
    margin-right: -24px;
    width: calc(100% + 48px);
  }
}

.stage-hud {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.stage-hud__item {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(2, 6, 23, 0.46);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.stage-hud__item span {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(191, 219, 254, 0.78);
  margin-bottom: 4px;
}

.hub-sidebar {
  min-height: 100%;
  background: rgba(2, 6, 23, 0.42);
}

.task-goal {
  background: rgba(30, 41, 59, 0.72);
  color: #e2e8f0;
}

.gap-12 {
  gap: 12px;
}
</style>
'''
    if vertical_variant:
        template = template.replace(
            "Um hub side-scroller em Phaser com casas, portas, chaves e moedas abrindo tasks reais.",
            "Um hub vertical em Phaser com blocos alcancaveis, ledges e predios em alguns patamares abrindo tasks reais."
        ).replace(
            "Ande pelo mapa como no Platform original.",
            "Suba pelos blocos e patamares como numa torre de tasks."
        ).replace(
            "Rua das portas",
            "Base da torre"
        ).replace(
            "Colina das tasks",
            "Meio da torre"
        ).replace(
            "Bairro final",
            "Topo da torre"
        ).replace(
            "{ image: 'grass:4x1', x: 300, y: HIGH_PLATFORM_Y, visible: true },\n      { image: 'grass:2x1', x: 520, y: MID_PLATFORM_Y, visible: true }",
            "{ image: 'grass:2x1', x: 180, y: 462, visible: true },\n      { image: 'grass:2x1', x: 340, y: 378, visible: true },\n      { image: 'grass:4x1', x: 520, y: 294, visible: true }"
        ).replace(
            "{ id: 'task-2', label: 'Porta 02', x: 430, y: GROUND_DOOR_Y, route: 'task-2', house: 'house2' }",
            "{ id: 'task-2', label: 'Porta 02', x: 560, y: 294, route: 'task-2', house: 'house2' }"
        ).replace(
            "{ image: 'grass:6x1', x: 260, y: ELEVATED_PLATFORM_Y, visible: true },\n      { image: 'grass:4x1', x: 610, y: HIGH_PLATFORM_Y, visible: true }",
            "{ image: 'grass:2x1', x: 160, y: 462, visible: true },\n      { image: 'grass:2x1', x: 300, y: 378, visible: true },\n      { image: 'grass:2x1', x: 460, y: 294, visible: true },\n      { image: 'grass:4x1', x: 640, y: 210, visible: true }"
        ).replace(
            "{ id: 'task-3', label: 'Porta 03', x: 350, y: ELEVATED_DOOR_Y, route: 'task-3', house: 'house4' },\n      { id: 'task-4', label: 'Porta 04', x: 720, y: GROUND_DOOR_Y, route: 'task-4', house: 'house5' }",
            "{ id: 'task-3', label: 'Porta 03', x: 340, y: 378, route: 'task-3', house: 'house4' },\n      { id: 'task-4', label: 'Porta 04', x: 700, y: 210, route: 'task-4', house: 'house5' }"
        ).replace(
            "{ image: 'grass:2x1', x: 220, y: 420, visible: true },\n      { image: 'grass:4x1', x: 430, y: 370, visible: true },\n      { image: 'grass:6x1', x: 690, y: HIGH_PLATFORM_Y, visible: true }",
            "{ image: 'grass:2x1', x: 180, y: 462, visible: true },\n      { image: 'grass:2x1', x: 330, y: 378, visible: true },\n      { image: 'grass:2x1', x: 490, y: 294, visible: true },\n      { image: 'grass:4x1', x: 690, y: 210, visible: true }"
        ).replace(
            "{ id: 'task-5', label: 'Porta 05', x: 500, y: 420, route: 'task-5', house: 'house1' },\n      { id: 'task-6', label: 'Porta 06', x: 860, y: GROUND_DOOR_Y, route: 'task-6', house: 'house2' }",
            "{ id: 'task-5', label: 'Porta 05', x: 520, y: 294, route: 'task-5', house: 'house1' },\n      { id: 'task-6', label: 'Porta 06', x: 760, y: 210, route: 'task-6', house: 'house2' }"
        )
    return template.replace("__COMP_KEY__", request.component_key).replace("__GAME_NAME__", request.game_name)
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6 pa-md-8 game-surface" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Descubra a palavra pela dica antes de esgotar as tentativas.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Leia a dica e monte a palavra correta.</li>
              <li>Toque nas letras sugeridas na ordem certa.</li>
              <li>Complete a palavra para vencer a rodada.</li>
              <li>Erros gastam tentativas.</li>
              <li>Feche 3 palavras antes de perder 3 tentativas totais.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Palavra</div>
                <div class="text-h4">{{{{ currentWordIndex + 1 }}}}/{{{{ words.length }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Objetivo</div>
                <div class="text-h4">{{{{ targetWins }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Tentativas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-card outlined class="pa-4 mb-4">
            <div class="text-overline mb-2">Dica</div>
            <div class="text-h6">{{{{ currentWord.clue }}}}</div>
          </v-card>

          <div class="letter-slots mb-4">
            <div
              v-for="(letter, index) in currentWord.answer.split('')"
              :key="index"
              class="letter-slot"
            >
              {{{{ guess[index] || '_' }}}}
            </div>
          </div>

          <v-row dense class="mb-4">
            <v-col
              v-for="(letter, index) in currentWord.letters"
              :key="letter + index"
              cols="3"
              sm="2"
            >
              <v-btn
                block
                large
                :disabled="gameOver || roundLocked || usedIndices.includes(index)"
                color="primary"
                @click="pickLetter(letter, index)"
              >
                {{{{ letter }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center">
            <v-btn text large @click="resetWord">
              Limpar palavra
            </v-btn>
            <v-btn text large @click="resetGame">
              Reiniciar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    targetWins: 3,
    maxLives: 3,
    currentWordIndex: 0,
    guess: '',
    usedIndices: [],
    roundLocked: false,
    message: 'Monte a palavra usando a dica.',
    alertType: 'info',
    words: [
      {{ clue: 'Jogo de perguntas com opcoes', answer: 'QUIZ', letters: ['Q', 'U', 'I', 'Z', 'A', 'O'] }},
      {{ clue: 'Escolha entre varias respostas', answer: 'OPCAO', letters: ['O', 'P', 'C', 'A', 'O', 'S'] }},
      {{ clue: 'Desafio de memoria em ordem', answer: 'SEQUENCIA', letters: ['S', 'E', 'Q', 'U', 'E', 'N', 'C', 'I', 'A', 'R'] }},
      {{ clue: 'Jogo de porta com premio escondido', answer: 'TESOURO', letters: ['T', 'E', 'S', 'O', 'U', 'R', 'O', 'L'] }}
    ]
  }}),
  computed: {{
    currentWord () {{
      return this.words[this.currentWordIndex] || this.words[this.words.length - 1]
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.wins >= this.targetWins || this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    pickLetter (letter, index) {{
      if (this.gameOver || this.roundLocked) {{
        return
      }}
      this.startSessionRound('spelling')
      this.guess += letter
      this.usedIndices.push(index)
      const expected = this.currentWord.answer.slice(0, this.guess.length)
      if (this.guess !== expected) {{
        this.registerLoss('lost')
        this.roundLocked = true
        this.message = `Letra errada. A palavra correta era ${{this.currentWord.answer}}.`
        this.alertType = 'error'
        window.setTimeout(() => {{
          this.advanceWord()
        }}, 900)
        return
      }}
      if (this.guess === this.currentWord.answer) {{
        this.registerWin(this.currentWord.answer.length * 10, 'won')
        this.roundLocked = true
        this.message = `Boa. Palavra completa: ${{this.currentWord.answer}}.`
        this.alertType = 'success'
        window.setTimeout(() => {{
          this.advanceWord()
        }}, 900)
      }}
    }},
    advanceWord () {{
      if (this.gameOver) {{
        this.message = this.session.wins >= this.targetWins
          ? 'Vitoria. Voce completou palavras suficientes.'
          : 'Fim de jogo. Tentativas esgotadas.'
        this.alertType = this.session.wins >= this.targetWins ? 'success' : 'error'
        return
      }}
      this.currentWordIndex = (this.currentWordIndex + 1) % this.words.length
      this.resetWord()
      this.message = 'Nova palavra liberada.'
      this.alertType = 'info'
    }},
    resetWord () {{
      this.guess = ''
      this.usedIndices = []
      this.roundLocked = false
    }},
    resetGame () {{
      this.resetSession()
      this.currentWordIndex = 0
      this.resetWord()
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.game-shell {{
  max-width: 1480px;
}}

.game-surface {{
  border-radius: 28px;
}}

.letter-slots {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(44px, 1fr));
  gap: 8px;
}}

.letter-slot {{
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  font-size: 1.25rem;
  font-weight: 700;
}}
</style>
"""


def _build_pattern_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-6" elevation="6">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Generated game</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Descubra o padrao correto entre cartas e repita sem errar.</p>
          </div>

          <v-alert
            v-if="message"
            dense
            text
            :type="alertType"
            class="mb-4"
          >
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Comece a rodada para gerar uma ordem de cartas.</li>
              <li>Toque nas cartas do menor para o maior numero.</li>
              <li>Complete a sequencia inteira para vencer a rodada.</li>
              <li>Se tocar fora da ordem, perde uma vida.</li>
              <li>O desafio cresce a cada rodada vencida.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Nivel</div>
                <div class="text-h4">{{{{ level }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Proximo alvo</div>
                <div class="text-h4">{{{{ expectedValue || '-' }}}}</div>
              </v-card>
            </v-col>
            <v-col cols="12" sm="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Vidas</div>
                <div class="text-h4">{{{{ livesLeft }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mb-4">
            <v-btn
              color="primary"
              large
              :disabled="gameOver || roundActive"
              @click="startRound"
            >
              {{{{ roundActive ? 'Rodada ativa' : 'Comecar rodada' }}}}
            </v-btn>
          </div>

          <v-row dense>
            <v-col
              v-for="card in cards"
              :key="card.id"
              cols="6"
              sm="3"
            >
              <v-btn
                block
                x-large
                class="pattern-card"
                :color="card.found ? 'success' : 'primary'"
                :disabled="gameOver || !roundActive || card.found"
                @click="pickCard(card.id)"
              >
                {{{{ card.value }}}}
              </v-btn>
            </v-col>
          </v-row>

          <div class="text-center mt-6">
            <v-btn text large @click="resetGame">
              Reiniciar
            </v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    level: 1,
    maxLives: 3,
    cards: [],
    expectedIndex: 0,
    roundActive: false,
    message: 'Comece uma rodada para montar o padrao.',
    alertType: 'info'
  }}),
  computed: {{
    expectedValue () {{
      return this.cards[this.expectedIndex] ? this.cards[this.expectedIndex].value : null
    }},
    livesLeft () {{
      return Math.max(this.maxLives - this.session.losses, 0)
    }},
    gameOver () {{
      return this.session.losses >= this.maxLives
    }}
  }},
  methods: {{
    startRound () {{
      if (this.gameOver || this.roundActive) {{
        return
      }}
      const size = Math.min(this.level + 2, 8)
      const values = this.shuffle(Array.from({{ length: size }}, (_, index) => index + 1))
      this.cards = values.map((value, index) => ({{
        id: index + 1,
        value,
        found: false
      }}))
      this.cards.sort((a, b) => a.value - b.value)
      this.cards = this.shuffle(this.cards)
      this.expectedIndex = 0
      this.roundActive = true
      this.startSessionRound('playing')
      this.message = 'Toque os numeros em ordem crescente.'
      this.alertType = 'info'
    }},
    shuffle (items) {{
      const copy = [...items]
      for (let index = copy.length - 1; index > 0; index -= 1) {{
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = copy[index]
        copy[index] = copy[randomIndex]
        copy[randomIndex] = temp
      }}
      return copy
    }},
    pickCard (cardId) {{
      if (!this.roundActive || this.gameOver) {{
        return
      }}
      const card = this.cards.find((entry) => entry.id === cardId)
      if (!card || card.found) {{
        return
      }}
      if (card.value !== this.expectedValue) {{
        this.registerLoss('lost')
        this.roundActive = false
        this.message = this.gameOver
          ? 'Fim de jogo. A ordem te venceu.'
          : `Ordem errada. O proximo numero era ${{this.expectedValue}}.`
        this.alertType = 'error'
        return
      }}

      card.found = true
      this.expectedIndex += 1
      if (this.expectedIndex >= this.cards.length) {{
        const points = this.cards.length * 12
        this.registerWin(points, 'won')
        this.level += 1
        this.roundActive = false
        this.message = `Padrao resolvido. Voce ganhou ${{points}} pontos.`
        this.alertType = 'success'
      }} else {{
        this.message = `Boa. Agora encontre o ${{this.expectedValue}}.`
        this.alertType = 'success'
      }}
    }},
    resetGame () {{
      this.resetSession()
      this.level = 1
      this.cards = []
      this.expectedIndex = 0
      this.roundActive = false
      this.message = 'Jogo reiniciado.'
      this.alertType = 'info'
    }}
  }}
}}
</script>

<style scoped>
.pattern-card {{
  min-height: 88px;
}}
</style>
"""


def _build_physics_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container fluid class="{request.component_key} game-shell py-6">
    <v-row justify="center">
      <v-col cols="12" lg="11" xl="10">
        <v-card class="pa-6" elevation="8">
          <div class="text-center mb-6">
            <div class="text-overline mb-2">Skill shot arena</div>
            <h1 class="text-h4 mb-2">{request.game_name}</h1>
            <p class="mb-0">Ajuste angulo e potencia, acerte a zona quente e transforme cada disparo em momento de palco.</p>
          </div>

          <v-alert v-if="message" dense text :type="alertType" class="mb-4">
            {{{{ message }}}}
          </v-alert>

          <v-card outlined class="pa-4 mb-4 text-left">
            <div class="text-subtitle-1 font-weight-bold mb-2">Como jogar</div>
            <ul class="mb-0">
              <li>Ajuste o angulo e a potencia antes de cada disparo.</li>
              <li>Tente pousar o projétil dentro da zona premium.</li>
              <li>Acertos quase perfeitos rendem mais pontos e mantem a arena em alta.</li>
              <li>Ganhe 3 acertos fortes antes de errar 3 vezes.</li>
            </ul>
          </v-card>

          <game-stats-bar :session="session" />

          <v-row class="mb-4">
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Zona alvo</div>
                <div class="text-h4">{{{{ targetMin }}}}m - {{{{ targetMax }}}}m</div>
              </v-card>
            </v-col>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Melhor impacto</div>
                <div class="text-h4">{{{{ bestShot }}}} pts</div>
              </v-card>
            </v-col>
            <v-col cols="12" md="4">
              <v-card outlined class="pa-4 text-center">
                <div class="text-caption">Margem atual</div>
                <div class="text-h4">{{{{ lastDeltaLabel }}}}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="5">
              <v-card outlined class="pa-4 control-panel mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-4">Controles</div>
                <div class="mb-2 d-flex justify-space-between">
                  <span>Angulo</span>
                  <strong>{{{{ angle }}}}°</strong>
                </div>
                <v-slider v-model="angle" min="20" max="75" step="1" color="amber darken-2" track-color="blue-grey lighten-4" />

                <div class="mb-2 d-flex justify-space-between">
                  <span>Potencia</span>
                  <strong>{{{{ power }}}}%</strong>
                </div>
                <v-slider v-model="power" min="30" max="100" step="1" color="cyan darken-2" track-color="blue-grey lighten-4" />

                <div class="d-flex flex-wrap gap-2 mt-4">
                  <v-btn color="primary" large :disabled="gameOver" @click="fireShot">Disparar</v-btn>
                  <v-btn text large @click="retune">Nova zona</v-btn>
                </div>
              </v-card>

              <v-card outlined class="pa-4">
                <div class="text-subtitle-1 font-weight-bold mb-3">Objetivo</div>
                <p class="mb-2">Encontre a regulagem ideal e transforme previsao em precisão.</p>
                <div class="text-body-2">A zona central vale mais. Erros amplos custam uma vida e esfriam a streak.</div>
              </v-card>
            </v-col>

            <v-col cols="12" md="7">
              <v-card outlined class="pa-4 physics-stage">
                <div class="d-flex justify-space-between align-center flex-wrap mb-4">
                  <div>
                    <div class="text-overline">Arena de impacto</div>
                    <div class="text-h6">Landing strip com feedback imediato</div>
                  </div>
                  <div class="text-body-2">Disparo {{{{ session.rounds + 1 }}}}</div>
                </div>

                <div class="trajectory-preview mb-4">
                  <div class="trajectory-arc" :style="arcStyle"></div>
                  <div class="launcher-base"></div>
                  <div class="impact-marker" :style="impactStyle"></div>
                  <div class="target-zone" :style="targetZoneStyle"></div>
                </div>

                <div class="distance-ruler">
                  <div
                    v-for="mark in rulerMarks"
                    :key="mark"
                    class="distance-ruler__tick"
                    :style="tickStyle(mark)"
                  >
                    <span>{{{{ Math.round(mark * maxDistance / 100) }}}}m</span>
                  </div>
                </div>

                <div class="mt-6 text-body-1 font-weight-medium">
                  {{{{ shotSummary }}}}
                </div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-center mt-6">
            <v-btn text large @click="resetGame">Reiniciar</v-btn>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import GameSessionMixin from './mixins/GameSessionMixin'

export default {{
  name: '{request.game_name}',
  components: {{
    GameStatsBar: () => import('./GameStatsBar')
  }},
  mixins: [GameSessionMixin],
  data: () => ({{
    angle: 48,
    power: 68,
    maxDistance: 120,
    targetCenter: 72,
    targetRadius: 9,
    lastLanding: null,
    lastPoints: 0,
    bestShot: 0,
    message: 'Ajuste os controles e solte o primeiro disparo.',
    alertType: 'info'
  }}),
  computed: {{
    targetMin () {{
      return Math.max(0, Math.round(this.targetCenter - this.targetRadius))
    }},
    targetMax () {{
      return Math.min(this.maxDistance, Math.round(this.targetCenter + this.targetRadius))
    }},
    gameOver () {{
      return this.session.wins >= 3 || this.session.losses >= 3
    }},
    landingPercent () {{
      const landing = this.lastLanding === null ? 14 : this.lastLanding
      return Math.max(4, Math.min(96, (landing / this.maxDistance) * 100))
    }},
    impactStyle () {{
      return {{
        left: `${{this.landingPercent}}%`
      }}
    }},
    targetZoneStyle () {{
      const left = ((this.targetCenter - this.targetRadius) / this.maxDistance) * 100
      const width = ((this.targetRadius * 2) / this.maxDistance) * 100
      return {{
        left: `${{Math.max(4, left)}}%`,
        width: `${{Math.min(92, width)}}%`
      }}
    }},
    arcStyle () {{
      const width = Math.max(22, this.landingPercent)
      const height = Math.max(90, this.angle * 2.1)
      return {{
        width: `${{width}}%`,
        height: `${{height}}px`
      }}
    }},
    rulerMarks () {{
      return [0, 20, 40, 60, 80, 100]
    }},
    lastDeltaLabel () {{
      if (this.lastLanding === null) {{
        return 'sem disparo'
      }}
      const delta = Math.abs(this.lastLanding - this.targetCenter)
      return `${{delta.toFixed(1)}}m`
    }},
    shotSummary () {{
      if (this.lastLanding === null) {{
        return 'A arena está pronta. Mire na janela premium para começar com moral.'
      }}
      return `Ultimo disparo: impacto em ${{this.lastLanding.toFixed(1)}}m, ${{this.lastPoints}} pontos e status ${{this.session.status || 'ready'}}.`
    }}
  }},
  methods: {{
    fireShot () {{
      if (this.gameOver) {{
        return
      }}
      this.startSessionRound('launching')
      const radians = (this.angle * Math.PI) / 180
      const normalizedPower = this.power / 100
      const rawDistance = Math.sin(radians * 2) * normalizedPower * this.maxDistance
      const drift = ((this.angle % 7) - 3) * 1.2 + ((this.power % 9) - 4)
      const landing = Math.max(0, Math.min(this.maxDistance, rawDistance + drift))
      const delta = Math.abs(landing - this.targetCenter)
      this.lastLanding = landing

      if (delta <= 3) {{
        const points = 80
        this.lastPoints = points
        this.bestShot = Math.max(this.bestShot, points)
        this.registerWin(points, 'bullseye')
        this.message = `Bullseye. O disparo pousou dentro da zona quente e rendeu ${{points}} pontos.`
        this.alertType = 'success'
      }} else if (delta <= this.targetRadius) {{
        const points = 45
        this.lastPoints = points
        this.bestShot = Math.max(this.bestShot, points)
        this.registerWin(points, 'won')
        this.message = `Boa regulagem. Impacto forte a ${{landing.toFixed(1)}}m e +${{points}} pontos.`
        this.alertType = 'success'
      }} else {{
        this.lastPoints = 0
        this.registerLoss('lost')
        this.message = this.gameOver
          ? 'Fim de jogo. A calibragem saiu da janela segura.'
          : `Disparo fora da zona. Voce caiu ${{delta.toFixed(1)}}m longe do alvo.`
        this.alertType = 'error'
      }}

      if (!this.gameOver) {{
        this.retarget()
      }}
    }},
    retarget () {{
      const center = 36 + Math.floor(Math.random() * 54)
      const radius = 7 + Math.floor(Math.random() * 5)
      this.targetCenter = center
      this.targetRadius = radius
    }},
    retune () {{
      if (this.gameOver) {{
        return
      }}
      this.retarget()
      this.message = 'Zona reposicionada. Recalibre e busque o proximo highlight.'
      this.alertType = 'info'
    }},
    tickStyle (mark) {{
      return {{
        left: `${{mark}}%`
      }}
    }},
    resetGame () {{
      this.resetSession()
      this.angle = 48
      this.power = 68
      this.lastLanding = null
      this.lastPoints = 0
      this.bestShot = 0
      this.retarget()
      this.message = 'Arena reiniciada.'
      this.alertType = 'info'
    }}
  }},
  mounted () {{
    this.retarget()
  }}
}}
</script>

<style scoped>
.control-panel {{
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.96));
}}

.physics-stage {{
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.94));
  color: #f8fafc;
}}

.trajectory-preview {{
  position: relative;
  min-height: 260px;
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(14, 165, 233, 0.22), rgba(8, 47, 73, 0.04) 50%, rgba(132, 204, 22, 0.22) 50%, rgba(101, 163, 13, 0.28));
  overflow: hidden;
}}

.trajectory-arc {{
  position: absolute;
  left: 10%;
  bottom: 58px;
  border-top: 4px solid rgba(250, 204, 21, 0.95);
  border-right: 4px solid rgba(250, 204, 21, 0.95);
  border-top-right-radius: 220px;
}}

.launcher-base {{
  position: absolute;
  left: 8%;
  bottom: 38px;
  width: 56px;
  height: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f97316, #fb7185);
}}

.impact-marker {{
  position: absolute;
  bottom: 32px;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #f8fafc;
  box-shadow: 0 0 0 8px rgba(248, 250, 252, 0.12);
  transform: translateX(-50%);
}}

.target-zone {{
  position: absolute;
  bottom: 22px;
  height: 42px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.24), rgba(250, 204, 21, 0.42), rgba(239, 68, 68, 0.26));
  border: 1px solid rgba(255, 255, 255, 0.42);
}}

.distance-ruler {{
  position: relative;
  height: 34px;
  border-top: 1px dashed rgba(248, 250, 252, 0.3);
}}

.distance-ruler__tick {{
  position: absolute;
  top: -1px;
  width: 1px;
  height: 18px;
  background: rgba(248, 250, 252, 0.45);
}}

.distance-ruler__tick span {{
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.78);
}}
</style>
"""


def generate_game(request: GameGenerationRequest, references: list[GameReference] | None = None) -> GeneratedGame:
    tag_name = to_kebab_case(request.game_name)
    engine_name = _select_template(request, references=references)
    component_code = _build_component_code(request, references=references)
    screen_code = _screen_code(request)

    return GeneratedGame(
        request=request,
        engine_name=engine_name,
        component_code=component_code,
        screen_code=screen_code,
        main_import=f"import {request.game_name}Screen from '../src/components/Screens/{request.game_name}'",
        task_entry="\n            {\n"
        f"                done: false,\n"
        f"                text: '{request.game_name}',\n"
        f"                component: '{request.component_key}',\n"
        f"                description: '{request.idea}'\n"
        "            },",
        route_entry=f"  {{ path: '/{request.component_key}', component: {request.game_name}Screen, isAuthenticated: false }},",
        screen_render=f"\n            <{tag_name} v-if=\"active == '{request.component_key}'\"></{tag_name}>",
        screen_component=f"        '{request.game_name}':   () => import('../{request.game_name}'),",
        client_render=f"\n        <{tag_name} v-if=\"active == '{request.component_key}'\"></{tag_name}>",
        client_component=f"        '{request.game_name}': () => import('../components/{request.game_name}'),",
    )


def build_fallback_output(game: GeneratedGame) -> str:
    request = game.request
    return f"""# Game Summary
Name: {request.game_name}
Key: {request.component_key}
Idea: {request.idea}
Engine: {game.engine_name}

# Main Component: src/components/{request.game_name}.vue
```vue
{game.component_code}
```

# Screen Wrapper: src/components/Screens/{request.game_name}.vue
```vue
{game.screen_code}
```

# Integration Snippets
main.js import:
```js
{game.main_import}
```

main.js task entry:
```js
{game.task_entry}
```

main.js route:
```js
{game.route_entry}
```

Screen.vue render:
```vue
{game.screen_render}
```

Screen.vue component registration:
```js
{game.screen_component}
```

Client.vue render:
```vue
{game.client_render}
```

Client.vue component registration:
```js
{game.client_component}
```
"""
