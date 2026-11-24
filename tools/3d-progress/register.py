"""Validated, append-only version registry for reviewed gallery assets."""
import argparse, hashlib, json, os, re, shutil, struct, zlib
from pathlib import Path
from datetime import datetime, timezone

STATUSES = ("設計中", "制作中", "承認待ち", "完成")
APPROVALS = ("NOT_APPROVED", "APPROVED")
KINDS = ("design", "progress", "render")

def png_check(p):
    data=p.read_bytes()
    if len(data)>20_000_000 or data[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError("Invalid PNG")
    pos=8; first=True; seen_data=False
    while pos+12<=len(data):
        n,kind=struct.unpack_from(">I4s",data,pos); end=pos+12+n
        if end>len(data) or zlib.crc32(data[pos+4:end-4])!=struct.unpack_from(">I",data,end-4)[0]:
            raise ValueError("PNG CRC/length")
        if first:
            if kind!=b'IHDR' or n!=13: raise ValueError("PNG header")
            w,h=struct.unpack_from(">II",data,pos+8)
            if not 0<w<=8192 or not 0<h<=8192: raise ValueError("PNG dimensions")
            first=False
        if kind==b'IDAT': seen_data=True
        if kind==b'IEND' and n==0 and end==len(data) and seen_data:
            return hashlib.sha256(data).hexdigest()
        pos=end
    raise ValueError("Incomplete PNG")

def register(root, meta, source):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}",meta["id"]): raise ValueError("Invalid id")
    if meta.get("publication_cleared") is not True: raise ValueError("Publication clearance required")
    if meta.get("status") not in STATUSES: raise ValueError("Invalid status")
    if meta.get("approval_state","NOT_APPROVED") not in APPROVALS: raise ValueError("Invalid approval_state")
    if meta.get("kind","render") not in KINDS: raise ValueError("Invalid kind")
    for k in ("name","floor","version"):
        if not isinstance(meta.get(k),str) or not meta[k]: raise ValueError(k)
    if type(meta.get("run_id")) is not int or meta["run_id"]<=0: raise ValueError("run_id")
    if not re.fullmatch(r"[0-9a-f]{40}",meta.get("source_sha","")): raise ValueError("source_sha")
    stamp=datetime.fromisoformat(meta["updated_at"].replace("Z","+00:00"))
    if stamp.tzinfo is None: raise ValueError("Timezone required")
    stamp=stamp.astimezone(timezone.utc).isoformat()
    index=root/"index.json"; data=json.loads(index.read_text(encoding="utf-8"))
    old=next((x for x in data["models"] if x["id"]==meta["id"]),None)
    kind=meta.get("kind","render"); field={"design":"designs","progress":"progress_images","render":"images"}[kind]
    previous=(old or {}).get(kind+"_updated_at")
    if not previous and kind=="render" and old and old.get("images"): previous=old["updated_at"]
    if previous and datetime.fromisoformat(previous)>=datetime.fromisoformat(stamp): return False
    prepared=[]
    for v in meta["images"]:
        p=(source/v["file"]).resolve()
        if not p.is_relative_to(source.resolve()) or not p.is_file(): raise ValueError("Invalid source")
        digest=png_check(p)
        if v.get("sha256") is not None and v["sha256"]!=digest: raise ValueError("Manifest image hash mismatch")
        path=f"renders/{meta['id']}/{digest}.png"
        prepared.append((p,path,{"view":v["view"],"path":path,"sha256":digest}))
    if not prepared: raise ValueError("No images")
    # Validate every input before mutating the registry or copying any files.
    row=dict(old or {})
    versions=list(row.get("history",[]))
    if previous:
        versions.append({
            "kind":kind,"version":row.get(kind+"_version",row.get("version")),
            "updated_at":previous,"run_id":row.get(kind+"_run_id",row.get("run_id")),
            "source_sha":row.get(kind+"_source_sha",row.get("source_sha")),
            "images":row.get(field,[]),"approval_state":row.get(kind+"_approval_state",row.get("approval_state","NOT_APPROVED"))
        })
    for p,path,_ in prepared:
        dest=root/path; dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists(): shutil.copyfile(p,dest)
        elif hashlib.sha256(dest.read_bytes()).hexdigest()!=Path(path).stem: raise ValueError("Stored image hash mismatch")
    row.update({"id":meta["id"],"name":meta["name"],"floor":meta["floor"]})
    row.setdefault("images",[]); row.setdefault("designs",[]); row.setdefault("progress_images",[])
    row[field]=[v for _,_,v in prepared]
    row[kind+"_updated_at"]=stamp; row[kind+"_version"]=meta["version"]
    row[kind+"_source_sha"]=meta["source_sha"]; row[kind+"_run_id"]=meta["run_id"]
    row[kind+"_approval_state"]=meta.get("approval_state","NOT_APPROVED")
    row["history"]=versions
    # The canonical card fields follow the newest render, never a design/progress upload.
    if kind=="render" or not row.get("version"):
        row.update({"version":meta["version"],"status":meta["status"],"run_id":meta["run_id"],"source_sha":meta["source_sha"]})
    row["approval_state"]=row.get("render_approval_state",meta.get("approval_state","NOT_APPROVED"))
    row["updated_at"]=max(stamp,row.get("updated_at",stamp))
    data["models"]=[x for x in data["models"] if x["id"]!=row["id"]]+[row]
    tmp=index.with_suffix(".tmp"); tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,index); return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--registry",type=Path,required=True); p.add_argument("--manifest",type=Path,required=True); p.add_argument("--source",type=Path,required=True)
    a=p.parse_args()
    print("updated" if register(a.registry,json.loads(a.manifest.read_text(encoding="utf-8")),a.source) else "unchanged")
