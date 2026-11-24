import argparse,hashlib,json,re
from pathlib import Path
from register import register

# Only first-party reference models explicitly cleared for publication.
MODELS={"blue_wisp_torch":("b1-blue-wisp-torch","Blue wisp torch"),"mod_floor_stone_4m":("b1-mod-floor-stone-4m","Stone floor 4m")}
def ingest(source,registry,run,sha,stamp):
    count=0
    for manifest in sorted(source.rglob("manifest.json")):
        folder=manifest.parent
        if folder.parent.name not in MODELS:continue
        model,name=MODELS[folder.parent.name]
        data=json.loads(manifest.read_text())
        if data["version"]!=folder.name or not re.fullmatch("[0-9a-f]{16}",folder.name):raise ValueError("version")
        images=[]
        for file,digest in sorted(data["files"].items()):
            if not re.fullmatch(r"(part-[0-9]+|exploded)\.png",file):continue
            p=folder/file
            if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError("hash mismatch")
            images.append({"file":file,"view":p.stem,"sha256":digest})
        if not images:raise ValueError("no drawings")
        count+=register(registry,{"id":model,"name":name,"floor":"第1層","version":folder.name,"run_id":run,"source_sha":sha,"updated_at":stamp,"publication_cleared":True,"status":"設計中","approval_state":"NOT_APPROVED","kind":"design","images":images},folder)
    return count
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path);p.add_argument("registry",type=Path);p.add_argument("run",type=int);p.add_argument("sha");p.add_argument("stamp")
    a=p.parse_args();print("updated",ingest(a.source,a.registry,a.run,a.sha,a.stamp))
