import os
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
import random
import nltk
from nltk.corpus import stopwords

# Ensure NLTK data is downloaded for tags
nltk.download('stopwords')
nltk.download('punkt')

def download_video(url, output_path="downloads"):
    """Downloads YouTube video using yt-dlp."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info.get('title', 'Unknown'), info.get('duration', 0)

def generate_tags(title):
    """Generates hashtags based on the video title."""
    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(title.lower())
    keywords = [word for word in words if word.isalnum() and word not in stop_words]
    
    base_tags = ["#shorts", "#fyp", "#trending", "#reels"]
    content_tags = [f"#{word}" for word in keywords[:5]]
    return " ".join(base_tags + content_tags)

def create_clips(video_path, num_clips, duration, output_folder="clips"):
    """Splits video into random segments of specific duration."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    video = VideoFileClip(video_path)
    video_duration = video.duration
    generated_clips = []

    # Load Whisper model once (small is faster for CPU)
    model = whisper.load_model("small") 

    for i in range(num_clips):
        # Ensure we don't pick a start time that exceeds video length
        max_start = max(0, video_duration - duration)
        start_time = random.uniform(0, max_start)
        end_time = min(start_time + duration, video_duration)
        
        # Cut the clip
        clip = video.subclip(start_time, end_time)
        clip_filename = f"{output_folder}/clip_{i}_{os.path.basename(video_path)}"
        
        # 1. Transcribe Audio
        # We need to temporarily save audio to transcribe it
        temp_audio = "temp_audio.wav"
        clip.audio.write_audiofile(temp_audio, logger=None)
        result = model.transcribe(temp_audio)
        
        # 2. Create Captions (Subtitle Generator)
        # This function creates a text clip for every segment found by Whisper
        def generator(txt):
            return TextClip(txt, font='Arial-Bold', fontsize=24, color='white', 
                            stroke_color='black', stroke_width=2, method='caption', 
                            size=(clip.w, None)).set_pos(('center', 'bottom'))

        # Convert Whisper segments to MoviePy subtitles
        subs = []
        for segment in result['segments']:
            start = segment['start']
            end = segment['end']
            text = segment['text']
            subs.append(((start, end), text))

        subtitles = SubtitlesClip(subs, generator)
        final_clip = CompositeVideoClip([clip, subtitles])
        
        # Write final file
        final_clip.write_videofile(clip_filename, codec='libx264', audio_codec='aac', logger=None)
        generated_clips.append(clip_filename)
        
        # Cleanup temp audio
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    video.close()
    return generated_clips