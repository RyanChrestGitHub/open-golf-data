import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from open_golf_data.cli import main


class CliTests(unittest.TestCase):
    def test_metric_view_example_is_read_only_json(self):
        root = Path(__file__).resolve().parents[1]
        archive = root / "examples" / "fictional_archive.json"
        mappings = root / "examples" / "fictional_mappings.json"
        original = archive.read_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["metric-view", str(archive), "--mappings", str(mappings),
                           "--source-sha256", "ab" * 32, "--key", "ball_speed"])
        self.assertEqual(result, 0)
        view = json.loads(output.getvalue())
        self.assertEqual(view["metric_key"], "ball_speed")
        self.assertEqual(view["unit_status"], "declared")
        self.assertEqual(view["mapping"]["kind"], "unknown")
        self.assertEqual([row["raw_value"] for row in view["rows"]], ["0.00", None, ""])
        self.assertEqual(archive.read_bytes(), original)
        for key, status in [("unknown_quantity", "unknown"), ("duration", "conflicting")]:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["metric-view", str(archive), "--mappings", str(mappings),
                                       "--source-sha256", "ab" * 32, "--key", key]), 0)
            self.assertEqual(json.loads(output.getvalue())["unit_status"], status)

    def test_metric_view_errors_are_nonzero_without_partial_output(self):
        root = Path(__file__).resolve().parents[1]
        archive = root / "examples" / "fictional_archive.json"
        mappings = root / "examples" / "fictional_mappings.json"
        for key, digest, config in [("absent", "ab" * 32, mappings),
                                    ("ball_speed", "cd" * 32, mappings),
                                    ("ball_speed", "ab" * 32, root / "absent.json")]:
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                result = main(["metric-view", str(archive), "--mappings", str(config),
                               "--source-sha256", digest, "--key", key])
            self.assertEqual(result, 1)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("Metric view failed", errors.getvalue())

    def test_metric_view_rejects_malformed_mapping_configuration(self):
        root = Path(__file__).resolve().parents[1]
        archive = root / "examples" / "fictional_archive.json"
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "mapping.json"
            for content in ['{}', '[null]', '[{"key":"a","key":"b"}]', '[{"extra":true}]']:
                config.write_text(content, encoding="utf-8")
                output, errors = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    result = main(["metric-view", str(archive), "--mappings", str(config),
                                   "--source-sha256", "ab" * 32, "--key", "ball_speed"])
                self.assertEqual(result, 1)
                self.assertEqual(output.getvalue(), "")

    def test_end_to_end_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "outputs"
            self.assertEqual(main(["demo", "--output", str(directory)]), 0)
            self.assertEqual(json.loads((directory / "report.json").read_text())["unclaimed"], 1)
            self.assertEqual(len(json.loads((directory / "golfer-001.json").read_text())["observations"]), 3)
            self.assertTrue((directory / "events.sqlite").is_file())
            self.assertEqual(main(["demo", "--output", str(directory)]), 0)


if __name__ == "__main__":
    unittest.main()
