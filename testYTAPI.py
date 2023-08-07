from deta import Deta
import os
import googleapiclient.discovery

# Initialize with a Project Key from DetaBaseKey.txt
with open("DetaBaseKey.txt") as f:
    Detakey = f.read()

# Initialize with a Project Key from YTKey.txt
with open("YTKey.txt") as f:
    YTkey = f.read()

deta = Deta(Detakey)
db = deta.Base("elbunquer-api-base")

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

def format_entry(ytContent: dict):
    pass

def get_key_from_title(ytContent: dict):
    pass

nextPage = response["nextPageToken"]
itemsCountTotal = response["pageInfo"]["resultsPerPage"]
itemsCount = 0
allEntriesAlreadyInDeta = False

info = db.get(key="info")
print(info)

while nextPage and not allEntriesAlreadyInDeta:
    for item in response["items"]:
        #Check if item exists in Deta
        try:
            videoID = item["snippet"]["resourceId"]["videoId"]
            res = db.fetch(query={"videoId": videoID})
        except:
            print("ERROR: " + item["snippet"]["title"] + " has no videoId")
            itemsCountTotal -= 1
            continue

        if res is None:
            #Add to Deta
            key,season=get_key_from_title(item["snippet"]["title"])
            db.put(format_entry(item), key=key)
            itemsCount += 1

            #Update info, check that season exists
            if season in info:
                info[season] += 1
            else:
                info[season] = 1
        else:
            #TODO: Check that if it is already in Deta, it has the same season, episode and title
            print(f"Item {item['snippet']['title']} already in Deta")
            allEntriesAlreadyInDeta = True

    if not allEntriesAlreadyInDeta:
        nextPage = response["nextPageToken"]
        response = callYTAPI(ELBUNQUER_ID, nextPage)

print(f"Added {itemsCount} items to Deta")
print(info)