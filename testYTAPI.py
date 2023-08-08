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
# print(response)

def obtain_season_episode(title: str):
    #Get the season number, parse title text to find digits in format 00x00
    try:
        seasonep = title.split(" ")[-1]
        #remove brackets
        seasonep = seasonep.replace(")","")
        seasonep = seasonep.replace("(","")
        season = int(seasonep.split("x")[0])
        episode = int(seasonep.split("x")[1])

        return season, episode
    except:
        print("ERROR in: " + title)
        return 0, None

def format_entry(video: dict):
    #Get the video id
    videoId = video['snippet']['resourceId']['videoId']
    #Get the video title
    videoTitle = video['snippet']['title']
    #Get the video description
    videoDescription = video['snippet']['description']
    #Get the video thumbnail
    videoThumbnails = video['snippet']['thumbnails']
    #Get the video date
    videoDate = video['snippet']['publishedAt']
    #Get the video link
    videoLink = "https://www.youtube.com/watch?v=" + videoId

    #Get the season and episode number
    season, episode = obtain_season_episode(videoTitle)

    if season == None:
        season = 0
        episode = info["0"] + 1
    
    #Save the video info in a json file
    videoInfo = {"videoId":videoId,"videoTitle":videoTitle,"videoDescription":videoDescription,\
                    "videoThumbnails":videoThumbnails,"videoDate":videoDate,"videoLink":videoLink,\
                    "season":season,"episode":episode}
    
    return videoInfo

def get_key_from_title(title: str):
    season, episode = obtain_season_episode(title)
    key = f"s{season}e{episode}"

    return key, season

###

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
        except:
            print("ERROR: " + item["snippet"]["title"] + " has no videoId")
            itemsCountTotal -= 1
            continue

        res = db.fetch(query={"videoId": videoID})
        if res.count == 0:
            res = None

        if res is None:
            #Add to Deta
            key,season=get_key_from_title(item["snippet"]["title"])
            # db.put(format_entry(item), key=key)
            itemsCount += 1

            #Update info, check that season exists
            if season in info:
                info[season] += 1
            else:
                info[season] = 1
            
            print(f"Added {item['snippet']['title']} to Deta")
        else:
            res = res.items[0]

            #Get season and episode from res
            season, episode = res["season"], res["episode"]
            #Get season and episode from item
            season2, episode2 = obtain_season_episode(item["snippet"]["title"])

            if season != season2 or episode != episode2:
                print(f"ERROR: {item['snippet']['title']} is already in Deta, but with different season or episode")
                print(f"Season in Deta: {season}, Season in YT: {season2}")
                print(f"Episode in Deta: {episode}, Episode in YT: {episode2}")
                
                #Add to Deta again with the new season and episode
                key,season=get_key_from_title(item["snippet"]["title"])
                # db.put(format_entry(item), key=key)
                itemsCount += 1

                #Update info, check that season exists
                info[season] -= 1
                if season2 in info:
                    info[season2] += 1
                else:
                    info[season2] = 1
            else:
                print(f"Item {item['snippet']['title']} already in Deta")
                allEntriesAlreadyInDeta = True

    if not allEntriesAlreadyInDeta:
        nextPage = response["nextPageToken"]
        response = callYTAPI(ELBUNQUER_ID, nextPage)

print(f"Added {itemsCount} items to Deta")
print(info)

# db.put(info, key="info")