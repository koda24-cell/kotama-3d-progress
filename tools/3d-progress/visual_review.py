"""Advisory CLIP prompt similarity, not artistic approval."""
import argparse
import hashlib
import json
from pathlib import Path

PROMPTS=[
 ("silhouette","a clearly defined coherent silhouette","an indistinct confusing silhouette"),
 ("material","a visually convincing detailed material","a flat visually unconvincing material"),
 ("lighting","a well lit readable 3D object","a dark unreadable 3D object"),
]
def direction(v):
    v=v.lower()
    if any(s in v for s in ("angle","three","斜め","perspective")): return "angle"
    if any(s in v for s in ("front","正面")): return "front"
    if any(s in v for s in ("side","側面","left","right")): return "side"
    return None

def evaluate(root,images,score):
    rows=[]
    for item in images:
        view=direction(item["view"])
        if not view: continue
        path=(root/item["path"]).resolve()
        if not path.is_relative_to(root.resolve()): raise ValueError("Invalid path")
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=item.get("sha256"): raise ValueError("Image hash mismatch")
        rows.append(dict(view=view,sha256=digest,scores=score(path)))
    return dict(views=rows,missing=sorted({"front","side","angle"}-{r["view"] for r in rows}))

def compare(old,new):
    result=[]
    for a in old["views"]:
        matches=[b for b in new["views"] if b["view"]==a["view"]]
        if len(matches)!=1 or sum(b["view"]==a["view"] for b in old["views"])!=1: continue
        b=matches[0]
        result.append(dict(view=a["view"],delta={k:round(b["scores"][k]-v,4) for k,v in a["scores"].items()}))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--limit",type=int,default=3)
    args=p.parse_args()
    import torch
    from PIL import Image
    from transformers import CLIPModel,CLIPProcessor
    model_id="openai/clip-vit-base-patch32"
    model=CLIPModel.from_pretrained(model_id).eval()
    processor=CLIPProcessor.from_pretrained(model_id)
    def score(path):
        with Image.open(path) as im:
            image=im.convert("RGB")
        inputs=processor(text=[t for _,a,b in PROMPTS for t in (a,b)],images=image,return_tensors="pt",padding=True)
        with torch.inference_mode():
            logits=model(**inputs).logits_per_image.reshape(-1,2)
            vals=logits.softmax(dim=1)[:,0].tolist()
        return {k:round(v,4) for (k,_,_),v in zip(PROMPTS,vals)}
    results=[]
    models=json.loads((args.registry/"index.json").read_text())["models"]
    for row in [r for r in models if r.get("images")][:args.limit]:
        current=evaluate(args.registry,row["images"],score)
        old=next((h for h in reversed(row.get("history",[])) if h.get("kind")=="render" and h.get("images")),None)
        previous=evaluate(args.registry,old["images"],score) if old else None
        results.append(dict(id=row["id"],version=row.get("render_version",row["version"]),current=current,previous_version=old["version"] if old else None,previous=previous,comparison=compare(previous,current) if previous else []))
    args.output.write_text(json.dumps(dict(method=model_id,advisory=True,models=results),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
