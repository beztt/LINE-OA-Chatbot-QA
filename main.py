import hashlib
import hmac
import os
import json
import httpx
import base64
import logging
import traceback

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from utils.qa_matcher import find_best_answer
from dotenv import load_dotenv
from collections import defaultdict, deque

# ตั้งค่า log
logging.basicConfig(level=logging.INFO)
# โหลด ENV
load_dotenv()
# user_id -> deque(maxlen=3)
user_histories = defaultdict(lambda: deque(maxlen=3))
# FastAPI app
app = FastAPI()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"


def verify_signature(signature, body):
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode()
    return hmac.compare_digest(expected_signature, signature)


@app.post("/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()

    if not verify_signature(x_line_signature, body):
        raise HTTPException(status_code=400, detail="Invalid signature")

    body_json = json.loads(body)
    events = body_json.get("events", [])

    for event in events:
        # ตรวจสอบว่าเป็นข้อความหรือไม่
        if event.get("type") != "message" or event["message"].get("type") != "text":
            continue

        reply_token = event["replyToken"]
        user_text = event["message"]["text"]
        logging.info(f"📥 Received message: {user_text}")

        # # ตรวจสอบว่าเริ่มต้นด้วย 'bot' หรือไม่
        # if user_text.lower().strip().startswith("bot"):
        #     question = user_text[3:].lstrip(": \n").strip()
        #     reply_text = find_best_answer(question)
        # else:
        #     reply_text = "หากต้องการถามบอท กรุณาพิมพ์ขึ้นต้นด้วย 'bot ...'"

        user_id = event["source"]["userId"]
        question = user_text.strip()

        # เก็บข้อความลง history
        user_histories[user_id].append(question)
        chat_history = list(user_histories[user_id])

        # ส่งเข้าไปให้ find_best_answer
        reply_text = find_best_answer(question, chat_history)

        await reply_to_line(reply_token, reply_text)

    return JSONResponse(content={"message": "OK"})


async def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    try:
        timeout = httpx.Timeout(10.0, connect=5.0)  # เพิ่ม timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(LINE_REPLY_ENDPOINT, headers=headers, json=body)
            logging.info(f"✅ Replied to LINE: {response.status_code}")
            logging.debug(f"LINE Response Body: {response.text}")
    except Exception as e:
        logging.error(f"❌ Error sending reply: {e}")
        traceback.print_exc()
        logging.error(f"Message that caused error: {message}")
