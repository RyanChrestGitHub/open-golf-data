"""Local-only CLI for the first synthetic laboratory."""

import argparse
import json
import sys
from pathlib import Path

from .fixture import run_fixture
from .ledger import Ledger
from .intake import stage_evidence, verify_evidence
from .classification import inspect_evidence
from .archive_table import _unique_object
from .metric_view import MetricMapping, read_metric


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
    evidence_inspect = cmds.add_parser("inspect-evidence", help="Read-only bounded syntax inspection; no adapter selection")
    evidence_inspect.add_argument("directory", type=Path, help="Staged evidence directory")
    metric = cmds.add_parser("metric-view", help="Read one explicitly mapped archival metric as JSON")
    metric.add_argument("archive", type=Path, help="Local archival table JSON")
    metric.add_argument("--mappings", required=True, type=Path, help="Local JSON list of MetricMapping objects")
    metric.add_argument("--source-sha256", required=True, help="Independently known source digest")
    metric.add_argument("--key", required=True, help="Common metric key from the supplied mappings")
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
    elif args.command == "metric-view":
        try:
            config = json.loads(args.mappings.read_text(encoding="utf-8"),
                                object_pairs_hook=_unique_object)
            if not isinstance(config, list):
                raise ValueError("mapping list required")
            mappings = [MetricMapping(**item) for item in config]
            report = read_metric(args.archive, expected_source_sha256=args.source_sha256,
                                 metric_key=args.key, mappings=mappings)
        except (OSError, ValueError, TypeError):
            print("Metric view failed: invalid archive, mappings, key or source digest", file=sys.stderr)
            return 1
        print(json.dumps(report, indent=2))
    elif args.command == "evidence":
        receipt = stage_evidence(args.file, args.output, device=args.device,
                                 software=args.software, version=args.version,
                                 route=args.route, kind=args.kind)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print("Evidence staged locally only. It has NOT been uploaded or certified.")
    elif args.command == "inspect-evidence":
        try:
            report = inspect_evidence(args.directory)
        except ValueError:
            print("Evidence inspection failed: invalid or changed staged evidence", file=sys.stderr)
            return 1
        print(json.dumps(report, indent=2, sort_keys=True))
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
