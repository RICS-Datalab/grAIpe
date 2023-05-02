import uvicorn
from typing import Annotated, Optional
from fastapi import FastAPI, Header, UploadFile, Body
from fastapi.responses import FileResponse
import jwt
from pydantic import BaseModel 
import requests
import shutil
import rasterio
from rasterio.enums import Resampling
from enum import Enum

app = FastAPI()

JWT_SECRET = "secret" # IRL we should NEVER hardcode the secret: it should be an evironment variable!!!
JWT_ALGORITHM = "HS256"

class User(BaseModel):
        username: str
        password: str

class Authenticator(BaseModel):
        token: str

class Project(BaseModel):
        project_id: int
        task_id: str

class FileName(str, Enum):
    all = "all.zip"
    orthophoto_tif = "orthophoto.tif"
    orthophoto_png = "orthophoto.png"
    orthophoto_mbtiles = "orthophoto.mbtiles"
    textured_model = "textured_model.zip"
    georeferenced_model_las = "georeferenced_model.las"
    georeferenced_model_ply = "georeferenced_model.ply"
    georeferenced_model_csv = "georeferenced_model.csv"    

class IndexName(str, Enum):
     ndvi = "NDVI" 
     ndyi = "NDYI" 
     ndre = "NDRE" 
     ndwi = "NDWI" 
     endvi = "ENDVI" 
     vndvi = "vNDVI" 
     vari ="VARI" 
     exg = "EXG" 
     tgi = "TGI" 
     bai = "BAI" 
     gli = "GLI"
     gndvi = "GNDVI" 
     grvi = "GRVI"
     savi = "SAVI"
     mnli = "MNLI"
     ms = "MS"
     rdvi = "RDVI"
     tdvi = "TDVI" 
     osavi = "OSAVI"
     lai = "LAI"
     evi = "EVI"
     arvi = "ARVI"

class MapName(str, Enum):
     dsm = "DSM"
     dtm = "DTM"

class Data(BaseModel):
    color_map: str = Body('spectral')
    formula: str = Body('NDVI')
    bands: str = Body('RGBNRe')
    hillshade: str = Body('')
    rescale: str = Body('-1%2C1')
    size: str = Body('512')
    format: str = Body('gtiff')
    epsg: str = Body('32629')

#HELPERS
def orthophoto(project, task, file, authorization):
    res = requests.get("http://localhost:8000/api/projects/{}/tasks/{}/download/{}".format(project, task, file),
                    headers={'Authorization': 'JWT {}'.format(authorization)},
                    stream=True)
    
    return res

def dtm_dsm_chm(project, task, file, authorization):
    filedict = {
        'DSM' : "dsm",
        'DTM' : "dtm",
    }
    fileName = filedict[file]
    
    res = requests.get('http://localhost:8000/api/projects/{}/tasks/{}/download/{}.tif'.format(project, task, fileName),
                    headers={'Authorization': 'JWT {}'.format(authorization)})
    print(res)
    content = res.content

@app.post("/login")
async def auth(user: User):
    res = requests.post('http://localhost:8000/api/token-auth/',
                        data={'username': user.username,
                              'password': user.password}).json()
    token = res['token']
    return token

@app.post("/create_project/{name}")
async def create_proj(name, Authorization: Annotated[str | None, Header()] = None):
    proj_res = requests.post('http://localhost:8000/api/projects/',
                        headers={'Authorization': 'JWT {}'.format(Authorization)},
                        data={'name': name}).json()

    project_id = proj_res['id']
    return project_id

# depois tentar com JWT
@app.get("/list_projects")
async def list_projs(Authorization: Annotated[str | None, Header()] = None):
    res = requests.get('http://localhost:8000/api/projects/', headers={'Authorization': 'JWT {}'.format(Authorization)})
    return res.json()

#melhorar isso aqui
@app.post("/create_execute_task/{project}}")
async def create_execute_task(project, images, file: UploadFile, Authorization: Annotated[str | None, Header()] = None):
    res = requests.post('http://localhost:8000/api/projects/{}/tasks/'.format(project), 
                headers={'Authorization': 'JWT {}'.format(Authorization)},
                files=file,
                data={
                    'options': options
                }).json()

    print(res)
    task_id = res['id']

    return task_id
####################

@app.get("/download/{project}/{task}/{file}")
async def get_orthophoto(project, task, file : FileName, Authorization: Annotated[str | None, Header()] = None):
    res = orthophoto(project, task, file, Authorization)
    
    with open(file, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return FileResponse("{}".format(file), filename=file)

@app.post("/index/{project}/{task}/{index}")
async def get_index(project, task, index : IndexName, data: Optional[Data], Authorization: Annotated[str | None, Header()] = None):
    indexdict = {
        'NDVI' :"orthophoto-NDVI.tif",
        'NDYI' : "orthophoto-NDYI.tif", 
        'NDRE' : "orthophoto-NDRE.tif", 
        'NDWI' : "orthophoto-NDWI.tif", 
        'VNDVI' : "orthophoto-vNDVI.tif", 
        'ENDVI' : "orthophoto-ENDVI.tif", 
        'VARI' :"orthophoto-VARI.tif", 
        'EXG' : "orthophoto-EXG.tif", 
        'TGI' : "orthophoto-TGI.tif", 
        'BAI' : "orthophoto-BAI.tif", 
        'GLI' : "orthophoto-GLI.tif",
        'GNDVI' : "orthophoto-GNDVI.tif", 
        'GRVI' : "orthophoto-GRVI.tif",
        'SAVI' : "orthophoto-SAVI.tif",
        'MNLI' : "orthophoto-MNLI.tif",
        'MS' : "orthophoto-MS.tif",
        'RDVI' : "orthophoto-RDVI.tif",
        'TDVI' : "orthophoto-TDVI.tif", 
        'OSAVI' : "orthophoto-OSAVI.tif",
        'LAI' : "orthophoto-LAI.tif",
        'EVI' : "orthophoto-EVI.tif",
        'ARVI' : "orthophoto-ARVI.tif",
    }

    data_index = {
        'color_map': data.color_map,
        'formula': index,
        'bands': data.bands,
        'hillshade': data.hillshade,
        'rescale': data.rescale,
        'size': data.size,
        'format': data.format,
        'epsg': data.epsg
    }

    print(index)

    dsm_wrkr = requests.post('http://localhost:8000/api/projects/{}/tasks/{}/orthophoto/export'.format(project, task),
                        headers={'Authorization': 'JWT {}'.format(Authorization)}, data=data_index).json()
    
    print(dsm_wrkr)
    print(dsm_wrkr['celery_task_id'])
    wrkr_uuid = dsm_wrkr['celery_task_id']
    #Activate worker
    while True:
        wrkr = requests.get('http://localhost:8000/api/workers/check/{}'.format(wrkr_uuid),
                        headers={'Authorization': 'JWT {}'.format(Authorization)}).json()

        if wrkr['ready'] == True:
            break

    print("KUNAMI")
    index_file = indexdict[index]
    print(index_file)
    res = requests.get('http://localhost:8000/api/workers/get/{}?filename={}'.format(wrkr_uuid, index_file),
                    headers={'Authorization': 'JWT {}'.format(Authorization)})
    print(res)
    content = res.content

    # Write the byte string to a local file as binary data
    with open(index_file, 'wb') as f:
        f.write(content)

    return FileResponse("{}".format(index_file), filename=index_file)

@app.get("/dsm_dtm_chm/{project}/{task}/{file}")
async def get_dtm_dsm_chm(project, task, file : MapName, Authorization: Annotated[str | None, Header()] = None):
    
    res = dtm_dsm_chm(project, task, file, Authorization)
    
    content = res.content

    # Write the byte string to a local file as binary data
    with open(file + '.tif', 'wb') as f:
        f.write(content)

    return FileResponse("{}".format(file + '.tif'), filename=file + '.tif')

@app.get("/full/{project}/{task}")
async def output_creation(project, task, file : FileName, Authorization: Annotated[str | None, Header()] = None):
    
    res = orthophoto(project, task, file, Authorization)
    with open(file, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
    dsm = dtm_dsm_chm(project, task, 'dsm', Authorization)
    dsmContent = dsm.content
    with open('dsm.tif', 'wb') as f:
        f.write(dsmContent)

    dtm = dtm_dsm_chm(project, task, 'dtm', Authorization)
    dtmContent = dtm.content
    with open('dtm.tif', 'wb') as f:
        f.write(dtmContent)

    resample_list2 = ['orthophoto-NDVI.tif', 'orthophoto.tif']
    '''
    source_ortho = 'orthophoto.tif'
    target_ortho = 'orthophoto_res.tif'
    source_index = 'orthophoto-NDVI.tif'
    target_index = 'orthophoto-NDVI_res.tif'
    # copy the file and rename it
    shutil.copyfile(source_ortho, target_ortho)
    shutil.copyfile(source_index, target_index)
    '''
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