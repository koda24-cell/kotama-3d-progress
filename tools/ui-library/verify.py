import json
from pathlib import Path
import sys

from PIL import Image

root = Path(sys.argv[1])
rows = json.loads(Path("ui-library/manifest.json").read_text())["assets"]
checked = 0
for row in rows:
    parts = [row, *row.get("variants", {}).values()]
    parts.extend(row[key] for key in ("fill", "frame") if key in row)
    for part in parts:
        png = (root / part["path"]).with_suffix(".png")
        with Image.open(png) as image:
            alpha = image.convert("RGBA").getchannel("A")
            assert list(image.size) == row["size"], png
            lo, hi = alpha.getextrema()
            assert lo == 0 and hi > 192 and png.stat().st_size < 150_000, png
            checked += 1
print(f"{len(rows)} designs and {checked} transparent PNG exports verified")
