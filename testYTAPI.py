import os
import googleapiclient.discovery

# Initialize with a Project Key from YTKey.txt
with open("YTKey.txt") as f:
    YTkey = f.read()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = YTkey
ELBUNQUER_ID = "PL5HwsHboiE9ngozgQ1ZkB9X4gnEwUcLR3"

def callYTAPI(playlistIdtxt="", pageTokentxt=""):
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        pageToken=pageTokentxt,
        playlistId=playlistIdtxt
    )
    response = request.execute()

    return response

response = callYTAPI(ELBUNQUER_ID)
print(response)
