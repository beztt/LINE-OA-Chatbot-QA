def build_rephrase_prompt(user_question: str, matched_qa: dict) -> list:
    return [
        {
            "role": "system",
            "content": (
                "คุณคือ admin ที่ช่วยตอบคำถามจากฐานข้อมูลระบบบริษัท "
                "ตอบด้วยภาษาสุภาพ อ่านง่าย ใช้คำลงท้ายว่า 'ครับ' เท่านั้น "
                "ห้ามพูดถึงคำถามต้นฉบับโดยตรง และห้ามใช้คำว่า 'ค่ะ', 'จ้า', 'ครับ/ค่ะ'"
            )
        },
        {
            "role": "user",
            "content": (
                f"คำถามจากผู้ใช้: {user_question}\n\n"
                f"คำถามเดิมจากฐานข้อมูล: {matched_qa['question']}\n\n"
                f"คำตอบเดิมจากฐานข้อมูล: {matched_qa['answer']}\n\n"
                f"โปรดตอบใหม่ให้เหมาะกับคำถามนี้ โดยใช้ข้อมูลจากคำตอบเดิม"
            )
        }
    ]

