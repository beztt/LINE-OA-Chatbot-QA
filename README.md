# 🤖 LINE OA Q&A Chatbot (with Pinecone + GPT Hybrid)

ระบบ LINE Bot สำหรับตอบคำถามเกี่ยวกับระบบ (เช่น DTMS, Dashboard, การติดตั้ง ฯลฯ)  
โดยใช้ Pinecone Vector Search + GPT Rephrasing + Fallback Matching เพื่อให้ดูเหมือนพูดคุยกับคนจริง

---

## ✅ Features

- ใช้ Pinecone vector DB match Q&A ที่ใกล้เคียง
- ใช้ GPT (gpt-3.5-turbo หรือ gpt-4-turbo) ช่วยแต่งคำตอบให้นุ่มนวล
- มีระบบ fallback local match หาก GPT หรือ Pinecone ใช้งานไม่ได้
- ตอบคำทักทาย / ขอบคุณ / ทดสอบ ได้แบบมนุษย์
- อัปเดต Q&A ได้ง่ายผ่าน `qa_data.json`

---

## 🧠 Architecture

```mermaid
flowchart TD
  A[User ส่งข้อความ LINE] --> B[/FastAPI /webhook/]
  B --> C{ขึ้นต้นด้วย "bot "?}
  C -- No --> C1[ตอบ Greeting หรือระบบพร้อม]
  C -- Yes --> D[Intent: เป็นคำถาม?]
  D -- No --> D1[ตอบ: ไม่ใช่คำถาม]
  D -- Yes --> E[Pinecone vector search]
  E -->|score >= 0.85| F1[ตอบตรงจาก Q&A]
  E -->|score >= 0.5| F2[ใช้ GPT rephrase คำตอบ]
  E -->|score < 0.5| F3[fallback local match หรือบอกไม่เข้าใจ]
  F1 --> G[ส่งข้อความกลับ LINE]
  F2 --> G
  F3 --> G
  C1 --> G
  D1 --> G
```

---

## 📦 Project Structure

```
.
├── main.py                   # LINE Webhook Endpoint
├── embed_qa_to_pinecone.py   # ฝัง Q&A เข้า Pinecone
├── qa_data.json              # คำถาม-คำตอบทั้งหมด
├── .env                      # เก็บ API keys
├── requirements.txt
├── render.yaml               # (optional) สำหรับ deploy ขึ้น Render
└── utils/
    ├── qa_matcher.py
    ├── pinecone_utils.py
    ├── prompt_builder.py
    ├── intent_detector.py
```

---

## 🛠️ Setup & Run

1. ติดตั้ง dependencies:

```bash
pip install -r requirements.txt
```

2. ตั้งค่า .env:

```env
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=qa-index
PINECONE_REGION=...
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

3. ฝัง Q&A ลง Pinecone:

```bash
python embed_qa_to_pinecone.py
```

4. รัน Server:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. ใช้ ngrok เพื่อ expose local webhook:

```bash
ngrok http 8000
```

6. ตั้งค่า Webhook URL ใน LINE Developer Console

---

## 🧪 Test Cases

| ประเภท         | ตัวอย่างคำถาม                       | พฤติกรรมที่คาดหวัง                                            |
| -------------- | ----------------------------------- | ------------------------------------------------------------- |
| 🎯 ตรง Q&A     | `ลืมรหัสผ่าน dashboard ต้องทำยังไง` | ตอบตรงจาก Pinecone                                            |
| 🔁 ใกล้เคียง   | `ลืม password เข้าระบบ`             | ใช้ GPT แต่งคำตอบจาก Q&A ที่ใกล้เคียง                         |
| 🧪 test        | `test`                              | ตอบ "ระบบพร้อมใช้งานครับ ✅"                                  |
| 🙏 ขอบคุณ      | `ขอบคุณครับ`                        | ตอบ "ยินดีครับ 😊"                                            |
| 🙌 สวัสดี      | `สวัสดีครับ`                        | ตอบ "สวัสดีครับ 😊 หากมีคำถาม พิมพ์มาได้เลยครับ"              |
| ❌ ไม่ใช่คำถาม | `พรุ่งนี้ประชุมไหม`                 | ตอบ fallback สุภาพ เช่น "ขออภัย ระบบยังไม่เข้าใจคำถามนี้ครับ" |
| ❓ ไม่มี match | `วิธีแก้ไข network fail`            | fallback match หรือแจ้งว่าไม่พบคำตอบ                          |

---

## 🧠 Notes

- อย่าลืม ignore ไฟล์สำคัญใน .gitignore:

```gitignore
.env
qa_data.json
```

- สามารถเพิ่ม Q&A ได้โดยแก้ไข `qa_data.json` แล้วรัน `embed_qa_to_pinecone.py` ใหม่

---
