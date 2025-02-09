import json
import requests
import os
import time
import datetime

# 🔹 Paths to Twitter Archive
TWITTER_ARCHIVE_PATH = "ARCHIVE_TWEET_DIRECTORY_PATH/tweets.js"
MEDIA_FOLDER = "TWEETS_MEDIA_FOLDER_DIRECTORY_PATH"

# 🔹 Bluesky Login Info
BSKY_USERNAME = "BLUESKY_USERNAME"
BSKY_PASSWORD = "BLUESKY_PASS"

# 🔹 Bluesky API Endpoints
BSKY_AUTH_URL = "https://bsky.social/xrpc/com.atproto.server.createSession"
BSKY_POST_URL = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
BSKY_UPLOAD_URL = "https://bsky.social/xrpc/com.atproto.repo.uploadBlob"

# 🔹 Authenticate with Bluesky
def get_bsky_session():
    print("🔄 Attempting to log in to Bluesky...")
    response = requests.post(BSKY_AUTH_URL, json={"identifier": BSKY_USERNAME, "password": BSKY_PASSWORD})
    data = response.json()
    
    if response.status_code == 200:
        return data.get("accessJwt")

    elif "AuthFactorTokenRequired" in data.get("error", ""):
        print("\n🔑 2FA Required! A sign-in code has been sent to your email.")
        time.sleep(15)
        factor_token = input("Enter the 2FA code from your email: ").strip()

        response_2fa = requests.post(BSKY_AUTH_URL, json={
            "identifier": BSKY_USERNAME,
            "password": BSKY_PASSWORD,
            "authFactorToken": factor_token
        })

        data_2fa = response_2fa.json()
        if response_2fa.status_code == 200:
            return data_2fa.get("accessJwt")
        else:
            print("❌ Failed 2FA authentication:", data_2fa)
            return None
    else:
        print("❌ Authentication error:", data)
        return None

jwt_token = get_bsky_session()
if not jwt_token:
    raise SystemExit("🔴 Exiting script. Fix authentication.")

# 🔹 Read Twitter archive
if not os.path.exists(TWITTER_ARCHIVE_PATH):
    raise SystemExit("❌ Twitter archive file not found!")

with open(TWITTER_ARCHIVE_PATH, "r", encoding="utf-8") as file:
    raw_data = file.read()
    json_start = raw_data.find("[")
    tweets_data = json.loads(raw_data[json_start:])

# 🔹 Format Twitter Timestamp (Corrected)
def format_twitter_timestamp(twitter_time):
    try:
        dt = datetime.datetime.strptime(twitter_time, "%a %b %d %H:%M:%S %z %Y")
        return dt.astimezone(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except Exception:
        return datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"



# 🔹 Find Media File in Local Folder
def find_local_media_file(tweet_id, media_filename):
    expected_filename = f"{tweet_id}-{media_filename}".lower()
    for file in os.listdir(MEDIA_FOLDER):
        if file.lower() == expected_filename:
            return os.path.join(MEDIA_FOLDER, file)
    return None

import mimetypes

def upload_media(file_path):
    """Uploads an image and returns the full blob reference object with correct MIME type."""
    if not os.path.exists(file_path):
        print(f"❌ Media file not found: {file_path}")
        return None

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/octet-stream"  # ✅ Required to send as raw binary
    }

    # ✅ Detect the MIME type dynamically
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type not in ["image/jpeg", "image/png"]:
        print(f"❌ Unsupported file type: {mime_type} ({file_path})")
        return None

    with open(file_path, "rb") as file:
        image_data = file.read()

    print(f"📤 Uploading media: {file_path} as {mime_type}...")
    response = requests.post(BSKY_UPLOAD_URL, headers=headers, data=image_data)  # ✅ Send raw binary

    if response.status_code == 200:
        json_response = response.json()
        blob = json_response.get("blob", {})
        if blob:
            # ✅ Add correct MIME type to returned blob reference
            blob["mimeType"] = mime_type
            print(f"✅ Uploaded media successfully: {blob}")
            return blob
        else:
            print("❌ Unexpected response from Bluesky:", json_response)
            return None
    else:
        print(f"❌ Media upload failed: {response.json()}")
        return None

# 🔹 Post to Bluesky (Fixed Version)
def post_to_bluesky(text, created_at, media_files=[]):
    if not text.strip():  # ✅ Ensure text is not empty
        text = "[No text content]"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    media_blobs = [upload_media(file_path) for file_path in media_files]
    media_blobs = [blob for blob in media_blobs if blob is not None]

    payload = {
        "repo": BSKY_USERNAME,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": text[:300],  # ✅ Truncate long tweets
            "createdAt": created_at
        }
    }

    if media_blobs:
        payload["record"]["embed"] = {
            "$type": "app.bsky.embed.images",
            "images": [
                {
                    "image": {
                        "$type": "blob",
                        "ref": blob["ref"],  # ✅ Correct blob reference
                        "mimeType": blob["mimeType"],  # ✅ Ensure correct MIME type
                        "size": blob.get("size", 0)
                    },
                    "alt": "Twitter image"
                }
                for blob in media_blobs
            ]
        }

    print("\n📤 Attempting to post to Bluesky...")
    print("📝 Payload:", json.dumps(payload, indent=2))

    response = requests.post(BSKY_POST_URL, headers=headers, json=payload)
    data = response.json() if response.content else {}

    if response.status_code == 200:
        print("✅ Successfully posted!")
    else:
        print(f"❌ Posting failed! Status Code: {response.status_code}")
        print("📩 API Response:", json.dumps(data, indent=2))

# 🔹 Migrate ALL Tweets with Local Media
for tweet in tweets_data:  # Limit to 10 tweets for testing
    text = tweet["tweet"].get("full_text", tweet["tweet"].get("text", ""))
    timestamp = tweet["tweet"].get("created_at", "")
    tweet_id = tweet["tweet"]["id_str"]

    media_files = []
    if "extended_entities" in tweet["tweet"] and "media" in tweet["tweet"]["extended_entities"]:
        for media in tweet["tweet"]["extended_entities"]["media"]:
            if media.get("type") == "photo":
                media_filename = media.get("media_url_https").split("/")[-1]
                file_path = find_local_media_file(tweet_id, media_filename)
                if file_path:
                    media_files.append(file_path)

    if text:
        post_time = format_twitter_timestamp(timestamp)
        print(f"📤 Posting: {text[:50]}... ({post_time})")
        post_to_bluesky(text, post_time, media_files)

        time.sleep(2)  # ✅ Prevent hitting rate limits

print("🎉 Migration complete!")
