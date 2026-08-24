"""
lofi lope YouTube Automation Pipeline
Full End-to-End Orchestrator:
1. Fetches Video, Audio, Image triplets from Google Drive (or local folders)
2. Watermark elimination
3. Cozy aesthetic lofi thumbnail creation
4. 1-Hour HD Video rendering (NVENC / CPU)
5. YouTube publish & SEO metadata tagging
"""

import os
import sys
import json
import glob
import random
import time
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from google_drive_fetch import fetch_assets_triplet
from thumbnail_generator import create_lofi_thumbnail, LOFI_HOOKS
from video_generator import build_lofi_video

PUBLISHED_LOG = "published_videos.json"
ALLOW_REPOST = os.getenv("ALLOW_REPOST", "true").lower() == "true"

def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_published_entry(video_name, audio_name, image_name, yt_video_id=None, title=""):
    history = get_published_history()
    entry = {
        "video_file": os.path.basename(video_name),
        "audio_file": os.path.basename(audio_name),
        "image_file": os.path.basename(image_name) if image_name else "",
        "youtube_id": yt_video_id,
        "youtube_url": f"https://youtu.be/{yt_video_id}" if yt_video_id else "LOCAL_RENDER",
        "title": title,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    history.append(entry)
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[LOG] Saved publication record to {PUBLISHED_LOG}")

def generate_youtube_metadata(audio_path, video_path):
    """Generate SEO-optimized lofi title, description, and tags for lofi lope."""
    base_name = os.path.splitext(os.path.basename(audio_path))[0].replace("_", " ").title()
    vid_name = os.path.splitext(os.path.basename(video_path))[0].replace("_", " ").title()
    
    titles_templates = [
        f"1 Hour {base_name} | Lofi Hip Hop Beats to Study / Relax to",
        f"Late Night Study Session - {base_name} | Cozy Lofi Beats [1 Hour]",
        f"Deep Focus & Study Beats | {base_name} - Chill Lofi Music (1 Hour)",
        f"Cozy Lofi Vibes for Work & Coding | {base_name} (1 Hour)",
        f"Midnight Thoughts | {base_name} - Relaxing Lofi Hip Hop for Sleep & Chill",
        f"Peaceful Study Session with {base_name} | Chillhop & Lofi Beats",
        f"Relaxing Lofi Beats for Stress Relief | {base_name} (1 Hour)"
    ]
    
    title = random.choice(titles_templates)
    
    desc = (
        f"☕ Welcome to lofi lope — your cozy corner for chill lofi beats, deep focus study sessions, and late-night relaxation.\n\n"
        f"🎵 Track: '{base_name}'\n\n"
        f"Immerse yourself in 1 hour of warm, nostalgic lofi hip hop beats designed for studying, coding, reading, working, or unwinding before sleep. "
        f"Let the calming rhythm guide your focus and bring peace to your mind.\n\n"
        f"✨ Perfect For:\n"
        f"• Deep focus study & homework sessions\n"
        f"• Coding, writing & creative work\n"
        f"• Late night thoughts & unwinding\n"
        f"• Stress relief, relaxation & deep sleep\n"
        f"• Cozy background music for reading & coffee breaks\n\n"
        f"🎧 Track Details:\n"
        f"• Track Name: {base_name}\n"
        f"• Duration: 1 Hour Looping Mix\n"
        f"• Channel: lofi lope\n\n"
        f"🔔 Subscribe to lofi lope for daily cozy lofi beats and study vibes!\n\n"
        f"#lofi #lofihiphop #studybeats #lofirelax #chillhop #lofilope #1hourlofi #beatsforstudying #codingbeats #cozyvibes"
    )
    
    tags = [
        "lofi", "lofi hip hop", "lofi beats", "study beats", "chillhop",
        "lofi chill", "relaxing lofi", "beats to study to", "late night lofi",
        "cozy lofi", "lofi music", "lofi lope", "deep focus", "coding music",
        "lofi study", "beats to relax to", "1 hour lofi", "chill beats",
        "study music", "sleep lofi", "ambient beats"
    ]
    
    return title, desc, tags

def run_pipeline(duration=3600, dry_run=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_thumb_dir = os.path.join(script_dir, "output_thumbnails")
    output_video_dir = os.path.join(script_dir, "output_videos")
    
    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("        LOFI LOPE BOT - AUTOMATED PIPELINE")
    print("="*60)
    
    # Step 1: Fetch triplet
    vid_path, aud_path, img_path, is_repost = fetch_assets_triplet(allow_repost=ALLOW_REPOST)
    if not vid_path or not aud_path:
        print("[ERROR] Could not fetch required video and audio assets.")
        return False
        
    print(f"\n[STEP 1] Assets Selected:")
    print(f"  • Video: {os.path.basename(vid_path)}")
    print(f"  • Audio: {os.path.basename(aud_path)}")
    print(f"  • Image: {os.path.basename(img_path) if img_path else 'None (extracting frame from video)'}")
    
    # If no thumbnail image, extract frame 2s from video
    if not img_path or not os.path.exists(img_path):
        img_path = os.path.join(script_dir, "input_images", f"frame_{os.path.splitext(os.path.basename(vid_path))[0]}.jpg")
        subprocess.run(['ffmpeg', '-y', '-ss', '00:00:02', '-i', vid_path, '-frames:v', '1', '-update', '1', img_path], check=True)
        
    # Step 2: Generate Thumbnail
    safe_name = "".join(c for c in os.path.splitext(os.path.basename(aud_path))[0] if c.isalnum() or c in (' ', '_', '-')).strip()
    thumb_output = os.path.join(output_thumb_dir, f"Thumb_{safe_name}.jpg")
    
    hook = random.choice(LOFI_HOOKS)
    print(f"\n[STEP 2] Creating Lofi Thumbnail with Hook: '{hook['main']}'...")
    create_lofi_thumbnail(img_path, thumb_output, main_text=hook['main'], sub_text=hook['sub'])
    
    # Step 3: Render Full Video
    dur_label = f"{duration//60}min" if duration >= 60 else f"{duration}s"
    final_video_path = os.path.join(output_video_dir, f"Lofi_{safe_name}_{dur_label}.mp4")
    
    print(f"\n[STEP 3] Rendering {dur_label} Looping Video...")
    success = build_lofi_video(
        input_video=vid_path,
        input_audio=aud_path,
        output_path=final_video_path,
        duration_seconds=duration,
        remove_watermark=True
    )
    
    if not success:
        print("[ERROR] Video generation failed.")
        return False
        
    # Step 4: Metadata & Publishing
    title, desc, tags = generate_youtube_metadata(aud_path, vid_path)
    print(f"\n[STEP 4] Generated YouTube Metadata:")
    print(f"  • Title: {title}")
    print(f"  • Tags: {', '.join(tags[:6])}...")
    
    if dry_run:
        print(f"\n[DRY RUN] Finished. Video saved at: {final_video_path}")
        print(f"[DRY RUN] Thumbnail saved at: {thumb_output}")
        save_published_entry(vid_path, aud_path, img_path, yt_video_id=None, title=title)
        return True
        
    # Optional Step 5: Upload to YouTube if publish_youtube exists
    try:
        from publish_youtube import upload_to_youtube, set_video_thumbnail
        print(f"\n[STEP 5] Uploading to YouTube...")
        video_id = upload_to_youtube(final_video_path, title, desc, tags=tags)
        if video_id:
            set_video_thumbnail(video_id, thumb_output)
            save_published_entry(vid_path, aud_path, img_path, yt_video_id=video_id, title=title)
            print(f"🎉 SUCCESS! Published to YouTube: https://youtu.be/{video_id}")
            return True
    except Exception as e:
        print(f"[YOUTUBE NOTE] YouTube API upload skipped or not configured ({e}). Video is ready in output_videos/")
        save_published_entry(vid_path, aud_path, img_path, yt_video_id=None, title=title)
        return True

if __name__ == "__main__":
    dur = 3600
    is_dry = "--dry-run" in sys.argv
    for idx, arg in enumerate(sys.argv):
        if arg == "--duration" and idx + 1 < len(sys.argv):
            dur = int(sys.argv[idx + 1])
    run_pipeline(duration=dur, dry_run=is_dry)
