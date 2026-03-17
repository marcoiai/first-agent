import argparse

from first_agent.agent import FirstAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the entert2 game generator agent.")
    parser.add_argument("goal", nargs="?", help="Game idea to give to the agent.")
    parser.add_argument("--auto", action="store_true", help="Let the agent invent a game idea automatically.")
    parser.add_argument("--write", action="store_true", help="Write the generated game directly into entert2.")
    parser.add_argument("--target", default=None, help="Override the entert2 repo path.")
    parser.add_argument("--seed", default=None, help="Optional seed for deterministic auto-idea generation.")
    parser.add_argument(
        "--category",
        default=None,
        help="Prefer a platform category for auto mode: learning, self-development, diagnostic, training, event, showtime, presentation.",
    )
    parser.add_argument("--show-last", action="store_true", help="Show the last stored generated game summary.")
    parser.add_argument("--write-last", action="store_true", help="Write the last stored generated game into entert2.")
    parser.add_argument("--approve-last", action="store_true", help="Mark the last generated game as approved.")
    parser.add_argument("--reject-last", action="store_true", help="Mark the last generated game as rejected.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = FirstAgent()
    if args.approve_last and args.reject_last:
        raise SystemExit("Use only one of --approve-last or --reject-last.")
    if args.show_last and args.write_last:
        raise SystemExit("Use only one of --show-last or --write-last.")
    if args.show_last:
        print(agent.show_last_generation())
        return
    if args.write_last:
        print(agent.write_last_generation(repo_path=args.target))
        return
    if args.approve_last:
        print(agent.record_feedback("approved"))
        return
    if args.reject_last:
        print(agent.record_feedback("rejected"))
        return
    if args.auto and args.write:
        result = agent.auto_write(repo_path=args.target, seed=args.seed, category=args.category)
    elif args.auto:
        if args.category:
            result = agent.auto_run_for_category(args.category, repo_path=args.target, seed=args.seed)
        else:
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
