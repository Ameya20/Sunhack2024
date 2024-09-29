import os
import pinecone
import pymongo
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from pinecone import ServerlessSpec
import openai
import asyncio

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

# Initialize Pinecone client
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Check if the index exists, create it if not
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=EMBEDDING_SIZE,  # Use the correct dimension size
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-west-2')
    )

# Connect to the Pinecone index
pinecone_index = pc.Index(PINECONE_INDEX)

# Initialize OpenAI embeddings model
embedding_model_name = "text-embedding-ada-002"
embedding_model = OpenAIEmbeddings(model=embedding_model_name)

# Function to retrieve embeddings using pinecone_id
def fetch_embedding_from_pinecone(pinecone_id):
    try:
        response = pinecone_index.fetch([pinecone_id])
        if "vectors" in response and pinecone_id in response["vectors"]:
            embedding = response["vectors"][pinecone_id]["values"]
            return embedding
        else:
            return None
    except Exception as e:
        print(f"Error fetching embedding from Pinecone: {str(e)}")
        return None

# Function to retrieve relevant documents based on user query
def retrieve_relevant_documents(user_query, file_name):
    try:
        document = summaries_collection.find_one({"filename": file_name})
        if not document:
            print('Document not found')
            return []

        pinecone_id = document.get("pinecone_id")
        if not pinecone_id:
            print(f"No pinecone_id found for the file '{file_name}'.")
            return []

        embedding = fetch_embedding_from_pinecone(pinecone_id)
        if embedding is None:
            print("No embedding found for the provided pinecone_id.")
            return []

        # Correctly reference the index name
        vector_store = LangchainPinecone.from_existing_index(
            index_name=PINECONE_INDEX,
            embedding=embedding_model,
            text_key="text",
            namespace=NAMESPACE
        )

        # Create a retriever from the vector store
        retriever = vector_store.as_retriever(top_k=None)  # Change this line


        # Use the retriever to get relevant documents
        relevant_docs = retriever.get_relevant_documents(user_query)

        if retriever:
            return retriever
        else:
            print("No relevant documents found.")
            return []

    except Exception as e:
        print(f"Error retrieving relevant documents: {str(e)}")
        return []



# Function to extract content from relevant documents
def extract_docs(source_docs):
    return [source_doc.page_content for source_doc in source_docs]

# Function to build the prompt
def build_prompt(docs, question):
    prompt = f"Context section:\n" + "\n-\n".join(docs) + f"\n\nQuestion: {question}"
    return prompt.strip()

# Function to generate response from OpenAI
async def generate_response(prompt):
    response = await openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Main function to handle the process
async def main():
    user_query = "What is the main greeting in the summary?"
    file_name = "newFile123"  # The filename to look for
    relevant_documents = retrieve_relevant_documents(user_query, file_name)

    if relevant_documents:
        context = extract_docs(relevant_documents)
        prompt = build_prompt(context, user_query)
        
        # Generate response from OpenAI
        answer = await generate_response(prompt)
        print("Generated Answer:", answer)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())