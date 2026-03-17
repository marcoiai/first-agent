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

## Environment

Create a `.env` file if needed:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
AGENT_NAME=First Agent
ENTERT2_PATH=/Users/auser/Downloads/entert2
```

## Behavior

Without `OPENAI_API_KEY`, the agent still works in fallback mode:

- builds a game name and component key
- can invent a game idea with `--auto`
- generates a starter component scaffold
- generates a screen wrapper
- generates integration snippets for `entert2`

With `OPENAI_API_KEY`, it uses the model to produce a more intelligent action plan.

The agent also reads existing `entert2` game components and uses the closest matches as references during generation. Today it especially benefits from strong examples like `TreasureDoors` and `ReactionRush`.
It now also runs a local self-review pass before returning or writing code, checking things like instructions, visible primary action, objective, loss condition, and common Vue template issues.

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
- print the route to open, like `http://localhost:8080/#/yourcomponentkey`
