from werkzeug.exceptions import BadRequest
from flask import request, jsonify, url_for
# ...imports...

@app.post("/render")
def render_route():
    try:
        j = request.get_json(force=True)
    except BadRequest as e:
        return {"error":"invalid_json","detail":str(e)}, 400

    # tolerate common key variants
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

    job, path = make_video(title, ingredients, steps, voiceover_b64, srt, width, height)
    return {"video_url": url_for("get_video", job=job, _external=True)}
