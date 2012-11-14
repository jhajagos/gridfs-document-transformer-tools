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

    #524
    process_files(gfs_files,gfs,temp_directory)



#524
def process_files(files,gfs,temp_directory):
    json_files = {}
    for file in files:
        if file[-4:] == "json":
            json_files[file[:-5]] = 1

    pdf_files = {}
    for file in files:
        if file[-3:] == "pdf":
            pdf_files[file] = 1

    document_files_to_process = {}
    for file in files:
        if file[-4:][0] == ".":
            extension = file[-3:]
        elif file[-5:][0] == ".":
            extension = file[-4:]
        else:
            extension = None
        if extension:
            if extension in ["doc","docx","ppt","pptx"]:
                if file + ".pdf" in pdf_files:
                    pdf_files.pop(file + ".pdf")
                if file not in json_files:
                    document_files_to_process[file] = 1

    for pdf_file in pdf_files.keys():
        if pdf_file not in json_files:
            document_files_to_process[pdf_file] = 1

    file_churner_obj = GridDocTransform.FileChurner(gfs, temp_directory)
    for file_name in document_files_to_process.keys():
        print("Processing file '%s'" % file_name)
        file_churner_obj.process_document_to_endpoint(file_name)



if __name__ == "__main__":
    config_name = os.path.join(os.path.split(os.path.realpath(__file__))[0],"config.json")
    f = open(config_name)
    config_json = f.read()
    config = json.loads(config_json)
    main(config)