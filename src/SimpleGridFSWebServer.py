from gridfs.errors import NoFile

__author__ = 'janos'


import gridfs
import pymongo
import json
import os
import pprint

def application(environ, start_response):

    #environ["CONFIGURATION_FILE"]
    configuration_file = "config.json"
    f = open(configuration_file,'r')
    configuration = json.load(f)

    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)

    uri = environ["PATH_INFO"]
    light_box_signal = "light-box-z"
    focus_z_signal = "focus-signal-z"
    light_box_on = 0
    focus = 0
    file_serve = 0
    if uri[1:len(light_box_signal) + 1] == light_box_signal:
        filename = uri[len(light_box_signal)+2:] + ".json"
        light_box_on = 1
    elif uri[1:len(focus_z_signal)] == focus_z_signal:
        focus = 1
    else:
        filename = uri[1:]
        file_serve = 1

    try:
        grid_out_obj = gfs.get_last_version(filename)
    except NoFile:
        start_response("404 Not Found", [("Content-type","text/plain")])
        return ['File not found',]

    if file_serve:
        response_headers = [
            ("Content-type", str(grid_out_obj.content_type)),
            ("Content-length",str(grid_out_obj.length)),
        ]

        start_response("200 OK", response_headers)
        return grid_out_obj #GridFs is an iterable object
    else:
        json_response = grid_out_obj.read()
        file_information = json.loads(json_response)
        content = ""
        response_headers = [("Content-type", 'text/html')]


        start_response("200 OK", response_headers)
        if light_box_on:
            content = html_header("Light box on for '" + file_information["original_filename"] + "'")
            content += "<body>"
            content += light_box_html(file_information["png_tiny"],file_information["png_large"])
            content += "</body></html>"
        elif focus:
            pass

        return [str(content),]

def html_header(title):
    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" dir="ltr" class="client-nojs" xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%s</title>
</head>
    """ % title

def close_html():
    return "</html>"

def open_body():
    return "<body>"

def close_body():
    return "</body>"

def light_box_html(image_files_list_thumb, image_files_list_full, n=3):
    i = 0
    html_text = ""
    for i in range(len(image_files_list_thumb)):
        if i % n == 0:
            if i == 0:
                html_text += "<div>\n"
            elif i == len(image_files_list_thumb) - 1:
                html_text += "</div>\n"
            else:
                html_text += "</div>\n<div>"
        html_text += '<span><a href="../%s"><img src="../%s"/></a></span>' % (image_files_list_full[i],image_files_list_thumb[i])

    if i % n != 0:
        html_text += "</div>\n"
    return html_text

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    os.environ["CONFIGURATION_FILE"] = "config.json"
    server = make_server('localhost', 9001, application)
    server.serve_forever()
