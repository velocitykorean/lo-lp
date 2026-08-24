"""
Google Drive Integration Module for lofi lope YouTube Automation
Fetches:
1. Video Loops (MP4/MOV/MKV) from GOOGLE_DRIVE_VIDEO_FOLDER_ID
2. Audio Tracks (MP3/WAV/FLAC) from GOOGLE_DRIVE_AUDIO_FOLDER_ID
3. Thumbnail Images (JPG/PNG/WEBP) from GOOGLE_DRIVE_IMAGE_FOLDER_ID

Supports:
- Priority for new unpublished lofi tracks
- Infinite circulation mode (Weighted Least-Recently-Used selection)
- Dynamic remixing across video, audio, and thumbnail permutations
- Seamless fallback between Google Drive and local directories
"""
import os
import io
import json
import sys
import glob
import random
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

GOOGLE_DRIVE_VIDEO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_VIDEO_FOLDER_ID")
GOOGLE_DRIVE_AUDIO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_AUDIO_FOLDER_ID")
GOOGLE_DRIVE_IMAGE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_IMAGE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "service_account.json")

LOCAL_VIDEO_DIR = os.getenv("LOCAL_VIDEO_DIR", "input_videos")
LOCAL_AUDIO_DIR = os.getenv("LOCAL_AUDIO_DIR", "input_audio")
LOCAL_IMAGE_DIR = os.getenv("LOCAL_IMAGE_DIR", "input_images")
PUBLISHED_LOG = "published_videos.json"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Build and return an authorized Google Drive v3 service instance."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[DRIVE] Google API libraries not installed.")
        return None

    if not GOOGLE_SERVICE_ACCOUNT_KEY:
        return None

    try:
        key_str = GOOGLE_SERVICE_ACCOUNT_KEY.strip()
        if key_str.startswith('{'):
            info = json.loads(key_str)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build('drive', 'v3', credentials=credentials)
        elif os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            return build('drive', 'v3', credentials=credentials)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sa_path = os.path.join(script_dir, GOOGLE_SERVICE_ACCOUNT_KEY)
            if os.path.exists(sa_path):
                credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
                return build('drive', 'v3', credentials=credentials)
            return None
    except Exception as e:
        print(f"[DRIVE ERROR] Failed to initialize Google Drive: {e}")
        return None

def list_files_in_folder(folder_id, mime_prefix=None, extensions=None):
    """List non-trashed files inside a Google Drive folder."""
    if not folder_id:
        return []
    service = get_drive_service()
    if not service:
        return []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size)",
            pageSize=100
        ).execute()
        files = results.get('files', [])
        if mime_prefix or extensions:
            filtered = []
            for f in files:
                name = f.get('name', '').lower()
                mime = f.get('mimeType', '').lower()
                if mime_prefix and mime.startswith(mime_prefix):
                    filtered.append(f)
                elif extensions and any(name.endswith(ext) for ext in extensions):
                    filtered.append(f)
            return filtered
        return files
    except Exception as e:
        print(f"[DRIVE ERROR] Error listing files in folder {folder_id}: {e}")
        return []

def download_file(file_id, dest_path):
    """Downloads a single file from Google Drive."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        return False
    service = get_drive_service()
    if not service:
        return False
    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with io.FileIO(dest_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"[DRIVE ERROR] Error downloading {file_id}: {e}")
        return False

def get_repost_counts():
    """Counts how many times each audio track has been published."""
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                counts = {}
                for item in data:
                    sname = (item.get("audio_file") or item.get("audio_name") or item.get("song_name") or "").strip().lower()
                    if sname:
                        counts[sname] = counts.get(sname, 0) + 1
                return counts
        except Exception:
            return {}
    return {}

def fetch_assets_triplet(allow_repost=True):
    """
    Fetches ONE video, ONE audio track, and ONE thumbnail image for lofi lope.
    Supports Infinite Circulation Mode with Weighted Least-Recently-Used selection.
    Intelligently combines Google Drive and local assets.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vid_dir = os.path.join(script_dir, LOCAL_VIDEO_DIR)
    aud_dir = os.path.join(script_dir, LOCAL_AUDIO_DIR)
    img_dir = os.path.join(script_dir, LOCAL_IMAGE_DIR)
    
    os.makedirs(vid_dir, exist_ok=True)
    os.makedirs(aud_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    drive_service = get_drive_service()
    drive_ready = (drive_service is not None)

    # 1. Gather Audio (Drive -> fallback Local)
    a_files = []
    if drive_ready and GOOGLE_DRIVE_AUDIO_FOLDER_ID:
        print("[DRIVE] Checking Google Drive Audio folder...")
        a_files = list_files_in_folder(GOOGLE_DRIVE_AUDIO_FOLDER_ID, extensions=['.mp3', '.wav', '.flac'])
    
    local_auds = sorted(glob.glob(os.path.join(aud_dir, "*.mp3")) + glob.glob(os.path.join(aud_dir, "*.wav")) + glob.glob(os.path.join(aud_dir, "*.flac")))

    # 2. Gather Video (Drive -> fallback Local)
    v_files = []
    if drive_ready and GOOGLE_DRIVE_VIDEO_FOLDER_ID:
        print("[DRIVE] Checking Google Drive Video folder...")
        v_files = list_files_in_folder(GOOGLE_DRIVE_VIDEO_FOLDER_ID, extensions=['.mp4', '.mov', '.mkv'])
    
    local_vids = sorted(glob.glob(os.path.join(vid_dir, "*.mp4")) + glob.glob(os.path.join(vid_dir, "*.mov")) + glob.glob(os.path.join(vid_dir, "*.mkv")))

    # 3. Gather Image (Drive -> fallback Local)
    i_files = []
    if drive_ready and GOOGLE_DRIVE_IMAGE_FOLDER_ID:
        print("[DRIVE] Checking Google Drive Image folder...")
        i_files = list_files_in_folder(GOOGLE_DRIVE_IMAGE_FOLDER_ID, extensions=['.jpg', '.jpeg', '.png', '.webp'])
    
    local_imgs = sorted(glob.glob(os.path.join(img_dir, "*.jpg")) + glob.glob(os.path.join(img_dir, "*.png")) + glob.glob(os.path.join(img_dir, "*.jpeg")) + glob.glob(os.path.join(img_dir, "*.webp")))

    # --- Select Audio ---
    repost_counts = get_repost_counts()
    sel_audio_path = None
    is_repost = False

    if a_files:
        unpublished_drive = [f for f in a_files if f['name'].strip().lower() not in repost_counts]
        if unpublished_drive:
            sel_a = unpublished_drive[0]
            is_repost = False
            print(f"[PIPELINE] New Lofi Track on Drive: {sel_a['name']}")
        elif allow_repost:
            weights = [max(1, 1000 // (3 ** min(repost_counts.get(f['name'].strip().lower(), 0), 6))) for f in a_files]
            sel_a = random.choices(a_files, weights=weights, k=1)[0]
            is_repost = True
            prev_c = repost_counts.get(sel_a['name'].strip().lower(), 0)
            print(f"[PIPELINE] Infinite Circulation: Selected {sel_a['name']} (published {prev_c} times before).")
        else:
            sel_a = None

        if sel_a:
            a_dest = os.path.join(aud_dir, sel_a['name'])
            if not os.path.exists(a_dest):
                print(f"[DRIVE] Downloading audio from Drive: {sel_a['name']}...")
                download_file(sel_a['id'], a_dest)
            sel_audio_path = a_dest
    
    if not sel_audio_path and local_auds:
        unpublished_local = [f for f in local_auds if os.path.basename(f).strip().lower() not in repost_counts]
        if unpublished_local:
            sel_audio_path = unpublished_local[0]
            is_repost = False
        elif allow_repost:
            weights = [max(1, 1000 // (3 ** min(repost_counts.get(os.path.basename(f).strip().lower(), 0), 6))) for f in local_auds]
            sel_audio_path = random.choices(local_auds, weights=weights, k=1)[0]
            is_repost = True

    if not sel_audio_path:
        print("[ERROR] No audio files found in Google Drive or local input_audio folder.")
        return None, None, None, False

    # --- Select Video ---
    sel_video_path = None
    if v_files:
        sel_v = v_files[len(repost_counts) % len(v_files)]
        v_dest = os.path.join(vid_dir, sel_v['name'])
        if not os.path.exists(v_dest):
            print(f"[DRIVE] Downloading video from Drive: {sel_v['name']}...")
            download_file(sel_v['id'], v_dest)
        sel_video_path = v_dest
    elif local_vids:
        sel_video_path = local_vids[len(repost_counts) % len(local_vids)]

    if not sel_video_path:
        print("[ERROR] No video files found in Google Drive or local input_videos folder.")
        return None, None, None, False

    # --- Select Image ---
    sel_image_path = None
    if i_files:
        sel_i = i_files[len(repost_counts) % len(i_files)]
        i_dest = os.path.join(img_dir, sel_i['name'])
        if not os.path.exists(i_dest):
            print(f"[DRIVE] Downloading image from Drive: {sel_i['name']}...")
            download_file(sel_i['id'], i_dest)
        sel_image_path = i_dest
    elif local_imgs:
        sel_image_path = local_imgs[len(repost_counts) % len(local_imgs)]

    return sel_video_path, sel_audio_path, sel_image_path, is_repost
