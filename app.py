from flask import Flask, request, jsonify, send_file, url_for
from render import make_video
import os

app = Flask(__name__)

@app.post("/render")
def render_route():
    j = request.get_json(force=True)
    title = j.get("title","Fridge Recipe")
    ingredients = j.get("ingredients", [])
    steps = j.get("steps", [])
    voiceover_b64 = j["voiceover_b64"]
    srt = j.get("srt", "")
    width = int(j.get("width",1080))
    height = int(j.get("height",1920))

    job, path = make_video(title, ingredients, steps, voiceover_b64, srt, width, height)
    video_url = url_for("get_video", job=job, _external=True)
    return jsonify({"video_url": video_url})

@app.get("/video/<job>.mp4")
def get_video(job):
    path = f"/tmp/vids/{job}.mp4"
    if not os.path.exists(path):
        return {"error":"not found"}, 404
    return send_file(path, mimetype="video/mp4", as_attachment=False)

# render.com will run via gunicorn
