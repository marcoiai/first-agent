import argparse

from first_agent.agent import FirstAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the entert2 game generator agent.")
    parser.add_argument("goal", nargs="?", help="Game idea to give to the agent.")
    parser.add_argument("--auto", action="store_true", help="Let the agent invent a game idea automatically.")
    parser.add_argument("--write", action="store_true", help="Write the generated game directly into entert2.")
    parser.add_argument("--target", default=None, help="Override the entert2 repo path.")
    parser.add_argument("--seed", default=None, help="Optional seed for deterministic auto-idea generation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = FirstAgent()
    if args.auto and args.write:
        result = agent.auto_write(repo_path=args.target, seed=args.seed)
    elif args.auto:
        result = agent.auto_run(repo_path=args.target, seed=args.seed)
    elif args.write:
        if not args.goal:
            raise SystemExit("A game idea is required unless you use --auto.")
        result = agent.write_directly(args.goal, repo_path=args.target)
    else:
        if not args.goal:
            raise SystemExit("A game idea is required unless you use --auto.")
        result = agent.run(args.goal)
    print(result)


if __name__ == "__main__":
    main()
