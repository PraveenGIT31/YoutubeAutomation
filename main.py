import argparse
import asyncio
import os
from ai_generator import generate_video_content, generate_thumbnail
from video_editor import generate_voiceover, create_scrolling_video_from_image
from upload_video import get_authenticated_service, upload_video
from fetch_trendshift import fetch_unprocessed_trending_repo, save_processed_repo
from screenshot_util import take_screenshot
def main():
    parser = argparse.ArgumentParser(description='Automated AI YouTube Video Creator')
    parser.add_argument('--topic', required=False, help='The topic of the video (optional if --auto is used)')
    parser.add_argument('--auto', action='store_true', help='Automatically fetch a trending GitHub repo from trendshift.io')
    parser.add_argument('--duration', type=int, default=30, help='Approximate duration in seconds')
    parser.add_argument('--aspect', default='9:16', choices=['9:16', '16:9'], help='Aspect ratio for Shorts (9:16) or normal videos (16:9)')
    parser.add_argument('--no-upload', action='store_true', help='Generate video but do not upload to YouTube')
    
    args = parser.parse_args()
    
    if not args.topic and not args.auto:
        parser.error("Either --topic or --auto must be provided.")

    repo_url = None
    repo_desc = None
    if args.auto:
        print("="*50)
        print("🤖 Running in AUTO mode: Fetching trending repo from trendshift.io")
        repo_url, repo_name, repo_desc = fetch_unprocessed_trending_repo()
        if not repo_url:
            print("No new repositories to process. Exiting.")
            return
        args.topic = f"A GitHub repository named {repo_name} which does: {repo_desc}"
        print(f"✅ Selected Repo: {repo_url}")
        print("="*50)

    print("="*50)
    print(f"🎬 Starting Automated Video Generation pipeline")
    print(f"Topic Context: {args.topic}")
    print(f"Target Duration: {args.duration}s")
    print(f"Aspect Ratio: {args.aspect}")
    print("="*50)
    
    # 1. Generate AI Content (Script, Title, Description)
    print("\n[1/4] Generating Script and Metadata using AI...")
    content = generate_video_content(args.topic, args.duration)
    
    title = content["title"]
    description = content["description"]
    
    if repo_url:
        description += f"\n\n🔗 Repository: {repo_url}"
        if repo_desc:
            description += f"\n📝 Description: {repo_desc}"
            
    tags = [t.strip() for t in content["tags"].split(',')]
    script = content["script"]
    search_query = content["search_query"]
    
    print(f"\n✅ Title: {title}")
    print(f"✅ Search Query for Visuals: {search_query}")
    print(f"✅ Script Preview: {script[:100]}...\n")
    
    # 2. Generate Voiceover
    print("[2/4] Generating Voiceover...")
    audio_file = asyncio.run(generate_voiceover(script))
    
    # 3. Take Screenshot (if we have a URL, otherwise use a placeholder or skip)
    screenshot_path = "repo_screenshot.png"
    if repo_url:
        print("\n[3/5] Capturing full-page screenshot of the repository...")
        try:
            asyncio.run(take_screenshot(repo_url, screenshot_path))
        except Exception as e:
            print(f"Screenshot failed: {e}")
            screenshot_path = None
    else:
        print("\n[3/5] No repo URL provided for screenshot. Will use fallback.")
        screenshot_path = None
        
    # 4. Generate Thumbnail
    print("\n[4/5] Generating Thumbnail via Gemini...")
    if os.path.exists("thumbnail.png"):
        print("✅ Using existing thumbnail.png")
        thumbnail_path = "thumbnail.png"
    else:
        thumbnail_path = generate_thumbnail(args.topic, "thumbnail.png")
    
    # 5. Assemble Final Video
    print("\n[5/5] Assembling Final Scrolling Video...")
    final_video = create_scrolling_video_from_image(
        image_path=screenshot_path,
        audio_path=audio_file,
        output_path="final_video.mp4",
        aspect_ratio=args.aspect
    )
    
    # Clean up temporary files
    if os.path.exists(audio_file):
        os.remove(audio_file)
    if screenshot_path and os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        
    print(f"\n🎉 Video generation complete: {final_video}")
    
    # 6. Upload to YouTube
    if not args.no_upload:
        print("\n[5/5] Uploading to YouTube...")
        try:
            youtube_service = get_authenticated_service()
            upload_video(
                youtube_service,
                final_video,
                title,
                description,
                tags,
                privacy_status="private", # default private for safety
                thumbnail_path=thumbnail_path
            )
            print("\n✅ Upload Complete!")
        except Exception as e:
            print(f"\n❌ Error during upload: {e}")
            print(f"The video was still saved as {final_video}")
    else:
        print("\n⏭️ Skipping YouTube upload as requested.")

    # 6. Mark repo as processed if auto mode
    if args.auto and repo_url:
        save_processed_repo(repo_url)
        print(f"\n✅ Marked {repo_url} as processed.")

if __name__ == "__main__":
    main()
