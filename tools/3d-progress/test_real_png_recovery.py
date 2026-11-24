import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from ingest_artifacts import ingest

def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))

def png():
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",1,1,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(b"\x00\xff\x00\x00"))+chunk(b"IEND",b"")

class RealPNGRecovery(unittest.TestCase):
    def test_corrupt_then_valid(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            registry=root/"registry"
            registry.mkdir()
            (registry/"index.json").write_text('{"models":[]}')
            incoming=root/"incoming"
            for name in ("a-corrupt","b-valid"):
                folder=incoming/name
                folder.mkdir(parents=True)
                data=png()
                if name=="a-corrupt": data=data[:-3]
                (folder/"front.png").write_bytes(data)
                meta=dict(id=name,name=name,floor="1",version="V01",kind="render",status="制作中",publication_cleared=True,approval_state="NOT_APPROVED",run_id=1,source_sha="a"*40,updated_at="2026-11-24T00:00:00Z",images=[dict(view="front",file="front.png",sha256=hashlib.sha256(data).hexdigest())])
                (folder/"manifest.json").write_text(json.dumps(meta))
            self.assertEqual(ingest(registry,incoming),[("a-corrupt","quarantined:ValueError"),("b-valid","updated")])
            models=json.loads((registry/"index.json").read_text())["models"]
            self.assertEqual([m["id"] for m in models],["b-valid"])
            self.assertFalse((registry/"renders"/"a-corrupt").exists())
            self.assertEqual(len(list((registry/"renders").rglob("*.png"))),1)
