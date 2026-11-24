import tempfile,json,hashlib,struct,zlib
from pathlib import Path
from import_design import ingest

def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack(">IIBBBBB",1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff'))+chunk(b'IEND',b'')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp); registry=root/"registry";registry.mkdir()
    (registry/"index.json").write_text('{"models":[]}')
    source=root/"incoming";folder=source/"blue_wisp_torch"/"0123456789abcdef";folder.mkdir(parents=True)
    (folder/"part-000.png").write_bytes(png)
    manifest={"version":folder.name,"files":{"part-000.png":hashlib.sha256(png).hexdigest()}}
    (folder/"manifest.json").write_text(json.dumps(manifest))
    args=(source,registry,123,"a"*40,"2026-11-24T00:00:00Z")
    assert ingest(*args)==1
    assert ingest(*args)==0
    row=json.loads((registry/"index.json").read_text())["models"][0]
    assert row["designs"] and row["design_approval_state"]=="NOT_APPROVED"
    manifest["files"]["part-000.png"]="0"*64
    (folder/"manifest.json").write_text(json.dumps(manifest))
    try: ingest(*args)
    except ValueError: pass
    else: raise AssertionError("bad hash accepted")
print("Import smoke passed")
