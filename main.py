from fastapi import FastAPI, HTTPException

from typing import Union

import json
from random import choice
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

@app.get("/info-episodi/{temporada}/{episodi}", tags=["Informació episodi"], description="Obté informació d'un episodi del podcast.")
def info_episodi_per_temporada(temporada: int, episodi: int):
    #Get from Deta base
    key = f"s{temporada}e{episodi}"
    data = db.get(key=key)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    return data

@app.get("/info-episodi/aleatori", tags=["Informació episodi"], description="Obté informació d'un episodi aleatori del podcast.")
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

@app.get("/info-episodis/per-temporada/{temporada}", tags=["Informació episodis"], description="Obté informació de multiples episodis del podcast d'una temporada.")
def info_episodis_per_temporada(temporada: int):
    #Get from Deta base
    key = f"s{temporada}"
    data = db.fetch(query={"season": temporada}, limit=1000)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    return data.items

def search_word(word: str, text: str):
    for w in text.split(sep=" "):
        if word == w: #Exact match
            print(f"Exact matching {w} |-| {word}")
            return True
        if (word in w or w in word) and abs(len(word)-len(w)) <= 2 and len(w) > 2:
            print(f"Matching {w} |-| {word}")
            return True
        
    return False
        
@app.get("/info-episodis/per-cerca/{cerca}", tags=["Informació episodis"], description="Obté informació de multiples episodis del podcast fent una cerca per paraula.")
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
    
    return furtherFileredData

from pydantic import BaseModel

class DetaSpaceActions(BaseModel):
    event: dict = {"id": str, "trigger": str}

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

def updateDatabase():
    pass

# Paths for Deta Space to call at scheduled times
@app.post("/__space/v0/actions", tags=["Actualitza informació"], description="Actualitza la informació dels episodis del podcast, **no es pot accedir.**", include_in_schema=True)
def actualitza_info(action: DetaSpaceActions):
    action = action.model_dump()
    actionID = action["event"]["id"]

    if actionID == "updateInfo":
        updateDatabase()
    else:
        raise HTTPException(status_code=402, detail="Action not found")

    return {"message": f"Action {actionID} received"}