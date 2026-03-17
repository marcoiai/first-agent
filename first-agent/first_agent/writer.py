from pathlib import Path

from first_agent.game_generator import GeneratedGame

GAME_STATS_BAR_CODE = """<template>
  <v-row class="mb-4" dense>
    <v-col cols="6" sm="3">
      <v-card outlined class="pa-3 text-center">
        <div class="text-caption">Score</div>
        <div class="text-h5">{{ safeSession.score }}</div>
      </v-card>
    </v-col>
    <v-col cols="6" sm="3">
      <v-card outlined class="pa-3 text-center">
        <div class="text-caption">Vitorias</div>
        <div class="text-h5">{{ safeSession.wins }}</div>
      </v-card>
    </v-col>
    <v-col cols="6" sm="3">
      <v-card outlined class="pa-3 text-center">
        <div class="text-caption">Derrotas</div>
        <div class="text-h5">{{ safeSession.losses }}</div>
      </v-card>
    </v-col>
    <v-col cols="6" sm="3">
      <v-card outlined class="pa-3 text-center">
        <div class="text-caption">Streak</div>
        <div class="text-h5">{{ safeSession.streak }}</div>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
export default {
  name: 'GameStatsBar',
  props: {
    session: {
      type: Object,
      default: () => ({})
    }
  },
  computed: {
    safeSession () {
      return Object.assign({
        score: 0,
        wins: 0,
        losses: 0,
        streak: 0,
        rounds: 0,
        status: 'idle'
      }, this.session || {})
    }
  }
}
</script>
"""

GAME_SESSION_MIXIN_CODE = """export default {
  data () {
    return {
      session: {
        score: 0,
        wins: 0,
        losses: 0,
        streak: 0,
        rounds: 0,
        status: 'idle',
        lastResult: null,
        bestScore: 0
      }
    }
  },
  methods: {
    sessionComponentName () {
      return this.$options && this.$options.name
        ? String(this.$options.name).replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()
        : 'generated-game'
    },
    startSessionRound (status = 'playing') {
      this.session.rounds += 1
      this.session.status = status
    },
    registerWin (points = 10, status = 'won') {
      const numericPoints = Number(points || 0)
      this.session.score += numericPoints
      this.session.wins += 1
      this.session.streak += 1
      this.session.status = status
      this.session.lastResult = 'win'
      this.session.bestScore = Math.max(this.session.bestScore, this.session.score)

      if (typeof this.saveGame === 'function') {
        this.saveGame({
          component: this.sessionComponentName(),
          score: this.session.score,
          win: true,
          rounds: this.session.rounds,
          streak: this.session.streak,
          status,
          sessionSnapshot: Object.assign({}, this.session)
        }, this.$route && this.$route.params ? this.$route.params.id : null)
      }
    },
    registerLoss (status = 'lost') {
      this.session.losses += 1
      this.session.streak = 0
      this.session.status = status
      this.session.lastResult = 'loss'

      if (typeof this.saveGame === 'function') {
        this.saveGame({
          component: this.sessionComponentName(),
          score: this.session.score,
          win: false,
          rounds: this.session.rounds,
          streak: this.session.streak,
          status,
          sessionSnapshot: Object.assign({}, this.session)
        }, this.$route && this.$route.params ? this.$route.params.id : null)
      }
    },
    resetSession () {
      this.session = {
        score: 0,
        wins: 0,
        losses: 0,
        streak: 0,
        rounds: 0,
        status: 'idle',
        lastResult: null,
        bestScore: 0
      }
    }
  }
}
"""


class Entert2Writer:
    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path)

    def write(self, game: GeneratedGame) -> list[Path]:
        request = game.request
        component_path = self.repo_path / "src" / "components" / f"{request.game_name}.vue"
        screen_path = self.repo_path / "src" / "components" / "Screens" / f"{request.game_name}.vue"
        main_path = self.repo_path / "src" / "main.js"
        screen_view_path = self.repo_path / "src" / "components" / "Form" / "Screen.vue"
        client_view_path = self.repo_path / "src" / "components" / "Client.vue"
        support_paths = self._support_paths_for_game(game)
        managed_paths = [component_path, screen_path, main_path, screen_view_path, client_view_path, *support_paths]
        backup_state = self._snapshot_paths(managed_paths)

        try:
            component_path.parent.mkdir(parents=True, exist_ok=True)
            screen_path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_support_files(game)

            component_path.write_text(game.component_code, encoding="utf-8")
            screen_path.write_text(game.screen_code, encoding="utf-8")

            self._insert_once(
                main_path,
                game.main_import,
                "import firebase from 'firebase/app'",
            )
            self._insert_task_entry(main_path, game.task_entry)
            self._insert_route_entry(main_path, game.route_entry)
            self._validate_main_integration(main_path, game.main_import, game.task_entry, game.route_entry)

            self._insert_component_registration(screen_view_path, game.screen_component)
            self._insert_view_render(screen_view_path, game.screen_render)

            self._insert_component_registration(client_view_path, game.client_component)
            self._insert_view_render(client_view_path, game.client_render)
            self._validate_view_integration(screen_view_path, game.screen_component, game.screen_render)
            self._validate_view_integration(client_view_path, game.client_component, game.client_render)
        except Exception:
            self._restore_paths(backup_state)
            raise

        return managed_paths

    def _support_paths_for_game(self, game: GeneratedGame) -> list[Path]:
        component_code = game.component_code
        paths: list[Path] = []
        if "import GameSessionMixin from './mixins/GameSessionMixin'" in component_code:
            paths.append(self.repo_path / "src" / "components" / "mixins" / "GameSessionMixin.js")
        if "import('./GameStatsBar')" in component_code or "<game-stats-bar" in component_code:
            paths.append(self.repo_path / "src" / "components" / "GameStatsBar.vue")
        return paths

    def _ensure_support_files(self, game: GeneratedGame) -> None:
        support_paths = self._support_paths_for_game(game)
        for path in support_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                continue
            if path.name == "GameStatsBar.vue":
                path.write_text(GAME_STATS_BAR_CODE, encoding="utf-8")
            elif path.name == "GameSessionMixin.js":
                path.write_text(GAME_SESSION_MIXIN_CODE, encoding="utf-8")

    def _snapshot_paths(self, paths: list[Path]) -> dict[Path, str | None]:
        snapshot: dict[Path, str | None] = {}
        for path in paths:
            snapshot[path] = path.read_text(encoding="utf-8") if path.exists() else None
        return snapshot

    def _restore_paths(self, snapshot: dict[Path, str | None]) -> None:
        for path, content in snapshot.items():
            if content is None:
                if path.exists():
                    path.unlink()
                continue
            path.write_text(content, encoding="utf-8")

    def _insert_once(self, path: Path, snippet: str, anchor: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet in text:
            return
        if anchor not in text:
            raise ValueError(f"Could not find insert anchor in {path}")
        updated = text.replace(anchor, f"{anchor}\n{snippet}", 1)
        path.write_text(updated, encoding="utf-8")

    def _insert_before(self, path: Path, snippet: str, anchor: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return
        updated = text.replace(anchor, f"{snippet}\n{anchor}", 1)
        path.write_text(updated, encoding="utf-8")

    def _insert_component_registration(self, path: Path, snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return

        components_start = text.find("    components: {")
        if components_start != -1:
            components_end = text.find("    },", components_start)
            if components_end != -1:
                updated = text[:components_end] + f"{snippet}\n" + text[components_end:]
                path.write_text(updated, encoding="utf-8")
                return

        raise ValueError(f"Could not find component registration anchor in {path}")

    def _insert_view_render(self, path: Path, snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return

        anchor_candidates = [
            "            </v-card>",
            "          </v-card>",
        ]

        for anchor in anchor_candidates:
            if anchor in text:
                updated = text.replace(anchor, f"{snippet}\n\n{anchor}", 1)
                path.write_text(updated, encoding="utf-8")
                return

        raise ValueError(f"Could not find render anchor in {path}")

    def _insert_route_entry(self, path: Path, snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return

        routes_start = text.find("const routes = [")
        if routes_start == -1:
            raise ValueError(f"Could not find routes declaration in {path}")

        routes_end = text.find("\n]", routes_start)
        if routes_end == -1:
            raise ValueError(f"Could not find routes closing bracket in {path}")

        updated = text[:routes_end] + f"\n{snippet}" + text[routes_end:]
        path.write_text(updated, encoding="utf-8")

    def _insert_task_entry(self, path: Path, snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return

        tasks_start = text.find("        tasks: [")
        if tasks_start == -1:
            raise ValueError(f"Could not find tasks declaration in {path}")

        tasks_end = text.find("\n        ],", tasks_start)
        if tasks_end == -1:
            raise ValueError(f"Could not find tasks closing bracket in {path}")

        prefix = text[:tasks_end]
        if not prefix.rstrip().endswith(","):
            prefix = prefix.rstrip() + ","
        updated = prefix + f"{snippet}\n" + text[tasks_end:]
        path.write_text(updated, encoding="utf-8")

    def _validate_view_integration(self, path: Path, component_snippet: str, render_snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if component_snippet.strip() not in text:
            raise ValueError(f"Component registration missing after write in {path}")
        if render_snippet.strip() not in text:
            raise ValueError(f"Render block missing after write in {path}")

    def _validate_main_integration(self, path: Path, import_snippet: str, task_snippet: str, route_snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        if import_snippet.strip() not in text:
            raise ValueError(f"Main import missing after write in {path}")
        if task_snippet.strip() not in text:
            raise ValueError(f"Task entry missing after write in {path}")
        if route_snippet.strip() not in text:
            raise ValueError(f"Route entry missing after write in {path}")
