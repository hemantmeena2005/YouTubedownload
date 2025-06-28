# app.py
from flask import Flask, request, send_file, jsonify, Response, stream_with_context
import yt_dlp
import zipfile
import os
import uuid
import shutil
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
if not os.path.exists('temp'):
    os.makedirs('temp')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    # ✨ NEW: Get the format from the frontend, default to 'm4a' for speed
    audio_format = data.get('format', 'm4a')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    download_id = str(uuid.uuid4())
    temp_dir = os.path.join('temp', download_id)
    os.makedirs(temp_dir, exist_ok=True)

    def generate_and_download():
        
        # ✨ NEW: Dynamic YDL options based on user's choice
        ydl_opts = {}
        if audio_format == 'mp3':
            yield "Mode: Compatible (MP3). Conversion will be slower.\n"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128', # Hardcoded for speed as requested
                }],
                'ignoreerrors': True,
                'noplaylist': False,
                'quiet': True,
            }
        else: # Default to m4a
            yield "Mode: Fastest (M4A). Skipping conversion.\n"
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'ignoreerrors': True,
                'noplaylist': False,
                'quiet': True,
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = info.get('entries', [info])
                total = len(entries)
                yield f"Found {total} videos. Starting download...\n\n"
                
                ydl.download([url])

            yield "\nZipping files... this might take a moment.\n"
            
            zip_path = os.path.join('temp', f"{download_id}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # ✨ CHANGED: Zip any audio file, not just .mp3
                for file in os.listdir(temp_dir):
                    # This is more robust and zips whatever yt-dlp created
                    zipf.write(os.path.join(temp_dir, file), arcname=file)
                    yield f"Zipped: {file}\n"

            yield f"\nZip file created successfully.\n"

        except Exception as e:
            logging.error(f"Error during download/zip for {download_id}: {e}")
            yield f"💥 An unexpected error occurred: {e}\n"
        finally:
            yield f"ALL_DONE:{download_id}\n"

    return Response(stream_with_context(generate_and_download()), mimetype='text/plain')


@app.route('/get_zip/<download_id>')
def get_zip(download_id):
    if not all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in download_id):
        return jsonify({'error': 'Invalid download ID'}), 400

    zip_path = os.path.join('temp', f"{download_id}.zip")
    temp_dir = os.path.join('temp', download_id)

    if not os.path.exists(zip_path):
        return jsonify({'error': 'File not found or already deleted.'}), 404
        
    def stream_and_cleanup():
        try:
            with open(zip_path, 'rb') as f:
                yield from f
        finally:
            logging.info(f"Cleaning up {zip_path} and {temp_dir}")
            try:
                os.remove(zip_path)
                shutil.rmtree(temp_dir)
            except OSError as e:
                logging.error(f"Error during cleanup: {e}")

    response = Response(stream_and_cleanup(), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename=playlist.zip'
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)