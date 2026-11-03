"""Check local references in the engineering handoff documents without network access."""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_handoff_document_references_exist(self):
        for name in (
            "AGENTS.md",
            "docs/ENGINEERING-PLAYBOOK.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            document = ROOT / name
            with self.subTest(document=name):
                text = document.read_text(encoding="utf-8")
                # These documents use inline Markdown links without titles/spaces.
                for destination in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", text):
                    url = urlsplit(destination)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    with self.subTest(link=destination):
                        target = (document.parent / unquote(url.path)).resolve()
                        self.assertTrue(target.is_relative_to(ROOT), destination)
                        self.assertTrue(target.is_file(), destination)


if __name__ == "__main__":
    unittest.main()
