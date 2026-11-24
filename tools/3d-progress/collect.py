"""Collect only source-repository artifacts with verified run provenance."""
import json, subprocess, time, re, os
from pathlib import Path
REPO="koda24-cell/kotama-no-bouken"
def gh(*args):
    for attempt in range(3):
        p=subprocess.run(["gh",*args],capture_output=True,text=True)
        if p.returncode==0: return p.stdout
        if attempt<2: time.sleep(2**attempt)
    raise RuntimeError("GitHub request failed: "+args[0])
def api(path):
    return json.loads(gh("api",path))
def collect(root, selected=""):
    root.mkdir(parents=True,exist_ok=True)
    if selected and not selected.isdecimal(): raise ValueError("Invalid run ID")
    if selected:
        runs=[api(f"repos/{REPO}/actions/runs/{selected}")]
        artifacts=api(f"repos/{REPO}/actions/runs/{selected}/artifacts?per_page=100")["artifacts"]
    else:
        artifacts=[]
        for page in range(1,11):
            batch=api(f"repos/{REPO}/actions/artifacts?per_page=100&page={page}")["artifacts"]
            artifacts.extend(batch)
            if len(batch)<100: break
    for a in artifacts:
        if a["expired"] or not re.fullmatch(r"gallery-production-[0-9]+[a-zA-Z0-9_-]*",a["name"]): continue
        if a["size_in_bytes"]>100_000_000: raise ValueError("Artifact too large")
        rid=a["workflow_run"]["id"]
        run=api(f"repos/{REPO}/actions/runs/{rid}")
        if run["conclusion"]!="success" or run["head_repository"]["full_name"]!=REPO: continue
        folder=root/str(rid)/str(a["id"])
        folder.mkdir(parents=True,exist_ok=True)
        gh("run","download",str(rid),"-R",REPO,"--name",a["name"],"--dir",str(folder))
        for p in folder.rglob("manifest.json"):
            m=json.loads(p.read_text())
            if m["run_id"]!=rid: raise ValueError("Run mismatch")
            sha=m["source_sha"]
            if not re.fullmatch(r"[0-9a-f]{40}",sha): raise ValueError("Invalid SHA")
            if sha!=run["head_sha"]:
                commit=api(f"repos/{REPO}/commits/{sha}")
                if run["event"]!="pull_request" or run["head_sha"] not in [x["sha"] for x in commit["parents"]]: raise ValueError("Commit mismatch")
            if m.get("approval_state")!="NOT_APPROVED": raise ValueError("Automatic approval forbidden")
            if any(not re.fullmatch(r"[0-9a-f]{64}",i.get("sha256","")) for i in m["images"]): raise ValueError("Missing image digest")
if __name__=="__main__":
    collect(Path("incoming"),os.environ.get("SOURCE_RUN_ID",""))
