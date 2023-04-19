import requests
import os
import json
import sys
import time
import argparse
import param
import shutil
import rasterio
from rasterio.enums import Resampling


parser = argparse.ArgumentParser()

parser.add_argument("--name", help = "project_name")
parser.add_argument("--folder", help = "/path/to/image/folder/")
parser.add_argument("--indexes", nargs="*", default= ['NDVI'],  help = "Availble indexes: NDVI, NDYI. NDRE, NDWI, ENDVI, vNDVI, VARI, EXG, TGI, BAI, GLI, GNDVI, GRVI, SAVI, MNLI, MS, RDVI, TDVI, OSAVI, LAI, EVI, ARVI")

args = parser.parse_args()

param.proj_name = args.name 

options_list = []

orthophoto_set = {'name': "orthophoto-resolution", 'value': 24}
autobound_set = {"name":"auto-boundary","value":True}
dsm_set = {"name":"dsm","value":True}
dtm_set = {"name":"dtm","value":True}

options_list.append(orthophoto_set)
options_list.append(autobound_set)
options_list.append(dsm_set)
options_list.append(dtm_set)


# Authentication
def auth():
    res = requests.post('http://localhost:8000/api/token-auth/',
                        data={'username': param.user,
                              'password': param.passw}).json()
    token = res['token']
    return token


# Create a project
def create_proj(token, proj_name):
    proj_res = requests.post('http://localhost:8000/api/projects/',
                        headers={'Authorization': 'JWT {}'.format(token)},
                        data={'name': param.proj_name }).json()

    project_id = proj_res['id']
    return project_id

directory_path = "images/"                                                         #param here

# Create an image list to send to the project
def image_list(directory_path):

    file_list = []

    for filename in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, filename)):
            file_list.append(directory_path + filename)

    images = []

    for item in file_list:
        with open(item, 'rb') as f:
            images.append(('images', (item, f.read(), 'image/tif')))
    
    return images

options = json.dumps(options_list)

# Create a task and execute it with the chosen options
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

# Verify the execution state of the task
def task_verification(token, project_id, task_id):
    while True:
        res = requests.get('http://localhost:8000/api/projects/{}/tasks/{}/'.format(project_id, task_id),
                        headers={'Authorization': 'JWT {}'.format(token)}).json()
        
        print(res['running_progress'])

        if res['running_progress'] == 1:
            print("Task has completed!")
            break
        else:
            print("Processing, hold on...")
            time.sleep(3)

######################################

# Obtain the orthophoto
def get_orthophoto(token, project_id, task_id):
    res = requests.get("http://localhost:8000/api/projects/{}/tasks/{}/download/orthophoto.tif".format(project_id, task_id),
                    headers={'Authorization': 'JWT {}'.format(token)},
                    stream=True)
    with open("orthophoto.tif", 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
        src = rasterio.open('orthophoto.tif')

        print(src.meta)
        print(src.descriptions)

# Obtain index (OSAVI)

#API request to create the worker
                                                        #orthophoto/dsm/dtm
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

#API request to get the file

def get_dtm_dsm(token, project_id, task_id, file):
    res = requests.get('http://localhost:8000/api/projects/{}/tasks/{}/download/{}.tif'.format(project_id, task_id, file),
                    headers={'Authorization': 'JWT {}'.format(token)})
    print(res)
    content = res.content

    # Write the byte string to a local file as binary data
    with open(file + '.tif', 'wb') as f:
        f.write(content)

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

def main():
    index = 'SAVI'
    color_map = 'spectral'

    data = {
    'color_map': '',
    'formula': '',
    'bands': '',
    'hillshade': '',
    'rescale': '-1%2C1',
    'size': '512',
    'format': 'gtiff-rgb',
    'epsg': '32629'
    }

    data_index = {
    'color_map': color_map,
    'formula': index,
    'bands': 'RGBNRe',
    'hillshade': '',
    'rescale': '-1%2C1',
    'size': '512',
    'format': 'gtiff',
    'epsg': '32629'
}

    data_dtm = {
    'color_map': 'viridis',
    'formula': '',
    'bands': '',
    'hillshade': '6',
    'rescale': '-1%2C1',
    'size': '512',
    'format': 'gtiff', #sem rgb - com rgb meter 'gtiff-rgb'
    'epsg': '32629'
}

    data_dsm = {
    'color_map': 'terrain',
    'formula': '',
    'bands': '',
    'hillshade': '6',
    'rescale': '-1%2C1',
    'size': '512',
    'format': 'gtiff',
    'epsg': '32629'
}

    token = auth()
    project_id = create_proj(token, args.name)
    images = image_list(args.folder)
    task_id = create_execute_task(token, project_id, images)
    task_verification(token, project_id, task_id)
    get_orthophoto(token, project_id, task_id)
    get_index(token, project_id, task_id, 'orthophoto', data_index)
    get_dtm_dsm(token, project_id, task_id, 'dsm')
    get_dtm_dsm(token, project_id, task_id, 'dtm')
    output_creation()

if __name__ == "__main__":
    main()
