import json
import tempfile
import unittest
from pathlib import Path

from open_golf_data.cli import main


class CliTests(unittest.TestCase):
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
