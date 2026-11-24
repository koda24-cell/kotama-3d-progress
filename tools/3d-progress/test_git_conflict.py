import subprocess
import tempfile
import unittest
from pathlib import Path

class GitConflict(unittest.TestCase):
    def test_replay_preserves_concurrent_update(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(cwd,*args,ok=True):
                p=subprocess.run(["git",*args],cwd=cwd,capture_output=True,text=True)
                if ok: self.assertEqual(p.returncode,0,p.stderr)
                return p
            git(root,"init","--bare","remote.git")
            git(root,"clone","remote.git","a")
            a=root/"a"
            git(a,"config","user.name","Test")
            git(a,"config","user.email","test@example.invalid")
            (a/"index.json").write_text("base\n")
            git(a,"add",".")
            git(a,"commit","-m","base")
            git(a,"push","origin","HEAD:refs/heads/3d-progress-data")
            git(root,"clone","-b","3d-progress-data","remote.git","b")
            b=root/"b"
            git(b,"config","user.name","Test")
            git(b,"config","user.email","test@example.invalid")
            (a/"index.json").write_text("base\nfirst\n")
            git(a,"commit","-am","first")
            (b/"index.json").write_text("base\nsecond\n")
            git(b,"commit","-am","second")
            git(b,"push","origin","HEAD:3d-progress-data")
            self.assertNotEqual(git(a,"push","origin","HEAD:3d-progress-data",ok=False).returncode,0)
            git(a,"fetch","origin","3d-progress-data")
            git(a,"reset","--hard","FETCH_HEAD")
            p=a/"index.json"
            p.write_text(p.read_text()+"first\n")
            git(a,"commit","-am","replay")
            git(a,"push","origin","HEAD:3d-progress-data")
            git(b,"fetch","origin","3d-progress-data")
            self.assertEqual(git(b,"show","FETCH_HEAD:index.json").stdout,"base\nsecond\nfirst\n")
