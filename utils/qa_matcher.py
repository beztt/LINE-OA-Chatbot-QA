import logging
import openai
import json
import os

from openai import OpenAI
from difflib import get_close_matches
from utils.pinecone_utils import search_answer_from_pinecone_with_metadata
from utils.prompt_builder import build_rephrase_prompt
from utils.intent_detector import is_non_question

# Load .env key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def gpt_rephrase_answer(user_question: str, matched_qa: dict, chat_history: list[str]):
    try:
        logging.info(f"[GPT] Chat history = {chat_history}")
        prompt = build_rephrase_prompt(user_question, matched_qa, chat_history)
        logging.info("[GPT] Trying to rephrase answer from closest QA match.")
        response = openai_client.chat.completions.create(
            # model="gpt-4",
            model="gpt-3.5-turbo",
            # messages=[{"role": "user", "content": prompt}],
            messages=prompt,
            temperature=0.5
        )
        logging.info("[GPT] Answered using ChatCompletion.")
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"[GPT] ❌ GPT fallback failed: {e}")
        return "ขออภัย ขณะนี้ระบบไม่สามารถตอบคำถามได้ครับ กรุณาลองใหม่ในภายหลังครับ"


# Main logic: Find best answer
def find_best_answer(user_question: str, chat_history: list[str]) -> str:
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
            elif score >= 0.36:
                return gpt_rephrase_answer(user_question, metadata, chat_history)
            elif score >= 0.25:
                logging.warning("[PINECONE] Low confidence, not using GPT. Falling back to local.")
                return fallback_answer(user_question)
            else:
                return "หากคุณต้องการสอบถามเกี่ยวกับระบบ กรุณาพิมพ์คำถามเกี่ยวกับ DTMS ได้เลยครับ"
            # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        fallback = fallback_answer(user_question)
        if fallback:
            return fallback
        return "หากคุณต้องการสอบถามเกี่ยวกับระบบ กรุณาพิมพ์คำถามเกี่ยวกับ DTMS ได้เลยครับ"

    except Exception as e:
        logging.error(f"[FALLBACK] Error occurred: {e}")
        fallback = fallback_answer(user_question)
        if fallback:
            return fallback
        return "ขออภัย ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้งในภายหลังครับ"
