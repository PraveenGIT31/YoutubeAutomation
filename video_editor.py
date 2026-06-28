import os
import asyncio
import edge_tts
from moviepy import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip
from dotenv import load_dotenv

load_dotenv()

async def generate_voiceover(script, output_filename="voiceover.mp3"):
    """
    Generates a voiceover using Microsoft Edge TTS.
    """
    print("Generating voiceover...")
    # 'en-US-ChristopherNeural' is a good, deep male voice
    communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
    await communicate.save(output_filename)
    print(f"Voiceover saved to {output_filename}")
    return output_filename

def create_scrolling_video_from_image(image_path, audio_path, output_path="final_video.mp4", aspect_ratio="9:16"):
    """
    Assembles the final video using moviepy by scrolling down the screenshot.
    """
    print("Assembling final scrolling video...")
    
    # Load audio
    audio_clip = AudioFileClip(audio_path)
    target_duration = audio_clip.duration
    
    if not image_path or not os.path.exists(image_path):
        print("No image provided. Creating a fallback black background...")
        if aspect_ratio == "9:16":
            size = (1080, 1920)
        else:
            size = (1920, 1080)
        video_clip = ColorClip(size=size, color=(0,0,0), duration=target_duration)
    else:
        from PIL import Image
        import numpy as np
        
        # Load the screenshot using PIL
        pil_img = Image.open(image_path)
        img_w, img_h = pil_img.size
        
        # Calculate target size
        if aspect_ratio == "9:16":
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080
            
        # We want to scale the image so it fills the width
        scale_factor = target_w / img_w
        target_height = int(img_h * scale_factor)
        
        # Resize using PIL
        pil_img_resized = pil_img.resize((target_w, target_height), Image.Resampling.LANCZOS)
        
        # Convert to numpy array for ImageClip
        scaled_img = ImageClip(np.array(pil_img_resized))
        scaled_w, scaled_h = scaled_img.size
        
        # If the image is taller than the target, we scroll down
        if scaled_h > target_h:
            # We scroll from top (y=0) to bottom (y=scaled_h - target_h)
            max_y = scaled_h - target_h
            
            # The crop function needs to return x1, y1, x2, y2 based on time t
            def get_crop_region(t):
                # Calculate progress from 0 to 1
                progress = t / target_duration
                # Add a little padding at start and end
                if progress < 0.1:
                    y_offset = 0
                elif progress > 0.9:
                    y_offset = max_y
                else:
                    # Scroll between 10% and 90% of the video duration
                    scroll_progress = (progress - 0.1) / 0.8
                    y_offset = max_y * scroll_progress
                
                return x1_y1_x2_y2(0, int(y_offset), target_w, int(y_offset) + target_h)
            
            def x1_y1_x2_y2(x1, y1, x2, y2):
                return x1, y1, x2, y2
                
            # Unfortunately, fx(crop) doesn't take a dynamic function easily in all versions.
            # We can use fl_image or set_position inside a CompositeVideoClip
            def make_frame(t):
                progress = t / target_duration
                if progress < 0.1:
                    y_offset = 0
                elif progress > 0.9:
                    y_offset = max_y
                else:
                    scroll_progress = (progress - 0.1) / 0.8
                    y_offset = max_y * scroll_progress
                
                # We need to crop the numpy frame
                frame = scaled_img.get_frame(t)
                y_offset = int(y_offset)
                return frame[y_offset:y_offset+target_h, 0:target_w]
                
            from moviepy import VideoClip
            video_clip = VideoClip(make_frame, duration=target_duration)
        else:
            # If it's shorter, center it on a black background
            background = ColorClip(size=(target_w, target_h), color=(0,0,0), duration=target_duration)
            centered_img = scaled_img.with_duration(target_duration).with_position('center')
            video_clip = CompositeVideoClip([background, centered_img])
                
    # Set the audio
    final_clip = video_clip.with_audio(audio_clip)
    
    # Write result
    print(f"Rendering final video to {output_path}...")
    final_clip.write_videofile(
        output_path, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac",
        logger=None # Disable verbose output
    )
    print("Video rendered successfully!")
    return output_path
