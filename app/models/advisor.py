from pydantic import BaseModel


class AdvisorMessage(BaseModel):
    reply_message: str = "ระบบประมวลผลขัดข้อง กรุณาถามคำถามใหม่อีกครั้ง"
    consider_account: str = ""
    confidence: float = 0
    reason: str = "เกิดความผิดพลาดในการประมวลผล"
    narrative: str = ""
