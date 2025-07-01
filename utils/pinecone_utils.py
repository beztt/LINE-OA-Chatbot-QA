import os
import logging
import openai
import numpy as np

from dotenv import load_dotenv
# from pinecone import Pinecone, ServerlessSpec
from fastapi import HTTPException, Header
from pinecone import Pinecone , ServerlessSpec
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_region = os.getenv("PINECONE_REGION")

pc = Pinecone(api_key=pinecone_api_key)

if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="gcp", region=pinecone_region)
    )
index = pc.Index(pinecone_index_name)

def get_embedding(text: str) -> list[float]:
    try:
        response = openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        embedding = np.array(response.data[0].embedding, dtype=np.float32)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Clip
        embedding = np.clip(embedding, -1.0, 1.0)

        # Check for NaN or inf
        if not np.isfinite(embedding).all():
            raise ValueError("Embedding contains NaN or Inf.")

        # Convert to list of float (not np.float32)
        return list(map(float, embedding))

    except Exception as e:
        logging.error(f"[EMBEDDING] ❌ Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail="Embedding error")

def search_answer_from_pinecone_with_metadata(question: str, top_k=1) -> dict | None:
    try:
        vector = get_embedding(question)

        query_resp = index.query(
            vector=[vector],  # หรือ queries=[vector] สำหรับบางเวอร์ชัน
            top_k=top_k,
            include_metadata=True
        )

        if query_resp and query_resp.matches:
            top_match = query_resp.matches[0]
            return {
                "id": top_match.id,
                "score": top_match.score,
                "metadata": top_match.metadata
            }

    except Exception as e:
        logging.error(f"[FALLBACK] Error occurred: {e}")
    return None