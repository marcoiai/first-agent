# First Agent

AI game generator starter focused on generating new mini-games for the `entert2` Vue 2 + Vuetify system.

## Setup

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Shortcut script:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
chmod +x run.sh
./run.sh --auto
```

The script uses `.venv/bin/python` automatically and forwards any arguments to `first_agent.main`.

Common examples with the shortcut script:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
./run.sh "temple relic expedition with risky paths and fading energy"
./run.sh --auto
./run.sh --auto --category showtime
./run.sh --suggest
./run.sh --suggest --family platform-hub
./run.sh --write-last
```

Important:

- use `./run.sh`, not `/run.sh`
- run it from `/Users/auser/Projects/ml-agent/first-agent`
- pass the game idea as the final positional argument when generating a specific game

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main "reaction game with colored targets"
```

Write directly into `entert2`:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main "memory game with hidden symbols" --write
```

Autonomous idea generation:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --auto
```

Autonomous idea generation plus direct write:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --auto --write
```

Category-guided autonomous generation:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --auto --write --category training
```

Available categories:

- `training`
- `event`
- `showtime`
- `presentation`

`--auto` now prefers more intentional ideas by category and engine, trying to rotate through underrepresented experience types instead of blindly combining vague phrases.

You can also teach the agent what worked:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --approve-last
```

or mark the last generation as weak:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --reject-last
```

That feedback is stored locally and used to bias future `--auto` generations toward engines you approved more often.

To inspect the stored summary for the latest generation:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
python -m first_agent.main --show-last
```

To publish the latest stored generation into `entert2`:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
./run.sh --write-last
```

To browse ready-made prompt families before generating:

```bash
cd /Users/auser/Projects/ml-agent/first-agent
./run.sh --suggest
./run.sh --suggest --family event-platform
./run.sh --suggest --family platform-hub
./run.sh --suggest --family vertical-platform-hub
./run.sh --suggest --family assessment
```

## Environment

Create a `.env` file if needed:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
AGENT_NAME=First Agent
ENTERT2_PATH=/Users/auser/Downloads/entert2
```

The agent also stores lightweight local memory files:

- `.first_agent_feedback.json`
- `.first_agent_last_generation.json`

## Behavior

Without `OPENAI_API_KEY`, the agent still works in fallback mode:

- builds a game name and component key
- can invent a game idea with `--auto`
- can invent by platform category with `--auto --category ...`
- generates a starter component scaffold
- generates a screen wrapper
- generates integration snippets for `entert2`

With `OPENAI_API_KEY`, it uses the model to produce a more intelligent action plan.

The agent also reads existing `entert2` game components and uses the closest matches as references during generation. Today it especially benefits from strong examples like `TreasureDoors` and `ReactionRush`.
It now also has a stronger `adventure` presentation layer and a dedicated `physics`/`skill-shot` direction inspired by references such as `Catapult`.
It now also runs a local self-review pass before returning or writing code, checking things like instructions, visible primary action, objective, loss condition, and common Vue template issues.
This review now also produces a simple quality scorecard with:

- `clarity`
- `interactivity`
- `originality`
- `visual`
- `theme_fit`
- `utility`

plus an average score and a recommendation such as `approved`, `good-but-needs-polish`, `weak`, or `regenerate`.

## Direct Write Mode

With `--write`, the agent will:

- create `src/components/GameName.vue`
- create `src/components/Screens/GameName.vue`
- patch `src/main.js`
- patch `src/components/Form/Screen.vue`
- patch `src/components/Client.vue`
- report which engine was selected
- run `generate -> self-review -> refine -> write`
- report which existing `entert2` games were used as references
- print the route to open, like `https://127.0.0.1:8081/#/yourcomponentkey`
