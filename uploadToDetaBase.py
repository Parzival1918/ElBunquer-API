from deta import Deta
from pathlib import Path

#get key from DetaBaseKey.txt
with open("DetaBaseKey.txt", "r") as f:
    key = f.read()

deta = Deta(key)
db = deta.Base("elbunquer-api-base")

