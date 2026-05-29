#!/usr/bin/env python3
"""
server.py — Local dev + admin server for THT Orchid Farm

Usage:
    ANTHROPIC_API_KEY=sk-... python3 server.py

    Site:   http://localhost:8000/
    Admin:  http://localhost:8000/admin.html
"""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

REPO          = Path(__file__).parent
DRAFTS_DIR    = REPO / "drafts"
IMAGES_DIR    = REPO / "images"
VARIETIES_JSON    = REPO / "varieties.json"
TRANSLATIONS_JSON = REPO / "translations.json"
FILL_OPTIONS  = {"fill-blush", "fill-white", "fill-purple", "fill-yellow", "fill-striped"}

DRAFTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


# ── Static file serving ───────────────────────────────────────────────────────

@app.route("/")
def root():
    return send_from_directory(REPO, "index.html")

@app.route("/drafts/<code>/photo.jpg")
def draft_photo(code):
    photo = DRAFTS_DIR / code.upper() / "photo.jpg"
    if not photo.exists():
        abort(404)
    return send_from_directory(DRAFTS_DIR / code.upper(), "photo.jpg")

@app.route("/<path:path>")
def static_serve(path):
    return send_from_directory(REPO, path)


# ── API: generate descriptions ────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY environment variable is not set."}), 500

    code = request.form.get("code", "").strip().upper()
    if not code:
        return jsonify({"error": "Species code is required."}), 400

    image_file = request.files.get("image")
    if not image_file:
        return jsonify({"error": "Image file is required."}), 400

    suffix = Path(image_file.filename).suffix.lower() or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        image_file.save(tmp_path)

    draft_dir = DRAFTS_DIR / code
    draft_dir.mkdir(exist_ok=True)
    photo_path = draft_dir / "photo.jpg"

    try:
        result = subprocess.run(
            ["sips", "-Z", "1200", "--setProperty", "formatOptions", "85",
             str(tmp_path), "--out", str(photo_path)],
            capture_output=True
        )
        if result.returncode != 0:
            return jsonify({"error": f"Image resize failed: {result.stderr.decode()}"}), 500
    finally:
        tmp_path.unlink(missing_ok=True)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        with open(photo_path, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()

        prompt = f"""You are writing product copy for THT Orchid Farm, a family-owned phalaenopsis orchid farm in Đơn Dương, Vietnam.

Variety code: {code}

Analyse this orchid photo and return ONLY a valid JSON object — no markdown fences, no extra text:

{{
  "suggested_name_en": "Short poetic English subtitle, 2–3 words. Example: 'Pink Cascade'. No code prefix.",
  "suggested_name_vi": "Natural Vietnamese translation. Example: 'Thác Hồng'.",
  "shortDesc": "1–2 sentences. Lead with petal colour/pattern, note the lip colour. End with '[POT] pot.' as a literal placeholder. Under 30 words total.",
  "longDesc": "3–4 sentences. Colour, pattern, unique visual traits, growing performance. Elegant and precise — no exclamation marks.",
  "shortDesc_vi": "Same content as shortDesc in natural Vietnamese. Keep [POT] as a literal placeholder.",
  "longDesc_vi": "Same content as longDesc in natural Vietnamese.",
  "fill": "Closest match from exactly: fill-blush fill-white fill-purple fill-yellow fill-striped"
}}"""

        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1200,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        ai = json.loads(raw)
    except Exception as exc:
        return jsonify({"error": f"Claude error: {exc}"}), 500

    fill = ai.get("fill", "fill-blush")
    if fill not in FILL_OPTIONS:
        fill = "fill-blush"

    return jsonify({
        "code": code,
        "suggested_name_en": ai.get("suggested_name_en", ""),
        "suggested_name_vi": ai.get("suggested_name_vi", ""),
        "shortDesc":    ai.get("shortDesc", ""),
        "longDesc":     ai.get("longDesc", ""),
        "shortDesc_vi": ai.get("shortDesc_vi", ""),
        "longDesc_vi":  ai.get("longDesc_vi", ""),
        "fill": fill,
    })


# ── API: save draft ───────────────────────────────────────────────────────────

@app.route("/api/save-draft", methods=["POST"])
def api_save_draft():
    data = request.get_json(force=True)
    code = (data.get("id") or "").strip().upper()
    if not code:
        return jsonify({"error": "id is required."}), 400

    draft_dir = DRAFTS_DIR / code
    if not (draft_dir / "photo.jpg").exists():
        return jsonify({"error": f"No photo found for {code}. Please generate first."}), 400

    pot = data.get("pot") or '5"'
    for key in ("shortDesc", "shortDesc_vi"):
        if isinstance(data.get(key), str):
            data[key] = data[key].replace("[POT]", pot)

    data["id"]          = code
    data["image"]       = f"images/{code}.jpg"
    data["species"]     = data.get("species") or "Phalaenopsis hybrid"
    data["light"]       = data.get("light")   or "Bright indirect"
    data["care"]        = data.get("care")     or "Beginner-friendly"
    data["watering"]    = data.get("watering") or "Every 7–10 days"
    data["temperature"] = data.get("temperature") or "18–28 °C"

    with open(draft_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return jsonify({"ok": True})


# ── API: list drafts ──────────────────────────────────────────────────────────

@app.route("/api/drafts", methods=["GET"])
def api_list_drafts():
    result = []
    if DRAFTS_DIR.exists():
        for d in sorted(DRAFTS_DIR.iterdir()):
            data_file = d / "data.json"
            if d.is_dir() and data_file.exists():
                with open(data_file, encoding="utf-8") as f:
                    result.append(json.load(f))
    return jsonify(result)


# ── API: publish draft ────────────────────────────────────────────────────────

@app.route("/api/publish/<code>", methods=["POST"])
def api_publish(code):
    code = code.upper()
    draft_dir  = DRAFTS_DIR / code
    data_file  = draft_dir / "data.json"
    photo_src  = draft_dir / "photo.jpg"

    if not data_file.exists() or not photo_src.exists():
        return jsonify({"error": f"Draft for {code} not found."}), 404

    with open(data_file, encoding="utf-8") as f:
        entry = json.load(f)

    worktree = REPO.parent / f"_tht_publish_{code.lower()}"

    # Clean up any leftover worktree from a previous failed attempt
    if worktree.exists():
        subprocess.run(["git", "worktree", "remove", str(worktree), "--force"],
                       cwd=REPO, capture_output=True)

    try:
        subprocess.run(["git", "fetch", "origin", "master"],
                       check=True, cwd=REPO, capture_output=True)
        subprocess.run(["git", "worktree", "add", str(worktree), "origin/master"],
                       check=True, cwd=REPO, capture_output=True)

        # Copy image into worktree
        wt_images = worktree / "images"
        wt_images.mkdir(exist_ok=True)
        shutil.copy2(photo_src, wt_images / f"{code}.jpg")

        # Update varieties.json
        wt_varieties = worktree / "varieties.json"
        with open(wt_varieties, encoding="utf-8") as f:
            varieties = json.load(f)
        varieties = [v for v in varieties if v["id"] != code]
        varieties.insert(0, entry)
        with open(wt_varieties, "w", encoding="utf-8") as f:
            json.dump(varieties, f, indent=2, ensure_ascii=False)

        # Update translations.json
        wt_trans = worktree / "translations.json"
        with open(wt_trans, encoding="utf-8") as f:
            translations = json.load(f)
        translations["en"][f"variety.{code}.name"]      = entry.get("name", "")
        translations["en"][f"variety.{code}.shortDesc"] = entry.get("shortDesc", "")
        translations["vi"][f"variety.{code}.name"]      = entry.get("name_vi", "")
        translations["vi"][f"variety.{code}.shortDesc"] = entry.get("shortDesc_vi", "")
        with open(wt_trans, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)

        def git(*args):
            r = subprocess.run(["git"] + list(args), cwd=worktree,
                                capture_output=True, check=True)
            return r

        git("add", f"images/{code}.jpg", "varieties.json", "translations.json")
        git("commit", "-m", f"Add variety {code} – {entry.get('name', code)}")
        git("push", "origin", "HEAD:master")

    except subprocess.CalledProcessError as exc:
        return jsonify({"error": exc.stderr.decode().strip() or str(exc)}), 500
    finally:
        subprocess.run(["git", "worktree", "remove", str(worktree), "--force"],
                       cwd=REPO, capture_output=True)

    shutil.rmtree(draft_dir, ignore_errors=True)
    return jsonify({"ok": True, "code": code, "name": entry.get("name", code)})


# ── API: delete draft ─────────────────────────────────────────────────────────

@app.route("/api/drafts/<code>", methods=["DELETE"])
def api_delete_draft(code):
    draft_dir = DRAFTS_DIR / code.upper()
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
    return jsonify({"ok": True})


# ── API: remove published variety ─────────────────────────────────────────────

@app.route("/api/remove/<code>", methods=["POST"])
def api_remove(code):
    code = code.upper()
    worktree = REPO.parent / f"_tht_remove_{code.lower()}"

    if worktree.exists():
        subprocess.run(["git", "worktree", "remove", str(worktree), "--force"],
                       cwd=REPO, capture_output=True)

    try:
        subprocess.run(["git", "fetch", "origin", "master"],
                       check=True, cwd=REPO, capture_output=True)
        subprocess.run(["git", "worktree", "add", str(worktree), "origin/master"],
                       check=True, cwd=REPO, capture_output=True)

        # Remove from varieties.json
        wt_varieties = worktree / "varieties.json"
        with open(wt_varieties, encoding="utf-8") as f:
            varieties = json.load(f)
        before = len(varieties)
        varieties = [v for v in varieties if v["id"] != code]
        if len(varieties) == before:
            return jsonify({"error": f"{code} not found in varieties.json"}), 404

        with open(wt_varieties, "w", encoding="utf-8") as f:
            json.dump(varieties, f, indent=2, ensure_ascii=False)

        # Remove translation keys
        wt_trans = worktree / "translations.json"
        with open(wt_trans, encoding="utf-8") as f:
            translations = json.load(f)
        for lang in ("en", "vi"):
            translations[lang].pop(f"variety.{code}.name", None)
            translations[lang].pop(f"variety.{code}.shortDesc", None)
        with open(wt_trans, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)

        # Remove image
        img = worktree / "images" / f"{code}.jpg"
        if img.exists():
            img.unlink()

        def git(*args):
            return subprocess.run(["git"] + list(args), cwd=worktree,
                                   capture_output=True, check=True)

        git("add", "-A")
        git("commit", "-m", f"Remove variety {code}")
        git("push", "origin", "HEAD:master")

    except subprocess.CalledProcessError as exc:
        return jsonify({"error": exc.stderr.decode().strip() or str(exc)}), 500
    finally:
        subprocess.run(["git", "worktree", "remove", str(worktree), "--force"],
                       cwd=REPO, capture_output=True)

    return jsonify({"ok": True, "code": code})


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  THT Orchid Farm — Local Server")
    print(f"  Site:   http://localhost:{port}/")
    print(f"  Admin:  http://localhost:{port}/admin.html\n")
    app.run(host="127.0.0.1", port=port, debug=False)
