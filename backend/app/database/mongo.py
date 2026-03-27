from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = MongoClient(MONGO_URL)
db = client["rag_chatbot"]

conversations_collection = db["conversations"]
messages_collection = db["messages"]