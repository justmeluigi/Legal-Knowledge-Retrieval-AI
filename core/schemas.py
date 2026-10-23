from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from core.permissions import UserRole


class GroundedPassage(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier.")
    document_title: str = Field(..., description="Formal legal title of the source agreement or policy.")
    page: int = Field(..., description="1-indexed page number in the source PDF.")
    clause_section: str = Field(default="Unspecified Section", description="Section or clause header name.")
    clearance_level: str = Field(..., description="Security clearance required to view this chunk.")
    verbatim_passage: str = Field(..., description="Exact textual excerpt supporting the answer.")
    similarity_score: float = Field(..., description="Semantic retrieval similarity score (higher is more relevant).")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language legal question.")
    user_id: Optional[str] = Field(default="david_executive", description="Selected demo user ID.")
    role: Optional[UserRole] = Field(default=None, description="Explicit role override.")
    provider: Optional[str] = Field(default="auto", description="LLM provider: 'qwen', 'gemini', 'openai', 'groq', 'mock'.")
    similarity_threshold: Optional[float] = Field(default=0.45, description="Minimum relevance threshold to prevent hallucination.")


class QueryResponse(BaseModel):
    query: str = Field(..., description="Original user query.")
    user_id: str = Field(..., description="User ID that executed the retrieval.")
    user_role: UserRole = Field(..., description="Security role of the user.")
    clearances_searched: List[str] = Field(default_factory=list, description="Clearance levels filtered during vector search.")
    status: Literal["ANSWERED", "ABSTAINED", "PERMISSION_RESTRICTED"] = Field(
        ...,
        description="ANSWERED: evidence was verified; ABSTAINED: evidence was insufficient; PERMISSION_RESTRICTED: higher clearance required."
    )
    answer: str = Field(..., description="Grounded synthesized legal answer or abstention notice.")
    abstention_reason: Optional[str] = Field(default=None, description="Explicit rationale when system abstains.")
    evidence_strength: Literal["STRONG", "MODERATE", "INSUFFICIENT", "ZERO_MATCHES"] = Field(
        ...,
        description="Confidence level of retrieved textual evidence."
    )
    citations: List[GroundedPassage] = Field(default_factory=list, description="Verbatim cited passages with page anchors.")
    documents_retrieved_count: int = Field(default=0, description="Number of permitted chunks retrieved from vector store.")
    processing_time_seconds: float = Field(default=0.0, description="Total execution time in seconds.")
    provider_used: str = Field(default="auto", description="Model and engine that generated the answer.")


class IndexedDocumentSummary(BaseModel):
    doc_id: str
    title: str
    category: str
    clearance_level: str
    total_pages: int
    total_chunks: int
    summary: str
