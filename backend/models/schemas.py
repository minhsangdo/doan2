"""
Pydantic schemas for request/response models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# === Chat Schemas ===
class ChatRequest(BaseModel):
    message: str = Field(..., description="Câu hỏi của thí sinh")
    session_id: Optional[str] = Field(None, description="ID phiên hội thoại")


class Source(BaseModel):
    node_type: str
    name: str
    score: Optional[float] = None


class SuggestedQuestion(BaseModel):
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    suggested_questions: List[SuggestedQuestion] = []
    session_id: str
    processing_time: float = 0.0
    bot_message_id: Optional[int] = None


# === Major (Nganh) Schemas ===
class NganhBase(BaseModel):
    ma_nganh: str
    ten: str
    nhom: str
    mo_ta: Optional[str] = None
    tohop_mon: List[str] = []


class NganhResponse(NganhBase):
    diem_chuan: Optional[dict] = None


class NganhListResponse(BaseModel):
    total: int
    items: List[NganhResponse]


# === Score (DiemChuan) Schemas ===
class DiemChuanBase(BaseModel):
    ma_nganh: str
    nam: int = 2025
    diem_thpt: Optional[float] = None
    diem_hocba: Optional[float] = None
    diem_dgnl: Optional[int] = None
    diem_vsat: Optional[int] = None


class DiemChuanResponse(DiemChuanBase):
    ten_nganh: Optional[str] = None


# === Admission Method (PhuongThuc) Schemas ===
class PhuongThucBase(BaseModel):
    ma_pt: str
    ten: str
    mo_ta: Optional[str] = None


# === Knowledge Graph Stats ===
class KGStats(BaseModel):
    total_nodes: int = 0
    total_relationships: int = 0
    node_counts: dict = {}
    relationship_counts: dict = {}


# === Admin Schemas ===
class ImportPDFRequest(BaseModel):
    file_path: str

class MajorUpdateRequest(BaseModel):
    ten: str
    nhom: str
    mo_ta: Optional[str] = None
    diem_thpt: Optional[float] = None
    diem_hocba: Optional[float] = None

class RebuildKGRequest(BaseModel):
    confirm: bool = False


class AdminResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None
