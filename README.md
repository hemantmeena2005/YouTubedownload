# YouTube Playlist Downloader

A Flask web application that downloads YouTube videos and playlists as audio files (MP3 or M4A) and provides them as downloadable ZIP files.

## Features

- Download YouTube videos and playlists as audio
- Choose between MP3 (slower, more compatible) or M4A (faster) formats
- Real-time progress updates
- Automatic ZIP file creation and download
- Clean, modern UI

## Deployment Options

### Option 1: Railway (Recommended - Free & Easy)

1. **Install Railway CLI** (optional but helpful):
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect it's a Python app and deploy

3. **Alternative: Deploy via CLI**:
   ```bash
   railway login
   railway init
   railway up
   ```

### Option 2: Render (Free Tier Available)

1. Go to [render.com](https://render.com)
2. Sign up and connect your GitHub
3. Click "New Web Service"
4. Select your repository
5. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Deploy

### Option 3: Heroku (Paid)

1. Install Heroku CLI
2. Run these commands:
   ```bash
   heroku create your-app-name
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

### Option 4: DigitalOcean App Platform

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Create new app from GitHub
3. Select your repository
4. Configure as Python app
5. Deploy

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python app.py
   ```

3. **Access at**: `http://localhost:5000`

## Important Notes

- **FFmpeg**: For MP3 conversion, FFmpeg needs to be installed on the server. Most cloud platforms (Railway, Render, Heroku) include it by default.
- **Storage**: The app uses temporary storage for downloads. Files are automatically cleaned up after download.
- **Rate Limits**: Be aware of YouTube's terms of service and rate limits.
- **Legal**: Ensure you comply with YouTube's terms of service and copyright laws.

## Environment Variables

- `PORT`: Port number (set automatically by most platforms)

## File Structure

```
├── app.py              # Main Flask application
├── index.html          # Frontend interface
├── requirements.txt    # Python dependencies
├── Procfile           # Deployment configuration
├── runtime.txt        # Python version
├── .gitignore         # Git ignore rules
└── temp/              # Temporary download directory
``` 