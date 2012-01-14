__author__ = 'janos'


import gridfs
import pymongo
import json
import os
import pprint

def application(environ, start_response):
    pprint.pprint(environ)

    #environ["CONFIGURATION_FILE"]
    configuration_file = "config.json"
    f = open(configuration_file,'r')
    configuration = json.load(f)

    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)

    filename = environ["PATH_INFO"][1:]
    grid_out_obj = gfs.get_last_version(filename)

    response_headers = [
        ("Content-type", str(grid_out_obj.content_type)),
        ("Content-length",str(grid_out_obj.length)),
    ]

    start_response("200 OK", response_headers)
    return [grid_out_obj.read(),]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    os.environ["CONFIGURATION_FILE"] = "config.json"
    server = make_server('localhost', 9001, application)
    server.serve_forever()
