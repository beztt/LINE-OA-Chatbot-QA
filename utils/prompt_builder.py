# def build_rephrase_prompt(user_question: str, matched_qa: dict) -> str:
#     return f"""ผู้ใช้ถามว่า:
# "{user_question}"

# จากฐานข้อมูล Q&A มีรายการที่ใกล้เคียงที่สุดคือ:
# Q: "{matched_qa['question']}"
# A: "{matched_qa['answer']}"

# กรุณาช่วยตอบผู้ใช้โดยใช้ข้อมูลจาก A เดิม แต่งให้เข้ากับภาษาของผู้ใช้ โดยอย่ากล่าวถึง Q&A เดิมโดยตรง และให้ตอบแบบสุภาพเข้าใจง่าย ใช้คำลงท้ายด้วย "ครับ" :
# """

def build_rephrase_prompt(user_question: str, matched_qa: dict) -> list:
    return [
        {
            "role": "system",
            "content": (
                "คุณคือแชทบอทตอบคำถามระบบภายในบริษัท "
                "ให้ตอบสั้น กระชับ สุภาพ และใช้คำลงท้ายว่า 'ครับ' เท่านั้น"
            )
        },
        {
            "role": "user",
            "content": (
                f"คำถามผู้ใช้:\n{user_question}\n\n"
                f"คำตอบจากฐานข้อมูล:\n{matched_qa['answer']}\n\n"
                "ช่วยตอบให้เข้ากับภาษาผู้ใช้"
            )
        }
    ]

