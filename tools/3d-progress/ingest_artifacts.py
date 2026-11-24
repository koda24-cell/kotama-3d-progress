"""Discover and validate gallery manifests inside extracted workflow artifacts."""
import json, sys
from pathlib import Path
from register import register

def ingest(registry, incoming):
    manifests=sorted(incoming.rglob("manifest.json"))
    results=[]
    for manifest in manifests:
        folder=manifest.parent
        try:
            meta=json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(meta,dict): raise ValueError("Invalid manifest")
        except (ValueError, UnicodeError):
            results.append(("unknown","quarantined:invalid-manifest")); continue
        if meta.get("id","").startswith(("gallery-test-","design-engine-test-")):
            results.append((meta["id"],"skipped:test-fixture")); continue
        if meta.get("publication_cleared") is not True:
            results.append((meta.get("id","unknown"),"skipped:no-publication-clearance")); continue
        if meta.get("approval_state") not in ("NOT_APPROVED","APPROVED"):
            results.append((meta.get("id","unknown"),"quarantined:approval")); continue
        try:
            changed=register(registry,meta,folder)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            results.append((meta.get("id","unknown"),"quarantined:"+type(exc).__name__)); continue
        results.append((meta["id"],"updated" if changed else "unchanged"))
    return results

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: ingest_artifacts.py REGISTRY_ROOT INCOMING_ROOT")
    for model,status in ingest(Path(sys.argv[1]),Path(sys.argv[2])): print(model,status)
