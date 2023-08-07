from deta import Deta
import json

#get key from DetaBaseKey.txt
with open("DetaBaseKey.txt", "r") as f:
    key = f.read()

deta = Deta(key)
db = deta.Base("elbunquer-api-base")

#Get data from json file
with open("dataJSON/videoInfo.json", "r") as f:
    videoData = json.load(f)["videoData"]

info = {}
for video in videoData:
    #Get season and episode 
    season = video["season"]
    episode = video["episode"]

    #Generate the key
    key = f"s{season}e{episode}"
    # db.put(video, key=key)

    print(f"Uploaded {key} to database")

    #Count how many episodes per season there are
    if f"{season}" not in info:
        info[f"{season}"] = 0

    info[f"{season}"] += 1

print(info)
db.put(info, "info")
