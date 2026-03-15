import re
from dataclasses import dataclass


@dataclass
class GameGenerationRequest:
    idea: str
    game_name: str
    component_key: str


@dataclass
class GeneratedGame:
    request: GameGenerationRequest
    component_code: str
    screen_code: str
    main_import: str
    task_entry: str
    route_entry: str
    screen_render: str
    screen_component: str
    client_render: str
    client_component: str


def to_pascal_case(value: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    parts = [part for part in "".join(ch if ch.isalnum() else " " for ch in normalized).split() if part]
    return "".join(part.capitalize() for part in parts) or "GeneratedGame"


def to_component_key(value: str) -> str:
    sanitized = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return "".join(sanitized.split()) or "generatedgame"


def to_kebab_case(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("-")
        chars.append(char.lower())
    return "".join(chars)


def build_generation_request(idea: str) -> GameGenerationRequest:
    game_name = to_pascal_case(idea)
    return GameGenerationRequest(
        idea=idea,
        game_name=game_name,
        component_key=to_component_key(idea),
    )


def build_system_prompt() -> str:
    return (
        "You generate new mini-games for a Vue 2 + Vuetify project named entert2. "
        "Output concise but complete code in the established project pattern. "
        "Every game must include a main component, a thin Screens wrapper, and "
        "integration snippets for main.js, Screen.vue, and Client.vue. "
        "Use the shared session contract with score, wins, losses, rounds, streak, and status."
    )


def build_user_prompt(request: GameGenerationRequest) -> str:
    return (
        f"Game idea: {request.idea}\n"
        f"Game component name: {request.game_name}\n"
        f"Component key: {request.component_key}\n"
        "Target stack: Vue 2, Vuetify 2, Firebase-ready app.\n"
        "Reference pattern: standalone component + screen wrapper + integration snippets.\n"
        "Use a self-contained game loop, mobile-friendly layout, and shared session stats."
    )


def _select_template(request: GameGenerationRequest) -> str:
    idea = request.idea.lower()
    if "reaction" in idea or "tap" in idea or "timed" in idea:
        return "reaction"
    if "memory" in idea or "symbol" in idea or "hidden order" in idea:
        return "memory"
    if "pattern" in idea or "sequence" in idea or "sorting" in idea:
        return "pattern"
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


def _build_component_code(request: GameGenerationRequest) -> str:
    template_name = _select_template(request)
    if template_name == "reaction":
        return _build_reaction_component(request)
    if template_name == "memory":
        return _build_memory_component(request)
    if template_name == "pattern":
        return _build_pattern_component(request)
    return _build_pick_one_component(request)


def _build_pick_one_component(request: GameGenerationRequest) -> str:
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
</style>
"""


def _build_reaction_component(request: GameGenerationRequest) -> str:
    return f"""<template>
  <v-container class="{request.component_key} fill-height">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="pa-6 text-center" elevation="6">
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


def generate_game(request: GameGenerationRequest) -> GeneratedGame:
    tag_name = to_kebab_case(request.game_name)
    component_code = _build_component_code(request)
    screen_code = _screen_code(request)

    return GeneratedGame(
        request=request,
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
