# YouTube Downloader

A simple local-only Flask web application for downloading YouTube videos and audio.

## Features
- Download YouTube videos in various formats (MP4, WebM)
- Extract audio in MP3 or M4A format
- Select quality options (Best, 1080p, 720p, 480p, 360p)
- Custom filename support
- Local use only - not intended for public deployment

## Requirements
- Python 3.x
- Flask
- yt-dlp
- ffmpeg (for audio extraction)

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python web_app.py`

## Usage
1. Run the Flask application
2. Open your browser to http://127.0.0.1:8080
3. Enter a YouTube URL
4. Select download options
5. Click Download

## Disclaimer
This tool is for personal, authorized content downloading only. Users must comply with YouTube's Terms of Service and local laws.