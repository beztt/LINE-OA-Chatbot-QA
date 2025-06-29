from difflib import get_close_matches
from utils.pinecone_utils import search_answer_from_pinecone_with_metadata
from utils.prompt_builder import build_rephrase_prompt
from utils.intent_detector import is_non_question

import logging
import openai
import json
import os

# Load .env key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Q&A
with open("qa_data.json", "r", encoding="utf-8") as f:
    qa_data = json.load(f)

# Fallback: Local match (fuzzy)
def fallback_answer(user_question: str):
    questions = [q["question"] for q in qa_data]
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.4)
    if matches:
        matched_q = matches[0]
        for qa in qa_data:
            if qa["question"] == matched_q:
                logging.info("[LOCAL] Fallback match found.")
                return qa["answer"]
    return "หากคุณต้องการสอบถามเกี่ยวกับระบบ กรุณาพิมพ์คำถามเกี่ยวกับ DTMS ได้เลยครับ"

def gpt_rephrase_answer(user_question: str, matched_qa: dict) -> str:
    try:
        # prompt = build_rephrase_prompt(user_question, matched_qa)
        logging.info("[GPT] Trying to rephrase answer from closest QA match.")
        response = openai.ChatCompletion.create(
            # model="gpt-4",
            model="gpt-3.5-turbo",
            # messages=[{"role": "user", "content": prompt}],
            messages=build_rephrase_prompt(user_question, matched_qa),
            temperature=0.5
        )
        logging.info("[GPT] Answered using ChatCompletion.")
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"[GPT] ❌ GPT fallback failed: {e}")
        return "ขออภัย ขณะนี้ระบบไม่สามารถตอบคำถามได้ครับ 😅"


# Main logic: Find best answer
def find_best_answer(user_question: str) -> str:
    intent = is_non_question(user_question)
    
    if intent == "greeting":
        return "สวัสดีครับ หากคุณต้องการสอบถามเกี่ยวกับระบบ กรุณาพิมพ์คำถามเกี่ยวกับ DTMS ได้เลยครับ"
    elif intent == "thanks":
        return "ยินดีครับ หากมีคำถามเพิ่มเติม ยินดีช่วยเหลือเสมอครับ"
    elif intent == "test":
        return "ระบบพร้อมใช้งานครับ ✅ หากคุณมีคำถาม พิมพ์ได้เลยครับ"
    
    # ขั้นตอน QA Matching
    try:
        match = search_answer_from_pinecone_with_metadata(user_question, top_k=1)
        if match:
            score = match["score"]
            metadata = match["metadata"]
            logging.info(f"[PINECONE] Score={score:.3f} ID={match['id']} Question={metadata['question']}")
            if score >= 0.85:
                logging.info("[PINECONE] Match found.")
                return metadata["answer"]
            elif score >= 0.35:
                return gpt_rephrase_answer(user_question, metadata)
            else:
                return fallback_answer(user_question)

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
