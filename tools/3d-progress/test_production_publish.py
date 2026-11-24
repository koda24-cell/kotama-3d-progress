import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from ingest_artifacts import ingest
from test_real_png_recovery import png

class ProductionPublish(unittest.TestCase):
    def test_real_publisher_replays_registry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(cwd,*args):
                return subprocess.run(["git",*args],cwd=cwd,check=True,capture_output=True,text=True).stdout
            git(root,"init","--bare","remote.git")
            git(root,"clone","remote.git","registry")
            a=root/"registry"
            git(a,"config","user.name","Test")
            git(a,"config","user.email","test@example.invalid")
            (a/"index.json").write_text('{"models":[]}')
            (a/"renders").mkdir()
            (a/"renders"/".keep").touch()
            git(a,"add",".")
            git(a,"commit","-m","base")
            git(a,"push","origin","HEAD:3d-progress-data")
            git(root,"clone","-b","3d-progress-data","remote.git","other")
            b=root/"other"
            git(b,"config","user.name","Test")
            git(b,"config","user.email","test@example.invalid")
            tools=root/"collector"/"tools"/"3d-progress"
            shutil.copytree(Path(__file__).resolve().parent,tools,ignore=shutil.ignore_patterns("__pycache__"))
            def fixture(folder,name):
                folder.mkdir(parents=True)
                data=png()
                (folder/"front.png").write_bytes(data)
                meta=dict(id=name,name=name,floor="1",version="V01",kind="render",status="制作中",publication_cleared=True,approval_state="NOT_APPROVED",run_id=1,source_sha="a"*40,updated_at="2026-11-24T00:00:00Z",images=[dict(view="front",file="front.png",sha256=hashlib.sha256(data).hexdigest())])
                (folder/"manifest.json").write_text(json.dumps(meta))
            fixture(root/"incoming"/"first","first")
            fixture(root/"other-input"/"second","second")
            ingest(a,root/"incoming")
            ingest(b,root/"other-input")
            git(b,"add",".")
            git(b,"commit","-m","concurrent update")
            git(b,"push","origin","HEAD:3d-progress-data")
            (a/"collection-status.json").write_text('{"result":"success"}')
            result=subprocess.run(["bash",str(tools/"publish_registry.sh")],cwd=a,env={**os.environ,"COLLECTION_RESULT":"success"},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn("rejected",result.stderr)
            self.assertIn("Retry verified gallery collection",result.stdout)
            git(b,"fetch","origin","3d-progress-data")
            models=json.loads(git(b,"show","FETCH_HEAD:index.json"))["models"]
            self.assertEqual({m["id"] for m in models},{"first","second"})
            for model in models:
                path=model["images"][0]["path"]
                git(b,"cat-file","-e","FETCH_HEAD:"+path)
