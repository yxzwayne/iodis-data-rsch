import os
import time
import json
import requests
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
PLAYLIST_ID = "PLbVNzAA7sXzCMxebUrgKN9dcsWlgQQmGf"  # iodis from @Harstem
BASE_URL = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={PLAYLIST_ID}&key={API_KEY}"

response = requests.get(BASE_URL + "&maxResults=1")
total_items = int(response.json()["pageInfo"]["totalResults"])

# Check if the JSON file exists and load existing data
existing_video_info = []
if os.path.exists("../iodis_video_info.json"):
    with open("../iodis_video_info.json", "r") as f:
        existing_video_info = json.load(f)

# Create a set of existing video IDs for faster lookup
existing_video_ids = set(video["video_id"] for video in existing_video_info)

video_info = []
next_page_token = None

with tqdm(total=total_items, desc="Processing videos") as pbar:
    while True:
        url = BASE_URL + (f"&pageToken={next_page_token}" if next_page_token else "")
        response = requests.get(url)
        data = response.json()

        for item in data["items"]:
            video_id = item["contentDetails"]["videoId"]
            if (
                "private" not in item["snippet"]["title"].lower()
                and video_id not in existing_video_ids
            ):
                video_info.insert(
                    0,
                    {
                        "title": item["snippet"]["title"],
                        "release_date": item["snippet"]["publishedAt"],
                        "description": item["snippet"]["description"],
                        "video_id": video_id,
                    },
                )
            pbar.update(1)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(0.2)

# Combine new video info with existing data
combined_video_info = video_info + existing_video_info

with open("../iodis_video_info.json", "w") as f:
    json.dump(combined_video_info, f)
