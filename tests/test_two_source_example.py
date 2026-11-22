import contextlib
import io
import json
from pathlib import Path
import unittest
from open_golf_data.cli import main


class TwoSourceExampleTests(unittest.TestCase):
    def test_same_consumer_key_preserves_distinct_source_values_and_units(self):
        root = Path(__file__).resolve().parents[1]
        config = root / 'examples/fictional_mappings.json'
        before = config.read_bytes()
        cases = [('fictional_archive.json', 'ab', 'declared', ['0.00', None, ''], 'tentative'),
                 ('fictional_second_archive.json', 'cd', 'conflicting', ['000.00', '1.2300', '1.2300'], 'unknown')]
        labels = []
        for name, digest, status, values, confidence in cases:
            archive = root / 'examples' / name
            original = archive.read_bytes()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(['metric-view', str(archive), '--mappings', str(config),
                               '--source-sha256', digest * 32, '--key', 'ball_speed'])
            self.assertEqual(result, 0)
            view = json.loads(output.getvalue())
            labels.append(view['source']['label'])
            self.assertEqual(view['metric_key'], 'ball_speed')
            self.assertEqual(view['unit_status'], status)
            self.assertEqual(view['mapping']['confidence'], confidence)
            self.assertEqual(view['mapping']['kind'], 'unknown')
            self.assertEqual([r['raw_value'] for r in view['rows']], values)
            self.assertEqual(archive.read_bytes(), original)
        self.assertNotEqual(*labels)
        self.assertEqual(config.read_bytes(), before)
