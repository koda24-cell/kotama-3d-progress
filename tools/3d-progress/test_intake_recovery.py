import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ingest_artifacts import ingest

class IntakeRecovery(unittest.TestCase):
    def test_invalid_then_valid(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("a","b","c"):
                (root/name).mkdir()
            (root/"a"/"manifest.json").write_text("{")
            for name in ("b","c"):
                (root/name/"manifest.json").write_text(json.dumps(dict(id=name,publication_cleared=True,approval_state="NOT_APPROVED")))
            with patch("ingest_artifacts.register",side_effect=[ValueError("Invalid PNG"),True]) as register:
                result=ingest(root,root)
            self.assertEqual(register.call_count,2)
            self.assertEqual(result,[("unknown","quarantined:invalid-manifest"),("b","quarantined:ValueError"),("c","updated")])
