from fastapi import FastAPI, HTTPException

from typing import Union

import json
from random import choice
from deta import Deta
import os
import googleapiclient.discovery
from pydantic import BaseModel

# Initialize with a Project Key from DetaBaseKey.txt
with open("DetaBaseKey.txt") as f:
    Detakey = f.read()

# Initialize with a Project Key from YTKey.txt
with open("YTKey.txt") as f:
    YTkey = f.read()
    
deta = Deta(Detakey)
db = deta.Base("elbunquer-api-base")

tags_metadata = [
    {
        "name": "Informació episodi",
        "description": "Obté informació d'un episodi del podcast.",
    },
    {
        "name": "Informació episodis",
        "description": "Obté informació de multiples episodis del podcast.",
    },
    {
        "name": "Actualitza informació",
        "description": "Actualitza la informació dels episodis del podcast.",
    },
]

description = """
Obté informació dels capítols d'**El Búnquer** de Youtube.
"""

app = FastAPI(
    title="elbunquer-api",
    description=description,
    version="0.1.0",
    contact={
        "name": "Pedro Juan Royo",
        "url": "https://github.com/Parzival1918",
        "email": "pedro.juan.royo@gmail.com",
    },
    # openapi_tags=tags_metadata,
    docs_url="/",
    redoc_url="/alt-docs",
)

class VideoDescription(BaseModel):
    height: int
    url: str
    width: int

class VideoTumbnails(BaseModel):
    default: VideoDescription
    medium: VideoDescription
    high: VideoDescription
    standard: VideoDescription
    maxres: VideoDescription

class InfoEpisodi(BaseModel):
    videoId: str
    videoTitle: str
    videoDescription: str
    videoThumbnails: VideoTumbnails
    videoDate: str
    videoLink: str
    season: int
    episode: int

@app.get("/info-episodi/{temporada}/{episodi}", tags=["Informació episodi"], description="Obté informació d'un episodi del podcast.", response_model=InfoEpisodi)
def info_episodi_per_temporada(temporada: int, episodi: int):
    #Get from Deta base
    key = f"s{temporada}e{episodi}"
    data = db.get(key=key)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    return data

@app.get("/info-episodi/aleatori", tags=["Informació episodi"], description="Obté informació d'un episodi aleatori del podcast.", response_model=InfoEpisodi)
def episodi_aleatori(inclou_extres: bool = False):
    #Get from Deta base info
    info = db.get(key="info")
    if info is None:
        raise HTTPException(status_code=401, detail="No hi ha informació disponible")
    
    #Get random season
    keysList = list(info.keys())
    keysList.remove("key")
    if not inclou_extres:
        keysList.remove("0")

    print(keysList)
    temporada = choice(keysList)

    #Get random episode
    episodi = choice(range(1, info[temporada] + 1))

    #Get from Deta base
    key = f"s{temporada}e{episodi}"
    data = db.get(key=key)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")

    return data

class InfoEpisodis(BaseModel):
    episodis: list[InfoEpisodi]

@app.get("/info-episodis/per-temporada/{temporada}", tags=["Informació episodis"], description="Obté informació de multiples episodis del podcast d'una temporada.", response_model=InfoEpisodis)
def info_episodis_per_temporada(temporada: int):
    #Get from Deta base
    key = f"s{temporada}"
    data = db.fetch(query={"season": temporada}, limit=1000)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    return {"episodis": data.items}

def search_word(word: str, text: str):
    for w in text.split(sep=" "):
        if word == w: #Exact match
            print(f"Exact matching {w} |-| {word}")
            return True
        if (word in w or w in word) and abs(len(word)-len(w)) <= 2 and len(w) > 2:
            print(f"Matching {w} |-| {word}")
            return True
        
    return False
        
@app.get("/info-episodis/per-cerca/{cerca}", tags=["Informació episodis"], description="Obté informació de multiples episodis del podcast fent una cerca per paraula.", response_model=InfoEpisodis)
def info_episodis_per_cerca(cerca: str, cerca_descripcio: bool = False):
    print(f"Searched for: {cerca}")
    #Get from Deta base
    if cerca_descripcio:
        data = db.fetch(query=[{"videoDescription?contains": cerca}, {"videoTitle?contains": cerca}], limit=1000)
    else:
        data = db.fetch(query={"videoTitle?contains": cerca}, limit=1000)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    furtherFileredData = []
    for item in data.items:
        if cerca_descripcio:
            if search_word(cerca, item["videoTitle"]) or search_word(cerca, item["videoDescription"]):
                furtherFileredData.append(item)
        else:
            if search_word(cerca, item["videoTitle"]):
                furtherFileredData.append(item)

    print(f"Found {len(furtherFileredData)} results")
    
    return {"episodis": furtherFileredData}

def obtainSeason(videoTitle: str):
    #Get the season number, parse title text to find digits in format 00x00
    try:
        seasonep = videoTitle.split(" ")[-1]
        #remove brackets
        seasonep = seasonep.replace(")","")
        seasonep = seasonep.replace("(","")
        season = int(seasonep.split("x")[0])
        episode = int(seasonep.split("x")[1])

        return season, episode
    except:
        print("ERROR in: " + videoTitle)
        return None, None
    
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

def format_entry(video: dict, info: dict):
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

def updateDatabase():
    response = callYTAPI(ELBUNQUER_ID)

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
                db.put(format_entry(item, info), key=key)
                itemsCount += 1

                #Update info, check that season exists
                if f"{season}" in info:
                    info[f"{season}"] += 1
                else:
                    info[f"{season}"] = 1
                
                print(f"Added '{item['snippet']['title']}' to Deta")
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

                    info[f"{season}"] -= 1
                    
                    #Add to Deta again with the new season and episode
                    key,season=get_key_from_title(item["snippet"]["title"])
                    db.delete(key=res["key"])
                    db.put(format_entry(item, info), key=key)
                    itemsCount += 1

                    #Update info, check that season exists
                    if f"{season2}" in info:
                        info[f"{season2}"] += 1
                    else:
                        info[f"{season2}"] = 1

                    print(f"Changed and added '{item['snippet']['title']}' to Deta")
                else:
                    print(f"Item '{item['snippet']['title']}' already in Deta")
                    allEntriesAlreadyInDeta = True

        if not allEntriesAlreadyInDeta:
            nextPage = response["nextPageToken"]
            response = callYTAPI(ELBUNQUER_ID, nextPage)

    print(f"Added {itemsCount} items to Deta")

    info.pop("key")
    print(info)
    db.put(info, key="info")

def updateEpisodeCount():
    #Get from Deta base info
    info = db.get(key="info")
    seasonsInInfo = list(info.keys())
    seasonsInInfo.remove("key")

    #Get from Deta base all items from each season and update the count
    for season in seasonsInInfo:
        items = db.fetch(query={"season": int(season)}, limit=1000)
        if items.count == info[season]:
            print(f"Season {season} episode count up to date ({items.count})")
            continue
        else:
            print(f"Season {season} episode count not up to date, updating... from {items.count} to {seasonsInInfo[season]}")
            info[season] = items.count

    db.put(info, key="info")

class DetaEvent(BaseModel):
    id: str
    trigger: str

class DetaSpaceActions(BaseModel):
    event: DetaEvent

# Paths for Deta Space to call at scheduled times
@app.post("/__space/v0/actions", tags=["Actualitza informació"], description="Actualitza la informació dels episodis del podcast, **no es pot accedir.**", include_in_schema=True)
def actualitza_info(action: DetaSpaceActions):
    action = action.model_dump()
    actionID = action["event"]["id"]

    if actionID == "updateInfo":
        updateDatabase()
        #update episode count too
        updateEpisodeCount()
    elif actionID == "updateEpisodeCount":
        updateEpisodeCount()
    else:
        raise HTTPException(status_code=402, detail="Action not found")

    return {"message": f"Action {actionID} received"}