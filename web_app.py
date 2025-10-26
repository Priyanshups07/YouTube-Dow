
#!/usr/bin/env python3
# Simple local-only Flask app for personal use.
# Do not deploy publicly.
import os
from pathlib import Path
import re
from flask import Flask, render_template_string, request, redirect, url_for, send_file, flash
import shutil

try:
    import yt_dlp as ytdlp
except Exception as e:
    raise SystemExit("yt-dlp is required. Install with: pip install -r requirements.txt")

app = Flask(__name__)
app.secret_key = "local-dev-only"  # for flash messages

TEMPLATE = r'''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Downloader (Local)</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; }
    .card { max-width: 720px; margin: 0 auto; padding: 1.5rem; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 1rem; font-weight: 600; }
    input, select { width: 100%; padding: 0.6rem 0.8rem; border: 1px solid #ddd; border-radius: 10px; }
    button { margin-top: 1.25rem; padding: 0.7rem 1rem; border: 0; border-radius: 12px; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    .note { font-size: 0.9rem; color: #555; margin-top: .5rem; }
    .success { color: #065f46; }
    .error { color: #991b1b; }
  </style>
</head>
<body>
  <div class="card">
    <h2>YouTube Media Downloader <small style="font-size:0.8em;color:#6b7280;">(Local · Personal Use)</small></h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
          {% for category, message in messages %}
            <li class="{{category}}">{{message}}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post" action="{{ url_for('download_route') }}">
      <label for="url">YouTube URL</label>
      <input type="url" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required>

      <label for="dtype">Type</label>
      <select id="dtype" name="dtype">
        <option value="video">Video</option>
        <option value="audio">Audio</option>
      </select>

      <label for="video_format">Video Format</label>
      <select id="video_format" name="video_format">
        <option value="mp4" selected>MP4</option>
        <option value="webm">WebM</option>
      </select>

      <label for="audio_format">Audio Format</label>
      <select id="audio_format" name="audio_format">
        <option value="mp3" selected>MP3</option>
        <option value="m4a">M4A</option>
      </select>

      <label for="quality">Quality</label>
      <select id="quality" name="quality">
        <option value="best">Best</option>
        <option value="1080p">1080p</option>
        <option value="720p">720p</option>
        <option value="480p">480p</option>
        <option value="360p">360p</option>
      </select>

      <label for="filename">Custom Filename (without extension)</label>
      <input type="text" id="filename" name="filename" placeholder="Optional">

      <label for="outdir">Output Directory</label>
      <input type="text" id="outdir" name="outdir" value="downloads">

      <button type="submit">Download</button>
      <div class="note">Use only for personal, authorized content. Comply with YouTube ToS and local laws.</div>
    </form>

    {% if file_ready %}
      <p class="success">Downloaded: <strong>{{ saved_path.name }}</strong></p>
      <a href="{{ url_for('serve_file', path=saved_path.name) }}">Click here to save the file</a>
    {% endif %}
  </div>
</body>
</html>
'''

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def build_format(dtype, vfmt, afmt, quality):
    height_map = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
    h = height_map.get(quality)
    if dtype == "audio":
        return "bestaudio/best"
    if vfmt == "mp4":
        if h is None: return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        return f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}][ext=mp4]/best[height<={h}]"
    else:
        if h is None: return "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"
        return f"bestvideo[height<={h}][ext=webm]+bestaudio[ext=webm]/best[height<={h}][ext=webm]/best[height<={h}]"

def sanitize(name: str) -> str:
    import re
    return re.sub(r'[\\/*?:"<>|]+', "", name).strip()

@app.route("/", methods=["GET"])
def index():
    return render_template_string(TEMPLATE, file_ready=False)

@app.route("/download", methods=["POST"])
def download_route():
    import re
    url = request.form.get("url", "").strip()
    dtype = request.form.get("dtype", "video")
    vfmt = request.form.get("video_format", "mp4")
    afmt = request.form.get("audio_format", "mp3")
    quality = request.form.get("quality", "best")
    filename = request.form.get("filename", "").strip()
    outdir = Path(request.form.get("outdir", "downloads")).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if not re.match(r"^https?://(www\.)?(youtube\.com|youtu\.be)/", url):
        flash("Invalid URL. Provide a YouTube URL.", "error")
        return redirect(url_for("index"))

    outtmpl = str(outdir / ("%s.%%(ext)s" % sanitize(filename))) if filename else str(outdir / "%(title)s [%(id)s].%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": build_format(dtype, vfmt, afmt, quality),
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": vfmt if dtype == "video" else None,
        "postprocessors": [],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
    }

    if dtype == "audio":
        if not check_ffmpeg():
            flash("ffmpeg is required for audio extraction. Install ffmpeg and try again.", "error")
            return redirect(url_for("index"))
        codec = "mp3" if afmt == "mp3" else "m4a"
        ydl_opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": "192"},
            {"key": "FFmpegMetadata", "add_metadata": True},
        ]
    else:
        if check_ffmpeg():
            ydl_opts["postprocessors"] = [{"key": "FFmpegMetadata", "add_metadata": True}]

    saved = None
    try:
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                flash("Failed to download. Video may be private/removed.", "error")
                return redirect(url_for("index"))
            if "requested_downloads" in info and info["requested_downloads"]:
                filename = info["requested_downloads"][0]["_filename"]
            else:
                filename = ydl.prepare_filename(info)
            p = Path(filename)
            if not p.exists():
                candidates = list(p.parent.glob(p.stem + ".*"))
                if candidates:
                    p = candidates[0]
            saved = p
    except ytdlp.utils.DownloadError as e:
        flash(f"Download error: {e}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Unexpected error: {e}", "error")
        return redirect(url_for("index"))

    return render_template_string(TEMPLATE, file_ready=True, saved_path=saved)

@app.route("/files/<path:path>")
def serve_file(path):
    base = Path("downloads").resolve()
    p = base.parent / path  # allow any directory used in UI
    if p.exists():
        return send_file(p, as_attachment=True, download_name=p.name)
    else:
        return "Not found", 404

if __name__ == "__main__":
    print("Starting local Web UI at http://127.0.0.1:8080/")
    print("Use only for personal, authorized content. Comply with YouTube ToS and local laws.")
    app.run(debug=False, port=8080)
