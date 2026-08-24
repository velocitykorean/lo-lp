# lofi lope YouTube Automation Bot ☕🎧

A production-grade, end-to-end automated pipeline for the **lofi lope** YouTube Channel (lofi hip hop, chillhop, study beats, coding music, late-night focus & sleep mixes).

---

## 📁 Project Architecture

```
lofilope/
├── .env                       # Environment configuration & Google Drive folder IDs
├── .env.example               # Example environment template
├── google_drive_fetch.py      # Fetches Video, Audio, and Image assets from Google Drive
├── thumbnail_generator.py     # Generates aesthetic high-CTR lofi thumbnails with watermark removal
├── video_generator.py         # Removes watermarks, upscales to 1080p, builds seamless ping-pong loops
├── auto_pipeline.py           # Master end-to-end automation orchestrator
├── publish_youtube.py         # YouTube Data API upload & thumbnail publishing module
├── published_videos.json      # Publication history tracking & infinite circulation log
├── requirements.txt           # Python dependencies
├── assets/
│   └── fonts/                 # Custom high-grade serif & display fonts
├── input_videos/              # Local / synced short video loops (10s-20s)
├── input_audio/               # Local / synced lofi beats & chillhop tracks (MP3/WAV)
├── input_images/              # Local / synced thumbnail background images
├── output_thumbnails/         # Generated YouTube thumbnails (1280x720)
├── output_videos/             # Rendered full 1080p Full HD videos (1 Hour)
└── .github/
    └── workflows/
        └── auto_publish.yml   # GitHub Actions automated daily publishing workflow
```

---

## 🔗 Google Drive Folder Setup

The bot monitors 3 dedicated Google Drive folders:

| Asset Type | Google Drive Folder URL | Folder ID |
|---|---|---|
| **Audio** (MP3/WAV) | [Audio Folder](https://drive.google.com/drive/folders/1N_gSsO0jVBaUFm72vb7EKw0JlUbqoLjO) | `1N_gSsO0jVBaUFm72vb7EKw0JlUbqoLjO` |
| **Video** (MP4/MOV) | [Video Folder](https://drive.google.com/drive/folders/1xW3wjRv8xX3X-2-g9pEnrfGzzTM1uiNj) | `1xW3wjRv8xX3X-2-g9pEnrfGzzTM1uiNj` |
| **Images** (JPG/PNG) | [Images Folder](https://drive.google.com/drive/folders/1GSC947Q033SklDhQy42DWuEoxi8RbKCY) | `1GSC947Q033SklDhQy42DWuEoxi8RbKCY` |

> **Important:** Share all 3 Google Drive folders with the Service Account email found in `service_account.json` with **Viewer** permissions.

---

## ⚙️ Configuration (`.env`)

Create your `.env` file from `.env.example`:

```env
# Google Drive Folder IDs
GOOGLE_DRIVE_VIDEO_FOLDER_ID=1xW3wjRv8xX3X-2-g9pEnrfGzzTM1uiNj
GOOGLE_DRIVE_AUDIO_FOLDER_ID=1N_gSsO0jVBaUFm72vb7EKw0JlUbqoLjO
GOOGLE_DRIVE_IMAGE_FOLDER_ID=1GSC947Q033SklDhQy42DWuEoxi8RbKCY

# Service Account Key
GOOGLE_SERVICE_ACCOUNT_KEY=service_account.json

# YouTube Data API Credentials
YT_CLIENT_ID=your_client_id
YT_CLIENT_SECRET=your_client_secret
YT_REFRESH_TOKEN=your_refresh_token

# Automation Settings
CHANNEL_NAME=lofi lope
DEFAULT_DURATION=3600
ALLOW_REPOST=true
```

---

## 🚀 Usage Commands

### 1. Run Complete Automation Pipeline (1-Hour Video)
```powershell
python auto_pipeline.py --duration 3600
```

### 2. Run Preview Test (30-Second Video Dry-Run)
```powershell
python auto_pipeline.py --duration 30 --dry-run
```

### 3. Generate Thumbnail Only
```powershell
python thumbnail_generator.py
```

---

## 🤖 GitHub Actions Automation

The repository includes a GitHub Action workflow `.github/workflows/auto_publish.yml` that runs daily or on-demand.

### Required Repository Secrets:
Set the following secrets in **GitHub Repository Settings -> Secrets and variables -> Actions**:
- `GOOGLE_DRIVE_VIDEO_FOLDER_ID`
- `GOOGLE_DRIVE_AUDIO_FOLDER_ID`
- `GOOGLE_DRIVE_IMAGE_FOLDER_ID`
- `GOOGLE_SERVICE_ACCOUNT_KEY` (Paste raw JSON content of `service_account.json`)
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`
