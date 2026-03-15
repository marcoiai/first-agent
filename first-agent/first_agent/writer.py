from pathlib import Path

from first_agent.game_generator import GeneratedGame


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

        component_path.write_text(game.component_code, encoding="utf-8")
        screen_path.write_text(game.screen_code, encoding="utf-8")

        self._insert_once(
            main_path,
            game.main_import,
            "import MathChallenge from '../src/components/MathChallenge'",
        )
        self._insert_before(main_path, game.task_entry, "        ]")
        self._insert_before(main_path, f"\n{game.route_entry}", "  { path: '/sv', component: StreetView },")

        self._insert_before(screen_view_path, game.screen_render, "            <MathChallenge v-if=\"active == 'mathchallenge'\"></MathChallenge>")
        self._insert_before(screen_view_path, f"\n{game.screen_component}", "        'MathChallenge':  () => import('../MathChallenge.vue')")

        self._insert_before(client_view_path, game.client_render, "        <ask-multiple v-if=\"active == 'AskMultiple'\" :choices=\"task.choices\"></ask-multiple>")
        self._insert_before(client_view_path, f"\n{game.client_component}", "        'welcome':      () => import('../components/Screens/Welcome'),")

        return [component_path, screen_path, main_path, screen_view_path, client_view_path]

    def _insert_once(self, path: Path, snippet: str, anchor: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet in text:
            return
        updated = text.replace(anchor, f"{anchor}\n{snippet}", 1)
        path.write_text(updated, encoding="utf-8")

    def _insert_before(self, path: Path, snippet: str, anchor: str) -> None:
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text:
            return
        updated = text.replace(anchor, f"{snippet}\n{anchor}", 1)
        path.write_text(updated, encoding="utf-8")
