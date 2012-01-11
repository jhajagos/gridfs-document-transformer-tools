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

        file_names = ["Much Ado About Nothing by Shakespeare.docx","Sample Presentation Plain Background.pptx","sample-pdf-document-with-ocr.pdf"]

        for file_name in file_names:
            mime_type_file_name = mimetypes.guess_type(file_name)[0]
            with open(file_name) as test_file:
                oid = self.gridFS.put(test_file, content_type = mime_type_file_name, filename = file_name)

        print(self.gridFS.list())

    def test_something(self):
        self.assertEqual(True, True)

if __name__ == '__main__':

    unittest.main()
