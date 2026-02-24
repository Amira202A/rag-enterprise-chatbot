from pymongo import MongoClient
import os

MONGO_URL = "mongodb://mongodb:27017"

client = MongoClient(MONGO_URL)
db = client["rag_chatbot"]
collection = db["chat_history"]