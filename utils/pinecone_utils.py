import os
import logging
import openai
import numpy as np

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_region = os.getenv("PINECONE_REGION")

openai_client = OpenAI(api_key=openai_api_key)
pc = Pinecone(api_key=pinecone_api_key)

if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="gcp", region=pinecone_region)
    )
index = pc.Index(pinecone_index_name)

def get_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def search_answer_from_pinecone_with_metadata(question: str, top_k: int = 1):
    vector = get_embedding(question)
    query_resp = index.query(queries=[vector], top_k=top_k, include_metadata=True)
    matches = query_resp.matches
    if not matches:
        return None
    m = matches[0]
    return {"id": m.id, "score": m.score, "metadata": m.metadata}
