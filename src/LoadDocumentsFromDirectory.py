__author__ = 'janos'

import json
import sys
import pymongo
import gridfs
import os
import mimetypes
import glob

def main(configuration,file_names):
    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)

    file_name_list = []
    for file_name in file_names:
        if "*" in file_name:
            file_names_expanded = glob.glob(file_name)
            for file_name_expanded in file_names_expanded:
                file_name_list.append(file_name_expanded)
        else:
            file_name_list.append(file_name)

    for file_name in file_name_list:
        f = open(file_name,"rb")
        file_name_gridfs = os.path.basename(file_name)
        mime_type_file_name = mimetypes.guess_type(file_name)[0]
        print("Uploading '%s'" % file_name)
        gfs.put(f, content_type = mime_type_file_name, filename = file_name_gridfs)
        f.close()

if __name__ == "__main__":
    config_name = os.path.join(os.path.split(os.path.realpath(__file__))[0],"config.json")
    f = open(config_name)
    config_json = f.read()
    config = json.loads(config_json)
    main(config,sys.argv[1:])