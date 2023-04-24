import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel 
import requests


app = FastAPI()

class User(BaseModel):
        username: str
        password: str

class Project(BaseModel):
        name: str
        token: str

@app.post("/authentication")
async def auth(user: User):
    res = requests.post('http://localhost:8000/api/token-auth/',
                        data={'username': user.username,
                              'password': user.password}).json()
    token = res['token']
    return token

@app.post("/create_project")
def create_proj(proj : Project):
    proj_res = requests.post('http://localhost:8000/api/projects/',
                        headers={'Authorization': 'JWT {}'.format(proj.token)},
                        data={'name': proj.name}).json()

    project_id = proj_res['id']
    return project_id

#melhorar isso aqui
@app.post("/create_execute_task")
def create_execute_task(token, project_id, images):
    res = requests.post('http://localhost:8000/api/projects/{}/tasks/'.format(project_id), 
                headers={'Authorization': 'JWT {}'.format(token)},
                files=images,
                data={
                    'options': options
                }).json()

    print(res)
    task_id = res['id']

    return task_id
####################

@app.get("/orthophoto")
def get_orthophoto(token, project_id, task_id):
    res = requests.get("http://localhost:8000/api/projects/{}/tasks/{}/download/orthophoto.tif".format(project_id, task_id),
                    headers={'Authorization': 'JWT {}'.format(token)},
                    stream=True)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)