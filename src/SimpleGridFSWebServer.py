from gridfs.errors import NoFile
__author__ = 'janos'

import gridfs
import pymongo
import json
import os
import urlparse

def application(environ, start_response):

    configuration_file = "config.json"
    f = open(configuration_file,'r')
    configuration = json.load(f)

    grid_file_connection = pymongo.Connection(configuration["mongo_file_store"]["server_name"])
    grid_db = grid_file_connection[configuration["mongo_file_store"]["database_name"]]
    gfs = gridfs.GridFS(grid_db)

    query_dictionary = urlparse.parse_qs(environ["QUERY_STRING"])
    uri = environ["PATH_INFO"]
    light_box_signal = "light-box-z"
    focus_signal = "in-focus-z"
    browse_signal = "browse-z"
    browse_on = 0
    light_box_on = 0
    focus_on = 0
    file_serve = 0

    if uri[1:len(light_box_signal) + 1] == light_box_signal:
        filename = uri[len(light_box_signal)+2:] + ".json"
        light_box_on = 1
    elif uri[1:len(focus_signal) + 1] == focus_signal:
        focus_on = 1
        filename = uri[len(focus_signal)+2:] + ".json"
    elif uri[1:len(browse_signal) + 1] == browse_signal:
        browse_on = 1
    else:
        filename = uri[1:]
        file_serve = 1

    if browse_on:
        browse_files = []
        grid_files = gfs.list()
        for grid_file in grid_files:
            if grid_file[-4:] == "json":
                browse_files.append(grid_file[:-5])

        browse_files.sort()
        content = html_header("File browser")
        content += "<body>"
        content += "<ul>"
        for browse_file in browse_files:
            content = generate_browse_content(browse_file, gfs, browse_file[0:browse_file.index(".")]+".free.text.wc.html", browse_file[0:browse_file.index(".")]+".free.text.ne.html", content)

        content += "</body></html>"
        response_headers = [("Content-type", 'text/html')]
        start_response("200 OK", response_headers)
        return [str(content)]

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
            content += light_box_html(file_information["png_tiny"],file_information["original_filename"])
            content += "</body></html>"
        elif focus_on:
            content += html_header("Focus on '" + file_information["original_filename"] + "'")

            if "part" in query_dictionary:
                part = int(query_dictionary["part"][0])
            else:
                part = 0

            content = html_header("Focus on for '" + file_information["original_filename"] + "'")
            content += "<body>"
            content += in_focus_html(part, file_information["png_medium"][part], file_information["png_large"][part],file_information["png_originals"][part], file_information["original_filename"], file_information["pdf_filename"], file_information["txt_filename"], len(file_information["png_originals"]))
            #content += in_focus_html(part, file_information["png_medium"][part], file_information["png_large"][part],file_information["png_originals"][part], file_information["original_filename"], file_information["pdf_filename"], file_information["txt_filename"], file_information["ft_wc_filename"], file_information["ft_ne_filename"], len(file_information["png_originals"]), gfs)
            #content += in_focus_html(part, '','','', file_information["original_filename"], file_information["pdf_filename"], file_information["txt_filename"], file_information["ft_wc_filename"], file_information["ft_ne_filename"], len(file_information["png_originals"]), gfs)
            content += "</body></html>"

        return [str(content),]

#524
def generate_browse_content(browse_file, gfs, ft_wc_filename, ft_ne_filename, content):
    print ft_wc_filename
    print ft_ne_filename
    wc_file=gfs.get_last_version(ft_wc_filename)
    wc_html=wc_file.read()

    ne_file=gfs.get_last_version(ft_ne_filename)
    ne_html=ne_file.read()

    content += '<li><a href = "../in-focus-z/%s">%s</li>' % (browse_file,browse_file)
    content += "<div><span>Insights:"+wc_html.decode('utf8','ignore') +ne_html.decode('utf8','ignore')+"</span></div>"

    return content

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

#def in_focus_html(current_position, image_file_medium, image_file_large,image_file_name,original_file_name, pdf_file_name, text_file_name, wc_file_name, ne_file_name, number_of_parts, gfs):
def in_focus_html(current_position, image_file_medium, image_file_large,image_file_name,original_file_name, pdf_file_name, text_file_name, number_of_parts):

    '''f=gfs.get_last_version(wc_file_name)
    wc_html=f.read()
    
    ne_file=gfs.get_last_version(ne_file_name)
    ne_html=ne_file.read()'''

    state = "middle"
    if current_position == 0:
        state = "start"
    elif current_position == number_of_parts - 1:
        state = "end"

    if state ==  "end":
        next = None
    else:
        next = "?part=%s" % (int(current_position) + 1)

    if state == "start":
        previous = None
    else:
        previous = "?part=%s" %  (int(current_position) - 1)

    html_text = '<div><span>Formats: <a href="../%s">Original format</a> | <a href="../%s">PDF</a> | <a href="/light-box-z/%s">Thumbnails</a>| <a href = "../%s">Image </a> | <a href="../%s">Text</a></span></div>' % (original_file_name, pdf_file_name, original_file_name, image_file_name, text_file_name)

    html_text += '<div><span>Navigation: '
    if next:
        html_text += '<a href="%s">Next</a>' % next
    else:
        html_text += "Next"
    if previous:
        html_text += ' | <a href="%s">Previous</a>' % previous
    else:
        html_text += " | Previous"
    first = "?part=0"
    last = "?part=%s" % (int(number_of_parts) - 1)
    html_text += '   |||   <a href="%s">First</a> | <a href="%s">Last</a> |' % (first,last)

    html_text += '<div><span><a href="../%s"><img src="../%s"></a></span></div></br>' % (image_file_name, image_file_large)
    #html_text += "<div><span>Insights:"+wc_html +ne_html+"</span></div>"
    return html_text

def light_box_html(image_files_list_thumb, original_file_name, n=3):
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
        html_text += '<span><a href="/in-focus-z/%s?part=%s"><img src="../%s"/></a></span>' % (original_file_name,i,image_files_list_thumb[i])

    if i % n != 0:
        html_text += "</div>\n"
    return html_text

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    os.environ["CONFIGURATION_FILE"] = "config.json"
    server = make_server('localhost', 9001, application)
    server.serve_forever()
