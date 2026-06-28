import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_video_content(topic, duration):
    """
    Generates video metadata and script using Google Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
        
    client = genai.Client(api_key=api_key)
    
    # Calculate approximate word count (average 2.5 words per second)
    word_count = int(duration) * 2.5
    
    prompt = f"""
    You are an expert YouTube scriptwriter and SEO specialist.
    Create a complete content package for a YouTube video about the following topic or GitHub repository: 
    "{topic}"
    
    If it is a GitHub repository, explain what it does, why it is cool, and why developers are starring it. Make it sound exciting!
    The video will be exactly {duration} seconds long.
    The voiceover script must be exactly around {word_count} words to fit this duration perfectly.
    
    Respond ONLY in valid JSON format with the following keys:
    "title": "A catchy, click-worthy YouTube title (max 70 characters)",
    "description": "An SEO optimized description with at least 3 relevant hashtags at the end",
    "tags": "comma, separated, list, of, 10, seo, tags",
    "script": "The actual voiceover script text. Do not include any brackets, speaker names, or stage directions. Just the spoken words.",
    "search_query": "A simple 1 or 2 word search term to find a background stock video for this topic on Pexels (e.g. 'technology', 'space', 'robot')"
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    # Parse the JSON response
    text = response.text
    # Clean up if the model wrapped it in markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    if text.endswith("```\n"):
        text = text[:-4]
        
    try:
        content = json.loads(text.strip())
        return content
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from AI: {text}")
        raise e

def generate_thumbnail(topic, output_filename="thumbnail.png"):
    """
    Generates a thumbnail image using Gemini's image generation capabilities (Imagen 3).
    If the API key does not have image generation access, it will fail gracefully.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Skipping thumbnail generation.")
        return None
        
    print(f"Generating thumbnail for topic: {topic}...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"A high quality, modern, YouTube thumbnail style illustration for a developer tool about: {topic}. Vibrant colors, highly detailed, visually striking, minimalist."
        
        response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="9:16",
            )
        )
        
        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            with open(output_filename, "wb") as f:
                f.write(image_data)
            print(f"Thumbnail successfully generated and saved to {output_filename}")
            return output_filename
        else:
            print("No image was returned from the API.")
            return None
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None

if __name__ == "__main__":
    # Test the module
    topic = "The history of Artificial Intelligence"
    duration = 30
    
    # List models to see what's available
    print("Available models:")
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        for m in client.models.list():
            if "imagen" in m.name.lower():
                print(m.name)
    except Exception as e:
        print(f"Failed to list models: {e}")
            
    print(f"\nGenerating content for: {topic}")
    result = generate_video_content(topic, duration)
    print(json.dumps(result, indent=2))
    

