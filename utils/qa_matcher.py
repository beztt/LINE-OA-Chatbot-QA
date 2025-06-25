import logging
from utils.pinecone_utils import search_answer_from_pinecone_with_metadata
from utils.prompt_builder import build_rephrase_prompt
import openai
import json
from difflib import get_close_matches
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_data = json.load(f)

def fallback_answer(user_question: str):
    questions = [q["question"] for q in qa_data]
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.5)
    if matches:
        matched_q = matches[0]
        for qa in qa_data:
            if qa["question"] == matched_q:
                logging.info("[LOCAL] Fallback match found.")
                return qa["answer"]
    return None

def find_best_answer(user_question: str) -> str:
    try:
        match = search_answer_from_pinecone_with_metadata(user_question, top_k=1)
        if match:
            score = match["score"]
            metadata = match["metadata"]
            logging.info(f"[PINECONE] Score={score:.3f} ID={match['id']}")
            if score >= 0.85:
                logging.info("[PINECONE] Match found.")
                return metadata["answer"]
            else:
                # ใช้ GPT เพื่อ rephrase answer
                prompt = build_rephrase_prompt(user_question, metadata)
                logging.info("[GPT] Trying to rephrase answer from closest QA match.")
                response = openai.ChatCompletion.create(
                    # model="gpt-4",
                    model="gpt-3.5-turbo",
                    # messages=[{"role": "user", "content": prompt}],
                    messages=build_rephrase_prompt(user_question, metadata),
                    temperature=0.5,
                )
                reply = response["choices"][0]["message"]["content"].strip()
                logging.info("[GPT] Answered using ChatCompletion.")
                return reply

        # fallback → local fuzzy match
        fallback = fallback_answer(user_question)
        if fallback:
            return fallback
        return "ขออภัย ไม่พบคำตอบที่ตรงกับคำถามของคุณครับ 😅"

    except Exception as e:
        logging.error(f"[FALLBACK] Error occurred: {e}")
        fallback = fallback_answer(user_question)
        if fallback:
            return fallback
        return "ขออภัย ระบบมีปัญหาชั่วคราว 😢"
