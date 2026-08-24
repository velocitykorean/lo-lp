"""
Aesthetic YouTube Thumbnail Generator for lofi lope
High-CTR, cozy aesthetic typography with thick, high-visibility letterforms:
- Auto-removes bottom-right AI watermarks (Gemini 4-point star / Grok / etc.) via seamless inpainting
- Bold typography with Gaussian ambient drop shadows
- Solid white thick headline ("DEEP FOCUS" / "LATE NIGHT" / "COZY VIBES")
- Warm pastel gold subtitle ("Lofi Beats to Study & Relax")
- Top-Right corner badge ("1 HOUR · LOFI BEATS")
- 1280x720 16:9 output
"""

import os
import sys
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LOFI_HOOKS = [
    {"main": "DEEP FOCUS", "sub": "Lofi Beats to Study & Work"},
    {"main": "LATE NIGHT", "sub": "Chill Lofi Study Session"},
    {"main": "COZY VIBES", "sub": "Relaxing Lofi Hip Hop Beats"},
    {"main": "STUDY SESSION", "sub": "Peaceful Beats for Deep Focus"},
    {"main": "MIDNIGHT CHILL", "sub": "Lofi Music to Relax & Sleep"},
    {"main": "RAINY NIGHTS", "sub": "Cozy Lofi Beats for Coding"},
    {"main": "STAY FOCUSED", "sub": "Calm Lofi for Studying & Work"},
    {"main": "PEACEFUL MIND", "sub": "Soothing Lofi Beats to Unwind"},
    {"main": "COFFEE BREAK", "sub": "Warm & Cozy Lofi Vibes"},
    {"main": "NIGHT THOUGHTS", "sub": "Chillhop & Ambient Lofi Beats"}
]

def get_font(font_name="Cinzel-Black.ttf", size=48):
    fonts = [
        os.path.join(SCRIPT_DIR, "assets", "fonts", font_name),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Cinzel.ttf"),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Georgia-Bold.ttf"),
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()

def remove_thumbnail_watermark(pil_img):
    """Seamlessly inpaints and removes any AI watermark in the bottom-right corner."""
    if not CV2_AVAILABLE:
        return pil_img
    try:
        cv_img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        h, w = cv_img.shape[:2]
        
        # Mask bottom-right watermark region
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[int(h * 0.76):int(h * 0.94), int(w * 0.86):int(w * 0.98)] = 255
        
        inpainted = cv2.inpaint(cv_img, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
        return Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)).convert("RGBA")
    except Exception as e:
        print(f"[WARN] Watermark inpainting skipped: {e}")
        return pil_img

def draw_cinematic_text(draw_target, pos, text, font, fill_color, shadow_blur=10, shadow_offset=(3, 5), shadow_opacity=230):
    """
    Renders text with a smooth Gaussian ambient shadow + directional drop shadow.
    """
    w, h = draw_target.size
    shadow_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    
    # 1. Ambient soft shadow
    s_draw.text(pos, text, font=font, fill=(0, 0, 0, shadow_opacity))
    # 2. Directional offset shadow
    ox, oy = shadow_offset
    s_draw.text((pos[0] + ox, pos[1] + oy), text, font=font, fill=(0, 0, 0, int(shadow_opacity * 0.9)))
    
    # Gaussian blur
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
    draw_target.alpha_composite(shadow_layer)
    
    # Draw crisp thick text on top
    text_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(text_layer)
    t_draw.text(pos, text, font=font, fill=fill_color)
    draw_target.alpha_composite(text_layer)

def create_lofi_thumbnail(bg_path, output_path, main_text=None, sub_text=None, badge_text="1 HOUR · LOFI BEATS"):
    """
    Creates a clean, aesthetic lofi lope thumbnail with watermark removal.
    """
    if not main_text:
        preset = random.choice(LOFI_HOOKS)
        main_text = preset["main"]
        sub_text = preset["sub"]

    # 1. Open and resize/crop to 1280x720 (16:9)
    img = Image.open(bg_path).convert("RGBA")
    target_w, target_h = 1280, 720
    
    if img.width / img.height > target_w / target_h:
        new_w = int(img.height * (target_w / target_h))
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        new_h = int(img.width * (target_h / target_w))
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))
        
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # 2. Seamlessly remove bottom-right AI watermark
    img = remove_thumbnail_watermark(img)
    
    # 3. Rich color and contrast enhancement
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    
    # 4. Smooth natural ambient dark shadow behind text area
    scrim = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(scrim)
    # Bottom-left text area smooth shadow
    for r in range(600, 0, -10):
        alpha = int((1.0 - (r / 600.0)**1.4) * 165)
        sdraw.ellipse([-120, target_h - 420, r * 1.8, target_h + 180], fill=alpha)
    # Top-right corner smooth shadow
    for r in range(350, 0, -10):
        alpha = int((1.0 - (r / 350.0)**1.4) * 130)
        sdraw.ellipse([target_w - r * 1.5, -80, target_w + 80, r * 1.2], fill=alpha)
    scrim = scrim.filter(ImageFilter.GaussianBlur(40))
    dark_bg = Image.new("RGBA", (target_w, target_h), (6, 8, 12, 255))
    canvas = Image.composite(dark_bg, img, scrim)
    
    font_main = get_font("Cinzel-Black.ttf", size=100)
    font_sub = get_font("Cinzel-Black.ttf", size=40)
    font_badge = get_font("Cinzel-Black.ttf", size=34)
    
    # --- 1. TOP-RIGHT BADGE ---
    dummy = ImageDraw.Draw(canvas)
    bbox = dummy.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox[2] - bbox[0]
    bx = target_w - bw - 75
    by = 50
    draw_cinematic_text(canvas, (bx, by), badge_text, font_badge, fill_color=(255, 242, 215, 255), shadow_blur=6, shadow_offset=(2, 4))
    
    # --- 2. BOTTOM-LEFT TEXT STACK ---
    x_pos = 75
    y_base = target_h - 170
    sub_y = y_base - 62
    
    # Subtitle (Thick warm champagne gold)
    if sub_text:
        draw_cinematic_text(canvas, (x_pos, sub_y), sub_text.upper(), font_sub, fill_color=(255, 222, 135, 255), shadow_blur=8, shadow_offset=(2, 3))
        
    # Main Headline (Thick solid white)
    draw_cinematic_text(canvas, (x_pos, y_base), main_text.upper(), font_main, fill_color=(255, 255, 255, 255), shadow_blur=12, shadow_offset=(3, 6))
    
    # 5. Merge and save
    final = canvas.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated Watermark-Free Lofi Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    test_img = os.path.join(SCRIPT_DIR, "input_images", "sample_test.jpg")
    # If test img doesn't exist, extract from sample video
    if not os.path.exists(test_img):
        import subprocess
        v_sample = os.path.join(SCRIPT_DIR, "input_videos", "Girl_repotting_succulent_at_desk_202608241759.mp4")
        if os.path.exists(v_sample):
            subprocess.run(['ffmpeg', '-y', '-ss', '00:00:02', '-i', v_sample, '-frames:v', '1', test_img], check=True)
            
    if os.path.exists(test_img):
        out_thumb = os.path.join(SCRIPT_DIR, "output_thumbnails", "lofilope_preview.jpg")
        create_lofi_thumbnail(test_img, out_thumb, "DEEP FOCUS", "Lofi Beats to Study & Work")
