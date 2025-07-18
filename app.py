# app.py
from flask import Flask, request, send_file, jsonify, Response, stream_with_context
import yt_dlp
import zipfile
import os
import uuid
import shutil
import logging
import time

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

            yield "\nProcessing files...\n"
            
            # Check if files were downloaded
            files_in_dir = os.listdir(temp_dir)
            if not files_in_dir:
                yield "❌ No files were downloaded. Please check the URL.\n"
                return
            
            yield f"Found {len(files_in_dir)} files.\n"
            
            # ✨ NEW: Handle single video vs playlist differently
            if total == 1:
                # Single video - no zip needed
                file_name = files_in_dir[0]
                file_path = os.path.join(temp_dir, file_name)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    yield f"✅ Single video ready: {file_name} ({file_size} bytes)\n"
                    yield f"SINGLE_FILE:{download_id}:{file_name}\n"
                else:
                    yield "❌ File not found after download.\n"
            else:
                # Multiple videos - create zip
                yield "Creating ZIP file for playlist...\n"
                zip_path = os.path.join('temp', f"{download_id}.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in files_in_dir:
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            zipf.write(file_path, arcname=file)
                            yield f"Zipped: {file}\n"

                # Verify zip was created
                if os.path.exists(zip_path):
                    zip_size = os.path.getsize(zip_path)
                    yield f"\n✅ ZIP file created successfully ({zip_size} bytes).\n"
                    yield f"ALL_DONE:{download_id}\n"
                else:
                    yield "\n❌ Failed to create ZIP file.\n"

        except Exception as e:
            logging.error(f"Error during download/zip for {download_id}: {e}")
            yield f"💥 An unexpected error occurred: {e}\n"
        finally:
            if total > 1:  # Only send ALL_DONE for playlists
                yield f"ALL_DONE:{download_id}\n"

    return Response(stream_with_context(generate_and_download()), mimetype='text/plain')


@app.route('/get_file/<download_id>/<filename>')
def get_file(download_id, filename):
    if not all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in download_id):
        return jsonify({'error': 'Invalid download ID'}), 400

    file_path = os.path.join('temp', download_id, filename)
    temp_dir = os.path.join('temp', download_id)

    # Add logging
    logging.info(f"Requesting single file: {filename} for ID: {download_id}")
    logging.info(f"File path: {file_path}")
    logging.info(f"File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found or already deleted.'}), 404
        
    def stream_and_cleanup():
        try:
            with open(file_path, 'rb') as f:
                yield from f
        finally:
            # Add delay before cleanup to ensure download completes
            time.sleep(1)
            logging.info(f"Cleaning up single file: {file_path} and {temp_dir}")
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except OSError as e:
                logging.error(f"Error during cleanup: {e}")

    # Determine MIME type based on file extension
    if filename.lower().endswith('.mp3'):
        mime_type = 'audio/mpeg'
    elif filename.lower().endswith('.m4a'):
        mime_type = 'audio/mp4'
    else:
        mime_type = 'audio/mpeg'  # default

    response = Response(stream_and_cleanup(), mimetype=mime_type)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/get_zip/<download_id>')
def get_zip(download_id):
    if not all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in download_id):
        return jsonify({'error': 'Invalid download ID'}), 400

    zip_path = os.path.join('temp', f"{download_id}.zip")
    temp_dir = os.path.join('temp', download_id)

    # Add more detailed logging
    logging.info(f"Requesting zip for ID: {download_id}")
    logging.info(f"Zip path: {zip_path}")
    logging.info(f"Zip exists: {os.path.exists(zip_path)}")
    
    if not os.path.exists(zip_path):
        # Check if temp directory exists
        if os.path.exists(temp_dir):
            files_in_temp = os.listdir(temp_dir)
            logging.info(f"Temp dir exists with files: {files_in_temp}")
        else:
            logging.info("Temp directory does not exist")
        return jsonify({'error': 'File not found or already deleted.'}), 404
        
    def stream_and_cleanup():
        try:
            with open(zip_path, 'rb') as f:
                yield from f
        finally:
            # Add delay before cleanup to ensure download completes
            time.sleep(1)
            logging.info(f"Cleaning up {zip_path} and {temp_dir}")
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except OSError as e:
                logging.error(f"Error during cleanup: {e}")

    response = Response(stream_and_cleanup(), mimetype='application/zip')
    response.headers['Content-Disposition'] = 'attachment; filename=playlist.zip'
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)