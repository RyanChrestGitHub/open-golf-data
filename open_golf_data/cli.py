"""Local-only CLI for the first synthetic laboratory."""

import argparse
import json
import sys
from pathlib import Path

from .fixture import run_fixture
from .ledger import Ledger
from .intake import stage_evidence, verify_evidence


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ogd", description="Open Golf Data local laboratory")
    cmds = p.add_subparsers(dest="command", required=True)
    demo = cmds.add_parser("demo", help="Replay the fictional mixed-player and multi-installation fixture")
    demo.add_argument("--output", default="lab-output", help="Local output directory")
    demo.add_argument("--fixture", type=Path, help="Optional alternative fixture JSON")
    verify = cmds.add_parser("inspect", help="Inspect counts in a local ledger")
    verify.add_argument("database", type=Path)
    evidence = cmds.add_parser("evidence", help="Stage arbitrary input locally; never uploads")
    evidence.add_argument("file", type=Path, help="Source file of any format")
    evidence.add_argument("--output", type=Path, default=Path("lab-evidence"))
    evidence.add_argument("--device", default="unknown")
    evidence.add_argument("--software", default="unknown")
    evidence.add_argument("--version", default="unknown")
    evidence.add_argument("--route", default="unknown")
    evidence.add_argument("--kind", default="unknown")
    evidence_verify = cmds.add_parser("verify-evidence", help="Read-only receipt and staged-byte integrity check")
    evidence_verify.add_argument("directory", type=Path, help="Directory containing receipt.json and source.bin")
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
    elif args.command == "evidence":
        receipt = stage_evidence(args.file, args.output, device=args.device,
                                 software=args.software, version=args.version,
                                 route=args.route, kind=args.kind)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print("Evidence staged locally only. It has NOT been uploaded or certified.")
    elif args.command == "verify-evidence":
        try:
            receipt = verify_evidence(args.directory)
        except ValueError as exc:
            print(f"Evidence verification failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"evidence_id": receipt["evidence_id"],
                          "integrity_matches_receipt": True,
                          "provenance_verified": False}, indent=2))
    elif args.command == "inspect":
        with Ledger(args.database) as ledger:
            print(json.dumps(ledger.counts(), indent=2))
    return 0
