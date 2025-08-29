"""
scripts/precache_wiki.py
Purpose: Pre-fetch and store a few Wikipedia pages for **offline demo** safety.
What to implement:
- Given a list of page names, download and save first paragraph to data/cache/.
Implementation notes:
- Retrieval falls back to this cache (and seed_kb) if internet is flaky.
"""
import os, argparse, json
from pathlib import Path

def main(pages):
    cache_dir = Path(__file__).resolve().parents[1] / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        import wikipedia
        wikipedia.set_lang("en")
        for name in pages:
            try:
                page = wikipedia.page(name, auto_suggest=False)
                text = page.content.split("\n")[0]
                out = {"title": page.title, "url": page.url, "snippet": text}
                (cache_dir / f"{page.title}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                print("cached:", page.title)
            except Exception as e:
                print("skip:", name, e)
    except Exception:
        print("wikipedia lib not available or offline; write placeholders")
        for name in pages:
            out = {"title": name, "url": "", "snippet": f"(offline placeholder) {name} facts."}
            (cache_dir / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+", required=True)
    args = ap.parse_args()
    main(args.pages)
