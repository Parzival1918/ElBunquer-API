from deta import Deta

# Initialize with a Project Key from DetaBaseKey.txt
with open("DetaBaseKey.txt") as f:
    Detakey = f.read()
    
deta = Deta(Detakey)
db = deta.Base("elbunquer-api-base")

res = db.fetch(query={"episode": 2}) #Fetch episodes that have episode number 2
print(res.items)