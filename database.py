import pymongo
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
client = pymongo.MongoClient(mongo_uri)
db = client["edusummarize"]
summaries_collection = db["edusummarize"]

def get_existing_files():
    return list(summaries_collection.find())

def delete_file(filename):
    summaries_collection.delete_one({"filename": filename})
