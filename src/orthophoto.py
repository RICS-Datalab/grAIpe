import json
import requests

def Orthophoto(project, task, file, authorization):
    res = requests.get("http://localhost:8000/api/projects/{}/tasks/{}/download/{}".format(project, task, file),
                    headers={'Authorization': 'JWT {}'.format(authorization)},
                    stream=True)
    
    return res

def Index_creation(project, task, index, data, Authorization):
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

    index_file = indexdict[index]
    print(index_file)
    res = requests.get('http://localhost:8000/api/workers/get/{}?filename={}'.format(wrkr_uuid, index_file),
                    headers={'Authorization': 'JWT {}'.format(Authorization)})
    print(res)
    content = res.content
    #with open(index_file, 'wb') as f:
    #    f.write(content)
    return content
    
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
    return content

def optionsListCreation(data):
    options_list = []
    if data == None:
        orthophoto_set = {'name': "orthophoto-resolution", 'value': 24}
        autobound_set = {"name":"auto-boundary","value": True}
        dsm_set = {"name":"dsm","value":True}
        dtm_set = {"name":"dtm","value":True}

        options_list.append(orthophoto_set)
        options_list.append(autobound_set)
        options_list.append(dsm_set)
        options_list.append(dtm_set)

        options_final = json.dumps(options_list)
        print(options_list)
        return options_final
        
    else:
        option = json.loads(data)
        for options in option['options']: 
            if options["value"] == "true":
                options["value"] = True
            elif options["value"] == "false":
                options["value"] = False
            else:
                options["value"] = int(options["value"])
            options_list.append({"name":options["name"],"value":options["value"]})
            options_final = json.dumps(options_list)

        return options_final
