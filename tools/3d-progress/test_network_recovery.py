import subprocess
import unittest
from unittest.mock import patch
from collect import gh

class NetworkRecovery(unittest.TestCase):
    @patch("collect.time.sleep")
    @patch("collect.subprocess.run")
    def test_timeout_and_disconnect_then_success(self,run,sleep):
        run.side_effect=[subprocess.TimeoutExpired("gh",180),subprocess.CompletedProcess("gh",1,"","connection reset"),subprocess.CompletedProcess("gh",0,"ok","")]
        self.assertEqual(gh("api","test"),"ok")
        self.assertEqual(run.call_count,3)
    @patch("collect.time.sleep")
    @patch("collect.subprocess.run")
    def test_exhaustion(self,run,sleep):
        run.side_effect=subprocess.TimeoutExpired("gh",180)
        with self.assertRaises(RuntimeError): gh("api","test")
        self.assertEqual(run.call_count,3)
