"""
The assumption here for testing is that you have a local instance of a MongoDB server running on a local port with no
username and password. The testing script will first test if the "test_grid_doc_transform" database exists.
If the DB exists it will first drop the database. The script will create a fresh version of the database
"test_grid_doc_transform".
 """

__author__ = 'janos'

import unittest
import GridDocTransform
import mimetypes
from pymongo import Connection
from gridfs import GridFS
import os
import pprint

def connect_to_local_server():
    try:
        connection = Connection()
    except:
        raise RuntimeError, "A MongoDB server instance is not running locally"
    return connection

def create_new_database_or_clobber(connection):
    if "test_grid_doc_transform" in connection.database_names():
        connection.drop_database("test_grid_doc_transform")
    cursor = connection["test_grid_doc_transform"]
    return cursor

def create_gridfs(cursor):
    return GridFS(cursor)


class BasicGridFSManipulation(unittest.TestCase):
    def setUp(self):
        self.connection = connect_to_local_server()
        self.cursor = create_new_database_or_clobber(self.connection)
        self.gridFS = create_gridfs(self.cursor)

        file_names = ["Much Ado About Nothing by Shakespeare.doc","Much Ado About Nothing by Shakespeare.docx","Sample Presentation Plain Background.pptx","Sample Presentation Plain Background.ppt","sample-pdf-document-with-ocr.pdf","6525_Page_4.png"]
        self.file_names = file_names

        for file_name in file_names:
            mime_type_file_name = mimetypes.guess_type(file_name)[0]
            f = open(file_name,'rb')
            self.gridFS.put(f.read(-1), content_type = mime_type_file_name, filename = file_name)
            f.close()

        temp_directory = os.path.abspath("temp")
        self.file_churner = GridDocTransform.FileChurner(self.gridFS,temp_directory)

#    def test_process_word_file(self):
#        self.file_churner.process_file("Much Ado About Nothing by Shakespeare.doc")
#    def test_process_pdf_file(self):
#        self.file_churner.process_file("sample-pdf-document-with-ocr.pdf")
#    def test_process_ppt_file(self):
#        self.file_churner.process_file("Sample Presentation Plain Background.pptx")
#    def test_process_png_file(self):
#        self.file_churner.process_file("6525_Page_4.png")

    def test_process_document_to_endpoint(self):
        document_details = self.file_churner.process_document_to_endpoint("Sample Presentation Plain Background.pptx")
        pprint.pprint(document_details)
        self.assertTrue(document_details.has_key("txt_filename"))


if __name__ == '__main__':

    unittest.main()
