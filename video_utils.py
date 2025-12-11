import os
import re
import gc
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from whisper import load_model

# --- Helper Functions ---

def clean_filename(title: str) -> str:
    """Sanitizes a string to be a safe filename."""
    s = re.sub(r'[\\/:*?"<>|]+', '', title)
    return s[:100].strip()

def time_to_seconds(time_str: str) -> float:
    """Converts a time string (m:s or h:m:s) to seconds."""
    parts = list(map(float, time_str.split(':')))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0.0

# --- Core Processing Function ---

async def process_youtube_clip(
    url: str, 
    time_range: str, 
    download_dir: str, 
    clip_dir: str, 
    user_id: int, 
    logger
) -> tuple[str, str]:
    """Downloads, clips, transcribes, and cleans up a YouTube video."""
    
    downloaded_video_path = None
    final_clip_path = None
    caption_text = None

    try:
        # 1. Parse time range (e.g., "1:30-2:00")
        start_str, end_str = time_range.split('-')
        start_time = time_to_seconds(start_str)
        end_time = time_to_seconds(end_str)
        
        if end_time <= start_time:
            logger.error("End time must be greater than start time.")
            return None, None

        # 2. Download the video using yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(download_dir, f'{user_id}_%(title)s.%(ext)s'),
            'quiet': True,
            'max_filesize': 500 * 1024 * 1024, # Max 500MB download
            'download_ranges': lambda _, __: [{'start_time': start_time, 'end_time': end_time + 5}], # Download slightly more
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'clip')
            downloaded_video_path = ydl.prepare_filename(info)

        logger.info(f"Video downloaded to {downloaded_video_path}")

        # 3. Perform clipping with moviepy
        output_filename = clean_filename(f"clip_{original_title}_{time_range}.mp4")
        final_clip_path = os.path.join(clip_dir, output_filename)
        
        with VideoFileClip(downloaded_video_path) as video:
            clipped_video = video.subclip(start_time, end_time)
            
            # Ensure output is Telegram-compatible (h264 codec)
            clipped_video.write_videofile(
                final_clip_path, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True,
                logger=None,  # Suppress moviepy logging
                fps=24 # Ensure low FPS for smaller size
            )

        # 4. Transcribe audio with Whisper (using the clipped file)
        logger.info("Starting Whisper transcription...")
        
        # Load small model for speed on free CPU tier
        model = load_model("small") 
        result = model.transcribe(final_clip_path, fp16=False)
        caption_text = result["text"]
        
        logger.info("Transcription complete.")
        
        # 5. Cleanup the Whisper model (crucial for memory management)
        del model
        gc.collect() 
        
        return final_clip_path, caption_text

    except Exception as e:
        logger.error(f"Error during video processing: {e}", exc_info=True)
        return None, None
        
    finally:
        # 6. CRUCIAL CLEANUP: Remove large temporary files to prevent OOM errors
        if downloaded_video_path and os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
            logger.info(f"Cleaned up source file: {downloaded_video_path}")
        
        # NOTE: We keep the final_clip_path until it's sent via Telegram, then it can be deleted
        # Telegram handles deleting the local file after successful upload.
        # However, for total safety, you might want to manually delete after sending:
        # if final_clip_path and os.path.exists(final_clip_path):
        #     os.remove(final_clip_path)
        #     logger.info(f"Cleaned up final clip: {final_clip_path}")
        
        gc.collect()