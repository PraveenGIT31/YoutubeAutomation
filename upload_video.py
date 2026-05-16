import os
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0, prompt='select_account')
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)

def upload_video(youtube, file, title, description, tags, category_id="22", privacy_status="private", thumbnail_path=None):
    print(f"Uploading file: {file}...")
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False, 
        }
    }

    # Call the API's videos.insert method to create and upload the video.
    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"Upload Complete! Video ID: {response['id']}")
    print(f"URL: https://youtu.be/{response['id']}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        print(f"Setting thumbnail: {thumbnail_path}...")
        try:
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Failed to set thumbnail: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload a video to YouTube.')
    parser.add_argument('--file', required=True, help='Path to the video file to upload.')
    parser.add_argument('--title', required=True, help='Title of the video.')
    parser.add_argument('--description', default='Uploaded via YouTube API.', help='Description of the video.')
    parser.add_argument('--tags', default='', help='Comma-separated tags for the video.')
    parser.add_argument('--privacy', default='private', choices=['private', 'public', 'unlisted'], help='Privacy status of the video.')
    parser.add_argument('--thumbnail', default=None, help='Path to the thumbnail image to upload.')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        exit(1)
        
    tags_list = [tag.strip() for tag in args.tags.split(',') if tag.strip()]

    youtube_service = get_authenticated_service()
    
    try:
        upload_video(
            youtube_service,
            args.file,
            args.title,
            args.description,
            tags_list,
            privacy_status=args.privacy,
            thumbnail_path=args.thumbnail
        )
    except Exception as e:
        print(f"An error occurred: {e}")
