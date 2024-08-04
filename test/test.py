
import requests

MAX_REQUESTS = 100000

data = {}

for i in range(MAX_REQUESTS):
    response = requests.get('http://localhost:8000')
    id = response.json()["id"]
    if data.get(id):
        data[id] += 1
    else:    
        data[id] = 1    
    
print(data) 
    