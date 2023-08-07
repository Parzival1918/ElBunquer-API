from fastapi import FastAPI, HTTPException

from typing import Union

import json
from random import choice
from deta import Deta

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
        "name": "Informació episodis",
        "description": "Obté informació d'un episodi del podcast.",
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

@app.get("/info-episodi/{temporada}/{episodi}", tags=["Informació episodis"])
def info_episodi_per_temporada(temporada: int, episodi: int):
    #Get from Deta base
    key = f"s{temporada}e{episodi}"
    data = db.get(key=key)
    if data is None:
        raise HTTPException(status_code=400, detail="L'episodi i/o la temporada no existeix")
    
    return data

@app.get("/info-episodi/random", tags=["Informació episodis"])
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
