"""Recipe wiring with invented bytes only; never opens a real fixture."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from open_golf_data.cli import main


ROOT = Path(__file__).resolve().parents[1]


class SquareStatsRecipeTests(unittest.TestCase):
    def test_fictional_pipeline_and_real_digest_mapping_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            source = work / "invented.csv"
            payload = (b'fictional metadata\nfictional metadata\n'
                       b'Ball Speed(mph),Carry(yd),Unused\n'
                       b'000.00,1.2300,fictional\n'
                       b',0,fictional\n'
                       b'000.00,1.2300,fictional\n')
            source.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            stage = work / "stage"
            archive = work / "projection.json"

            def invoke(args):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    status = main(args)
                return status, out.getvalue(), err.getvalue()

            self.assertEqual(invoke(["evidence", str(source), "--output", str(stage)])[0], 0)
            evidence = stage / ("ev-" + digest[:24])
            before = {p: p.read_bytes() for p in (source, evidence / "source.bin", evidence / "receipt.json")}
            self.assertEqual(invoke(["verify-evidence", str(evidence)])[0], 0)
            self.assertEqual(invoke(["project-csv", str(evidence), "--config",
                                    str(ROOT / "examples/squarestats_projection.json"),
                                    "--output", str(archive)])[0], 0)
            real_mappings = ROOT / "examples/squarestats_mappings.json"
            args = ["metric-view", str(archive), "--mappings", str(real_mappings),
                    "--source-sha256", digest, "--key", "ball_speed"]
            status, out, _ = invoke(args)
            self.assertEqual(status, 1)  # Published source pin cannot bind invented bytes.
            self.assertEqual(out, "")
            mappings = json.loads(real_mappings.read_text(encoding="utf-8"))
            for mapping in mappings:
                mapping["source_sha256"] = digest  # Test-only link to invented bytes.
            fictional_mappings = work / "fictional_mappings.json"
            fictional_mappings.write_text(json.dumps(mappings), encoding="utf-8")
            args[3] = str(fictional_mappings)
            for key, expected in (("ball_speed", ["000.00", "", "000.00"]),
                                  ("carry_distance", ["1.2300", "0", "1.2300"])):
                args[-1] = key
                status, out, _ = invoke(args)
                self.assertEqual(status, 0)
                view = json.loads(out)
                self.assertEqual([row["raw_value"] for row in view["rows"]], expected)
                self.assertEqual(view["unit_status"], "declared")
                self.assertEqual(view["mapping"]["confidence"], "tentative")
                self.assertEqual(view["mapping"]["kind"], "unknown")
            for path, original in before.items():
                self.assertEqual(path.read_bytes(), original)
