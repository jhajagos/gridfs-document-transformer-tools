import json
import sys
import pymongo
import gridfs
import os
import mimetypes
import GridDocTransform

def main(configuration):
    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)
    temp_directory = configuration["temporary_directory"]
    gfs_files = gfs.list() #This will not scale
    json_files = {}
    for gfs_file in gfs_files:
        if gfs_file[-4:] == "json":
            json_files[gfs_file[:-4]] = 1

    pdf_files = {}
    for gfs_file in gfs_files:
        if gfs_file[-3:] == "pdf":
            pdf_files[gfs_file] = 1

    document_files_to_process = {}
    for gfs_file in gfs_files:
        if gfs_file[-4:] == ".":
            extension = gfs_file[-3:]
        elif gfs_file[-5:] == ".":
            extension = gfs_file[-4:]

        if extension in ["doc","docx","ppt","pptx"]:
            if gfs_file + ".pdf" in pdf_files:
                pdf_files.pop(gfs_file + ".pdf")
            if gfs_file not in json_files:
                document_files_to_process[gfs_file] = 1
    for pdf_file in pdf_files.keys():
        if pdf_file not in json_files:
            document_files_to_process[pdf_file] = 1

    file_churner_obj = GridDocTransform.FileChurner(gfs, temp_directory)
    for file_name in document_files_to_process.keys():
        print("Processing file '%s'" % file_name)
        file_churner_obj.process_document_to_endpoint(file_name)

if __name__ == "__main__":
    f = open("config.json")
    config_json = f.read()
    config = json.load(config_json)
    main(config,sys.argv[2:])