# utils/intent_detector.py
def is_non_question(text: str) -> str:
    greetings = ["สวัสดี", "ดีครับ", "hello", "hi"]
    thanks = ["ขอบคุณ", "thank", "thanks"]
    tests = ["test", "ทดลอง", "ทดสอบ"]

    lower = text.lower()

    if any(w in lower for w in greetings):
        return "greeting"
    elif any(w in lower for w in thanks):
        return "thanks"
    elif any(w in lower for w in tests):
        return "test"
    return "question"
