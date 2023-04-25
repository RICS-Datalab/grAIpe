import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel 
import requests
import shutil
import rasterio
from rasterio.enums import Resampling
from enum import Enum

app = FastAPI()

class User(BaseModel):
        username: str
        password: str

class Authenticator(BaseModel):
        token: str

class Project(BaseModel):
        name: str
        id: int
        task_id: str

class IndexName(str, Enum):
    all = "all.zip"
    orthophoto_tif = "orthophoto.tif"
    orthophoto_png = "orthophoto.png"
    orthophoto_mbtiles = "orthophoto.mbtiles"
    textured_model = "textured_model.zip"
    georeferenced_model_las = "georeferenced_model.las"
    georeferenced_model_ply = "georeferenced_model.ply"
    georeferenced_model_csv = "georeferenced_model.csv"    

@app.post("/login")
async def auth(user: User):
    res = requests.post('http://localhost:8000/api/token-auth/',
                        data={'username': user.username,
                              'password': user.password}).json()
    token = res['token']
    return token

@app.post("/create_project")
def create_proj(tkn : Authenticator, proj : Project):
    proj_res = requests.post('http://localhost:8000/api/projects/',
                        headers={'Authorization': 'JWT {}'.format(tkn.token)},
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

@app.get("/download/{file}")
def get_orthophoto(proj : Project, file : IndexName):
    res = requests.get("http://localhost:8000/api/projects/{}/tasks/{}/download/{}".format(proj.id, proj.task_id, file),
                    headers={'Authorization': 'JWT {}'.format(proj.token)},
                    stream=True)

@app.get("/index")
def get_index(token, project_id, task_id, export_file, data):

    dsm_wrkr = requests.post('http://localhost:8000/api/projects/{}/tasks/{}/{}/export'.format(project_id, task_id, export_file),
                        headers={'Authorization': 'JWT {}'.format(token)}, data=data).json()
    if export_file == 'orthophoto':
        print(dsm_wrkr)
        print(dsm_wrkr['celery_task_id'])
        wrkr_uuid = dsm_wrkr['celery_task_id']

        #Activate worker
        while True:
            wrkr = requests.get('http://localhost:8000/api/workers/check/{}'.format(wrkr_uuid),
                            headers={'Authorization': 'JWT {}'.format(token)}).json()

            if wrkr['ready'] == True:
                break

        res = requests.get('http://localhost:8000/api/workers/get/{}?filename={}'.format(wrkr_uuid, param.def_ndvi_file),
                        headers={'Authorization': 'JWT {}'.format(token)})
        print(res)
        content = res.content

        # Write the byte string to a local file as binary data
        with open(param.def_ndvi_file, 'wb') as f:
            f.write(content)

@app.get("/dsm_dtm")
def get_dtm_dsm(token, project_id, task_id, file):
    res = requests.get('http://localhost:8000/api/projects/{}/tasks/{}/download/{}.tif'.format(project_id, task_id, file),
                    headers={'Authorization': 'JWT {}'.format(token)})
    print(res)
    content = res.content

    # Write the byte string to a local file as binary data
    with open(file + '.tif', 'wb') as f:
        f.write(content)

@app.get("/full")
def output_creation():
    resample_list2 = ['orthophoto-NDVI_res.tif', 'orthophoto_res.tif']

    source_ortho = 'orthophoto.tif'
    target_ortho = 'orthophoto_res.tif'
    source_index = 'orthophoto-NDVI.tif'
    target_index = 'orthophoto-NDVI_res.tif'
    # copy the file and rename it
    shutil.copyfile(source_ortho, target_ortho)
    shutil.copyfile(source_index, target_index)

    #Resize the smaller images
    for image in resample_list2:
        with rasterio.open(image) as src:
            # Calculate the new dimensions based on the desired scale factor
            scale_factor = 0.5  # For example
            new_width = 5662  #int(src.width * scale_factor)
            new_height = 5022 #int(src.height * scale_factor)

            # Resample the source raster to the new dimensions
            data = src.read(
                out_shape=(src.count, new_height, new_width),
                resampling=Resampling.bilinear
            )

            # Update the profile with the new dimensions and other metadata
            profile = src.profile
            profile.update(width=new_width, height=new_height, transform=src.transform)

            # Write the resampled data to a new tiff file
            with rasterio.open(image, 'w', **profile) as dst:
                dst.write(data)
    
    #create the CHM file
    with rasterio.open('dsm.tif') as src1, rasterio.open('dtm.tif') as src2:
        # Check that both rasters have the same shape
        assert src1.shape == src2.shape, "The rasters must have the same shape"
        
        # Read the data from the first bands of both rasters
        band1 = src1.read(1)
        band2 = src2.read(1)
        
        # Subtract the values from the first band of the second raster from the first band of the first raster
        result = band1 - band2
        
        # Update the profile of the output file with the metadata from the first raster
        profile = src1.profile
        
        # Write the result to a new tif file
        with rasterio.open('chm.tif', 'w', **profile) as dst:
            dst.write(result, 1)
    
    
    # Open the source TIFF files
    src1 = rasterio.open('orthophoto_res.tif')
    src2 = rasterio.open('orthophoto-NDVI_res.tif')
    src3 = rasterio.open('chm.tif')

    # Define the output file
    dst_file = 'final.tif'

    # Create the output file
    with rasterio.open(
        dst_file,
        'w',
        driver='GTiff',
        height=src1.height,
        width=src1.width,
        count=8,  # The number of bands in the output file
        dtype=src1.dtypes[0],
        crs=src1.crs,
        transform=src1.transform
    ) as dst:
        # Write the first band from the first source file to the output file
        dst.write(src1.read(1), 1)
        dst.write(src1.read(2), 2)
        dst.write(src1.read(3), 3)
        dst.write(src1.read(4), 4)
        dst.write(src1.read(5), 5)
        dst.write(src1.read(6), 6)

        # Write the second band from the second source file to the output file
        dst.write(src2.read(1), 7)

        dst.write(src3.read(1), 8)

    # Close the source and destination files
    src1.close()
    src2.close()
    src3.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)