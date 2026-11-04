"""Bulk-attach item photos.

Put your image files in  backend/photos/  named after the item, e.g.:
    Chicken Burger.jpg
    تشكن برغر.png
    Big Hanks Burger.webp
Then run from the backend/ folder:
    .venv\\Scripts\\python import_photos.py          (preview: what matches what)
    .venv\\Scripts\\python import_photos.py --apply  (actually attach them)

Matching is by item name (English OR Arabic), case/space/punctuation-insensitive.
Each matched image is copied into the website's img/uploads/ folder and set as
that item's photo. Unmatched files are listed so you can rename and re-run.
"""
import argparse
import re
import shutil
import sys
import uuid

from sqlalchemy import select

from app.config import UI_DIR
from app.database import SessionLocal
from app.models import Product

PHOTOS_DIR = UI_DIR / "backend" / "photos"
UPLOADS_DIR = UI_DIR / "img" / "uploads"
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def norm(s: str) -> str:
    """Lowercase, drop punctuation/brackets and Arabic diacritics, collapse spaces."""
    s = (s or "").lower().strip()
    s = re.sub(r"[ً-ْٰ]", "", s)       # Arabic short vowels/diacritics
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"[^\w؀-ۿ]+", " ", s)         # keep letters/digits/Arabic, rest -> space
    return re.sub(r"\s+", " ", s).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually attach (otherwise just preview)")
    args = ap.parse_args()

    if not PHOTOS_DIR.exists():
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created {PHOTOS_DIR}. Put your item photos there (named after each item) and run again.")
        return

    files = [f for f in sorted(PHOTOS_DIR.iterdir()) if f.suffix.lower() in ALLOWED]
    if not files:
        print(f"No images found in {PHOTOS_DIR}. Add .jpg/.png/.webp/.gif files named after items.")
        return

    db = SessionLocal()
    try:
        products = db.scalars(select(Product)).all()
        # name -> list of products (so we can flag ambiguous names)
        by_name: dict[str, list[Product]] = {}
        for p in products:
            for nm in (p.name_en, p.name_ar):
                k = norm(nm)
                if k:
                    by_name.setdefault(k, []).append(p)

        matched, ambiguous, unmatched = [], [], []
        for f in files:
            key = norm(f.stem)
            hits = by_name.get(key)
            if not hits:  # fall back to a unique "contains" match
                cand = [p for p in products if key and (key in norm(p.name_en) or key in norm(p.name_ar)
                                                        or norm(p.name_en) in key or norm(p.name_ar) in key)]
                hits = cand if len(cand) == 1 else (cand or None)
            if not hits:
                unmatched.append(f.name)
            elif len(hits) > 1:
                ambiguous.append((f.name, [h.name_en or h.name_ar for h in hits]))
            else:
                matched.append((f, hits[0]))

        print(f"\n{len(matched)} matched, {len(ambiguous)} ambiguous, {len(unmatched)} unmatched "
              f"(of {len(files)} images; {len(products)} items).\n")
        for f, p in matched:
            print(f"  [match] {f.name}  ->  {p.name_en or p.name_ar}")
        for name, opts in ambiguous:
            print(f"  [AMBIGUOUS] {name}  ->  several items: {', '.join(opts)} (rename the file more specifically)")
        for name in unmatched:
            print(f"  [no item]  {name}  (rename it to exactly match an item name)")

        if not args.apply:
            print("\nPreview only. Re-run with  --apply  to attach the matched photos.")
            return

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        for f, p in matched:
            dest_name = f"{uuid.uuid4().hex}{f.suffix.lower()}"
            shutil.copyfile(f, UPLOADS_DIR / dest_name)
            p.image_url = f"/img/uploads/{dest_name}"
        db.commit()
        print(f"\nAttached {len(matched)} photos.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
