__author__ = 'janos'
import json
import sys
import pymongo
import gridfs
import os
import mimetypes

def main(configuration,file_names):
    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)

    for file_name in file_names:
        f = open(file_name,"rb")
        file_name_gridfs = os.path.basename(file_name)
        mime_type_file_name = mimetypes.guess_type(file_name)[0]
        print("Uploading '%s'" % file_name)
        gfs.put(f, content_type = mime_type_file_name, filename = file_name_gridfs)
        f.close()

if __name__ == "__main__":
    f = open("config.json")
    config_json = f.read()
    config = json.load(config_json)
    main(config,sys.argv[2:])
