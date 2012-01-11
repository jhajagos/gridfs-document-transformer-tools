"""
The assumption here for testing is that you have a local instance of a MongoDB server
running on a local port with no security enabled. The testing script will first test if the "test_grid_doc_transform" database exists.
 If the DB exists it will first drop the database. The script will create a fresh version of the database "test_grid_doc_transform".
 """

__author__ = 'janos'

import unittest
import GridDocTransform

from pymongo import Connection
from gridfs import GridFS

def connect_to_local_server():
    try:
        connection = Connection()
    except:
        raise RuntimeError, "A MongoDb server is not running  on the local server"
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


    def test_something(self):
        self.assertEqual(True, False)

if __name__ == '__main__':

    unittest.main()
