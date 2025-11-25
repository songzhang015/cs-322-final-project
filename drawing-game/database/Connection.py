import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
import json

load_dotenv()

class Connection:

    def __init__(self):
        self.__connection = self.__init_conn()
        self.db = self.__connection["db"]
        self.packs_collection = self.db["packs"]

    def __init_conn(self):
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/appdb")
        return MongoClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where()
        )

    def gather_session(self):
        return self.__connection
