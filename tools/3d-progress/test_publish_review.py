"""Integration test: real competing pushes to a disposable bare repository."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("publish_review.sh").resolve()

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout

class PublicationTest(unittest.TestCase):
    def exercise(self, conflicts):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            git(root, "init", "--bare", str(remote))
            writer = root / "writer"
            git(root, "clone", str(remote), str(writer))
            for k,v in (("user.name","Test"),("user.email","test@example.invalid")):
                git(writer,"config",k,v)
            git(writer,"switch","-c","data")
            (writer/"index.json").write_text("original registry")
            git(writer,"add",".")
            git(writer,"commit","-m","initial")
            git(writer,"push","origin","data")
            rival=root/"rival"
            git(root,"clone","-b","data",str(remote),str(rival))
            git(rival,"config","user.name","Rival")
            git(rival,"config","user.email","rival@example.invalid")
            counter=root/"count"
            counter.write_text("0")
            hook=writer/".git/hooks/pre-push"
            hook.write_text("""#!/bin/sh
set -eu
n=$(cat "$COUNT_FILE")
if [ "$n" -lt "$CONFLICTS" ]; then
  n=$((n+1))
  echo "$n" > "$COUNT_FILE"
  git -C "$RIVAL" pull --ff-only origin data
  echo "$n" > "$RIVAL/concurrent.txt"
  git -C "$RIVAL" add concurrent.txt
  git -C "$RIVAL" commit -m "concurrent update $n"
  git -C "$RIVAL" push origin data
fi
""")
            hook.chmod(0o755)
            report=root/"report.json"
            report.write_text('{"advisory":true}')
            env=dict(os.environ,COUNT_FILE=str(counter),CONFLICTS=str(conflicts),RIVAL=str(rival),RETRY_DELAY="0")
            result=subprocess.run(["bash",str(SCRIPT),"origin","data",str(report)],cwd=writer,env=env,capture_output=True,text=True)
            print(result.stdout,result.stderr)
            self.assertEqual(result.stdout.count("publication attempt"),3)
            self.assertEqual(int(counter.read_text()),conflicts)
            self.assertEqual(result.stderr.count("[rejected]") + result.stderr.count("[remote rejected]"),conflicts)
            git(rival,"pull","--ff-only","origin","data")
            self.assertEqual((rival/"index.json").read_text(),"original registry")
            self.assertEqual((rival/"concurrent.txt").read_text().strip(),str(conflicts))
            self.assertEqual(result.returncode,0 if conflicts==2 else 1)
            if conflicts==2:
                self.assertEqual((rival/"visual-review.json").read_text(),report.read_text())
            else:
                self.assertFalse((rival/"visual-review.json").exists())
                self.assertIn("stopped after three",result.stderr)

    def test_recovers_on_third_attempt(self):
        self.exercise(2)

    def test_stops_after_three_failures(self):
        self.exercise(3)

if __name__=="__main__":
    unittest.main()
