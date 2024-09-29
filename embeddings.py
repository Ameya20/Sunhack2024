import os
import pinecone
import tiktoken
import pymongo
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from pinecone import ServerlessSpec  # Ensure this is imported

# Load environment variables
load_dotenv()

# MongoDB and Pinecone setup
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE"))  # Adjust if necessary
NAMESPACE = os.getenv("UUID_NAMESPACE", None)

# Initialize MongoDB connection
client = pymongo.MongoClient(MONGO_URI)
db = client["edusummarize"]
summaries_collection = db["edusummarize"]

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Check if the index exists, create it if not
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,  # Adjust based on the embedding model
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-west-2')
    )

# Connect to the Pinecone index
pinecone_index = pc.Index(PINECONE_INDEX)

# Initialize OpenAI embeddings model
embedding_model_name = "text-embedding-ada-002"  # Ensure this matches the index dimension
embedding_model = OpenAIEmbeddings(model=embedding_model_name)  

# Function to fetch the summary, generate embeddings, store in Pinecone, and update MongoDB
def process_file_and_store_embeddings(file_id):
    try:
        # Fetch the document from MongoDB using file_id
        print(f"Looking for document with filename: '{file_id}'")
        document = summaries_collection.find_one({"filename": file_id})

        if not document:
            print('Document not found')
            return

        print('Document found:', document)
        summary = document["summary"]

        # Generating embeddings
        embeddings = embedding_model.embed_query(summary)
        
        print("Embedding shape:", len(embeddings))  # Ensure this matches the expected dimension

        # Add document (embedding) to Pinecone
        upsert_response = pinecone_index.upsert(
            [(str(document["_id"]), embeddings)]  
        )

        # Check if the upsert was successful
        if upsert_response.upserted_count > 0:  # Check for upserted count
            print(f"Embeddings stored in Pinecone for document ID: {document['_id']}")
            # Update the document in MongoDB with the Pinecone embedding ID
            summaries_collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"pinecone_id": str(document["_id"])}}  # Update with the ID used in Pinecone
            )
            print("MongoDB updated with Pinecone embedding ID.")
        else:
            print("Failed to store embeddings in Pinecone.")

    except Exception as e:
        print(f"Error processing file and storing embeddings: {str(e)}")

file_id = "newFile123"
process_file_and_store_embeddings(file_id)
