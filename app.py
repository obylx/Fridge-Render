from flask import Flask, request, jsonify, url_for
from werkzeug.exceptions import BadRequest
import traceback

app = Flask(__name__)
app.url_map.strict_slashes = False  # accept /render and /render/

@app.get("/health")
def health():
    return {"status": "ok", "endpoints": ["POST /render", "GET /video/<job>.mp4"]}

@app.post("/render")
def render_route():
    try:
        j = request.get_json(force=True)
    except BadRequest as e:
        return {"error":"invalid_json","detail":str(e)}, 400

    # tolerate common key variants so one typo doesn’t 500
    voiceover_b64 = (
        j.get("voiceover_b64")
        or j.get("VoiceOver_b64")
        or j.get("voiceOver_b64")
        or j.get("voiceoverB64")
    )
    if not voiceover_b64:
        return {"error":"missing_field","detail":"voiceover_b64 is required"}, 400

    title = j.get("title","Fridge Recipe")
    ingredients = j.get("ingredients", [])
    steps = j.get("steps", [])
    srt = j.get("srt","")
    width = int(j.get("width",1080))
    height = int(j.get("height",1920))

    try:
        job, path = make_video(title, ingredients, steps, voiceover_b64, srt, width, height)
        return {"video_url": url_for("get_video", job=job, _external=True)}
    except Exception as e:
        # print ffmpeg errors to logs so you can see them in Render
        print("RENDER ERROR:\n", traceback.format_exc(), flush=True)
        return {"error":"render_failed","detail":str(e)}, 500
