import sys
import os
from upload_video import get_authenticated_service
from googleapiclient.http import MediaFileUpload

def update_thumbnail(video_id, thumbnail_path):
    print(f"Updating thumbnail for video {video_id} with {thumbnail_path}...")
    youtube = get_authenticated_service()
    
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print("Thumbnail uploaded successfully!")
    except Exception as e:
        print(f"Failed to set thumbnail: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 update_thumbnail.py <video_id> <thumbnail_path>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    thumbnail_path = sys.argv[2]
    
    if not os.path.exists(thumbnail_path):
        print(f"Error: File '{thumbnail_path}' not found.")
        sys.exit(1)
        
    update_thumbnail(video_id, thumbnail_path)
