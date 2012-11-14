__author__ = 'janos'

import json
import sys
import pymongo
import gridfs
import os
import mimetypes
import glob
import datetime
import time
import ProcessNewDocumentsInGridFS

def main(configuration,file_names,path):
    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)
    check_file_updates(configuration,file_names,gfs)


#524: detect modified files
def check_file_updates(configuration,files,gfs):
    modified_files = []
    for file in files:
        last_modified_ts = int(os.path.getmtime(os.path.join(path, file)))
        file_name_gridfs = os.path.basename(file)
        if(gfs.exists(filename=file_name_gridfs)):
            f = gfs.get_last_version(file_name_gridfs)
            f_ts = int(f.time_stamp)
            if(last_modified_ts > f_ts):
                f = open(os.path.join(path, file),"rb")
                mime_type_file_name = mimetypes.guess_type(file)[0]
                ts = time.time()
                print("Uploading modified file '%s'" % file)
                gfs.put(f, content_type = mime_type_file_name, filename = file_name_gridfs, time_stamp = ts)
                modified_files.append(file_name_gridfs)
        else:
            file_name_list = []
            f = open(os.path.join(path, file),"rb")
            mime_type_file_name = mimetypes.guess_type(file)[0]
            print("Uploading '%s'" % file)

            #524: add a timestamp field - used for checking file updates
            ts = time.time()
            gfs.put(f, content_type = mime_type_file_name, filename = file_name_gridfs, time_stamp = ts)
            f.close()

    #524: Call ProcessNewDocumentsInGridFS to do the churning and upload updated files into gridfs
    if(len(modified_files)>0):
        ProcessNewDocumentsInGridFS.process_files(modified_files,gfs,configuration["temporary_directory"])
    else:
        files = gfs.list()
        ProcessNewDocumentsInGridFS.process_files(files,gfs,configuration["temporary_directory"])


if __name__ == "__main__":
    config_name = os.path.join(os.path.split(os.path.realpath(__file__))[0],"config.json")
    f = open(config_name)
    config_json = f.read()
    config = json.loads(config_json)
    path = 'C:/Users/janos/workspace/grid-doc-transform/src/test/sampledata'
    files = os.listdir(path)
    main(config,files,path)