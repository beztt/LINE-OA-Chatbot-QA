from dotenv import load_dotenv
from pinecone import Pinecone

import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(pinecone_index_name)

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response["data"][0]["embedding"]

def search_answer_from_pinecone_with_metadata(question, top_k=1):
    vector = get_embedding(question)
    response = index.query(vector=vector, top_k=top_k, include_metadata=True)

    if response and response["matches"]:
        return response["matches"][0]
    return None

