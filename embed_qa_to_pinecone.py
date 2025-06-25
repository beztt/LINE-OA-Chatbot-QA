from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

import os
import json
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_region = os.getenv("PINECONE_REGION")

pc = Pinecone(api_key=pinecone_api_key)

# สร้าง index ถ้ายังไม่มี
if pinecone_index_name not in pc.list_indexes().names():
    pc.create_index(
        name=pinecone_index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="gcp", region=pinecone_region)
    )
    print("✅ สร้าง index ใหม่เรียบร้อยแล้ว")

# เชื่อม index
index = pc.Index(pinecone_index_name)

with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_list = json.load(f)

def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response["data"][0]["embedding"]

for i, qa in enumerate(tqdm(qa_list)):
    question = qa["question"]
    answer = qa["answer"]
    vector = get_embedding(question)

    index.upsert([
        {
            "id": f"qa-{i}",
            "values": vector,
            "metadata": {
                "question": question,
                "answer": answer
            }
        }
    ])

print("✅ ฝัง Q&A เข้า Pinecone สำเร็จแล้ว!")
