import base64, os, uuid, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUT_DIR = "/tmp/vids"

def _wrap(draw, text, font, max_w, margin=80):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) <= (max_w - 2*margin):
            line = test
        else:
            lines.append(line); line = w
    lines.append(line)
    return lines

def _card(title, body_lines, w, h):
    img = Image.new("RGB", (w, h), (12, 14, 16))
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(FONT_PATH, 72)
    fb = ImageFont.truetype(FONT_PATH, 46)
    y = 100
    if title:
        d.text((80, y), title, font=ft, fill=(240, 240, 240))
        y += 140
    for ln in body_lines:
        for l in textwrap.wrap(ln, width=48):
            d.text((80, y), l, font=fb, fill=(230, 230, 230))
            y += 66
    return img

def make_video(title, ingredients, steps, voiceover_b64, srt_text, width=1080, height=1920):
    os.makedirs(OUT_DIR, exist_ok=True)
    job = uuid.uuid4().hex
    work = f"/tmp/{job}"; os.makedirs(work, exist_ok=True)

    # 1) write voiceover
    vo_path = f"{work}/vo.mp3"
    with open(vo_path, "wb") as f:
        f.write(base64.b64decode(voiceover_b64))

    # 2) build cards
    # Title
    _card(title, ["Quick fridge recipe"], width, height).save(f"{work}/card_00.png")

    # Ingredients
    ing_lines = ["Ingredients:"] + ingredients
    _card("", ing_lines, width, height).save(f"{work}/card_01.png")

    # Steps (one card per step)
    for i, step in enumerate(steps, start=2):
        _card(f"Step {i-1}", [step], width, height).save(f"{work}/card_{i:02d}.png")

    # 3) slideshow manifest (per-card durations)
    durations = [2.5, 4.0] + [3.5]*len(steps)
    with open(f"{work}/list.txt", "w") as f:
        for i, d in enumerate(durations):
            f.write(f"file 'card_{i:02d}.png'\n")
            f.write(f"duration {d}\n")
        f.write(f"file 'card_{len(durations)-1:02d}.png'\n")  # repeat last frame

    # 4) optional captions
    srt_path = f"{work}/captions.srt"
    vf = "format=yuv420p"
    if srt_text and srt_text.strip():
        with open(srt_path, "w") as f:
            f.write(srt_text)
        # escape quotes in path for ffmpeg
        srt_escaped = srt_path.replace("'", r"'\''")
        vf = f"subtitles='{srt_escaped}',format=yuv420p"

    # 5) render with ffmpeg
    out_path = f"{OUT_DIR}/{job}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt",
        "-i", vo_path,
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        out_path
    ]
    subprocess.run(cmd, check=True)
    return job, out_path
