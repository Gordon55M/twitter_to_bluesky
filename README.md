# twitter_to_bluesky
2025 Twitter Archive to BlueSky Posts with Media

***********
**WARNING**
***********
THIS WILL SPAM YOUR FEED AND FOLLOWERS. DO THIS AS SOON AS YOU MIGRATE TO BLUESKY
***********

This local Python code is meant to take a downloaded and unzipped twitter archive file and migrate previous tweets and media associated with those tweets to BlueSky Social. There are a few variables I took into consideration:
-Two Factor Authentication
-Tweet Archive Unzipped tweets.js path
-Tweet Media Archive Folder location

Steps to use:
1) Download your twitter archive and unzip.
2) Within the unzipped folder locate the tweets.js file. Currently (02/09/25) it exists at /data/tweets.js
3) Locate the Media Folder.  Currently (02/09/25) it exists at /data/tweets_media
  # 🔹 Paths to Twitter Archive
TWITTER_ARCHIVE_PATH = "ENTER_TWEETS_FILE_LOCATION_AND_FILENAME.EXTENSION"
MEDIA_FOLDER = "ENTER_TWEETS_MEDIA_FOLDER_LOCATION"
5) Enter you BlueSky Login information here:
# 🔹 Bluesky Login Info
BSKY_USERNAME = "BLUESKY_LOGIN"
BSKY_PASSWORD = "BLUESKY_PASS"
5) Run the Python script
6) Within seconds BlueSky will send you a 2FA via email if you have that setup. Within 15 seconds, the Python console will ask for that two facor code. Paste it in and hit enter
7) Watch as your old tweets cycle through and get posted to your BlueSky Feed!
