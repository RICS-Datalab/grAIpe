import uvicorn
from fastapi import FastAPI
import requests

app = FastAPI()


@app.get("/auth")
def auth():
    res = requests.post('http://localhost:8000/api/token-auth/',
                        data={'username': param.user,
                              'password': param.passw}).json()
    token = res['token']
    return token


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)