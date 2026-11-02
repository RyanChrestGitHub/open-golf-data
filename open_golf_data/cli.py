"""Local-only CLI for the first synthetic laboratory."""

import argparse
import json
from pathlib import Path

from .fixture import run_fixture
from .ledger import Ledger


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ogd", description="Open Golf Data local laboratory")
    cmds = p.add_subparsers(dest="command", required=True)
    demo = cmds.add_parser("demo", help="Replay the fictional mixed-player and multi-installation fixture")
    demo.add_argument("--output", default="lab-output", help="Local output directory")
    demo.add_argument("--fixture", type=Path, help="Optional alternative fixture JSON")
    verify = cmds.add_parser("inspect", help="Inspect counts in a local ledger")
    verify.add_argument("database", type=Path)
    args = p.parse_args(argv)
    if args.command == "demo":
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        with Ledger(output / "events.sqlite") as ledger:
            if args.fixture:
                report = run_fixture(ledger, args.fixture)
            else:
                report = run_fixture(ledger)
            for player in ("golfer-001", "golfer-002"):
                ledger.export_golfer(player, output / f"{player}.json")
                ledger.export_golfer(player, output / f"{player}.csv")
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        print(f"Synthetic lab complete: {output.resolve()}")
        print("No real launch monitor, cloud login, or network synchronization is implemented.")
    elif args.command == "inspect":
        with Ledger(args.database) as ledger:
            print(json.dumps(ledger.counts(), indent=2))
    return 0
