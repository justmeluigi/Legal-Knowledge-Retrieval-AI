import time
import re
from typing import List, Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

from core.permissions import UserRole, DEMO_USERS, get_accessible_clearances, ClearanceLevel
from core.schemas import QueryRequest, QueryResponse, GroundedPassage
from core.vector_store import LegalVectorStoreManager
from core.llm_provider import get_llm


RAG_SYSTEM_PROMPT = """You are an expert Legal Knowledge Retrieval Assistant.
Your mandate is to provide precise, faithful, evidence-based legal answers derived EXCLUSIVELY from the provided retrieved legal passages.

CRITICAL OPERATIONAL RULES:
1. STRICT GROUNDING: State only facts directly affirmed by the provided passages. Never extrapolate, assume, or hallucinate legal terms.
2. CITATION DISCIPLINE: For every substantive assertion, reference the specific document title and page number (e.g., "[Doc: Master SaaS Agreement, Page 1]").
3. INSUFFICIENT EVIDENCE HANDLING: If the provided excerpts do not explicitly answer the question or contain ambiguous gaps, state plainly: "The provided passages do not contain sufficient evidence to resolve this matter."
4. PROFESSIONAL TONE: Provide clear, formal, corporate legal synthesis.
"""

RAG_USER_PROMPT = """LEGAL QUESTION:
{query}

RETRIEVED AUTHORIZED EVIDENCE (Filtered for clearance: {clearances}):
{context}

Provide a concise, grounded legal answer supported directly by the evidence above:"""


class LegalRAGEngine:
    """Orchestrates RBAC-filtered semantic search, evidence thresholding, grounded abstention, and LLM synthesis."""

    def __init__(self, vector_manager: Optional[LegalVectorStoreManager] = None):
        self.vector_manager = vector_manager or LegalVectorStoreManager.get_instance()

    def answer_query(self, req: QueryRequest) -> QueryResponse:
        start_time = time.time()

        # Determine user role and permitted clearance tags
        user_id = req.user_id or "david_executive"
        profile = DEMO_USERS.get(user_id)
        role = req.role or (profile.role if profile else UserRole.EXECUTIVE_BOARD)
        permitted_clearances = get_accessible_clearances(role)

        similarity_threshold = req.similarity_threshold or 0.40

        # 1. Search vector database using strict RBAC clearance filter
        authorized_results = self.vector_manager.search_with_rbac(
            query=req.query,
            permitted_clearances=permitted_clearances,
            top_k=4
        )

        # 2. Check if evidence is sufficient within authorized results
        best_authorized_score = authorized_results[0][1] if authorized_results else 0.0

        # 3. Check if higher clearance exists (to explain PERMISSION_RESTRICTED vs general abstention)
        all_possible_clearances = [c.value for c in ClearanceLevel]
        higher_clearances = [c for c in all_possible_clearances if c not in permitted_clearances]
        
        has_restricted_match = False
        restricted_clearance_found = None
        if higher_clearances:
            restricted_results = self.vector_manager.search_with_rbac(
                query=req.query,
                permitted_clearances=higher_clearances,
                top_k=2
            )
            if restricted_results and restricted_results[0][1] >= similarity_threshold:
                has_restricted_match = True
                restricted_clearance_found = restricted_results[0][0].metadata.get("clearance_level", "HIGHER_SECURITY")

        # CASE A: Permission Restricted
        if best_authorized_score < similarity_threshold and has_restricted_match:
            elapsed = round(time.time() - start_time, 2)
            return QueryResponse(
                query=req.query,
                user_id=user_id,
                user_role=role,
                clearances_searched=permitted_clearances,
                status="PERMISSION_RESTRICTED",
                answer=(
                    f"ACCESS RESTRICTED: Documents containing evidence relevant to your inquiry are classified at "
                    f"a higher security tier ([{restricted_clearance_found}]). Your current role ({role.value}) "
                    f"is granted clearance only for [{', '.join(permitted_clearances)}]. "
                    f"In accordance with corporate data governance and legal RBAC policies, retrieval has been withheld."
                ),
                abstention_reason=f"Relevant knowledge requires [{restricted_clearance_found}] clearance. Current user role: {role.value}.",
                evidence_strength="ZERO_MATCHES",
                citations=[],
                documents_retrieved_count=0,
                processing_time_seconds=elapsed,
                provider_used="RBAC Access Controller"
            )

        # CASE B: Insufficient Evidence -> Abstain
        if not authorized_results or best_authorized_score < similarity_threshold:
            elapsed = round(time.time() - start_time, 2)
            return QueryResponse(
                query=req.query,
                user_id=user_id,
                user_role=role,
                clearances_searched=permitted_clearances,
                status="ABSTAINED",
                answer=(
                    "ABSTAINED: The indexed legal repository does not contain sufficient factual evidence or "
                    "contractual provisions to answer this inquiry. The system is programmed to abstain from "
                    "speculation or external hallucinations."
                ),
                abstention_reason=(
                    f"Best relevance score ({round(best_authorized_score, 3)}) is below the required evidence threshold ({similarity_threshold})."
                    if authorized_results else "Zero matching documents found in permitted knowledge base."
                ),
                evidence_strength="INSUFFICIENT" if authorized_results else "ZERO_MATCHES",
                citations=[],
                documents_retrieved_count=len(authorized_results),
                processing_time_seconds=elapsed,
                provider_used="Evidence Verification Filter"
            )

        # CASE C: Sufficient Evidence -> Synthesize Answer with Grounded Citations
        citations: List[GroundedPassage] = []
        context_snippets = []

        for doc, score in authorized_results:
            if score >= similarity_threshold:
                meta = doc.metadata
                citations.append(GroundedPassage(
                    doc_id=meta.get("doc_id", "unknown"),
                    document_title=meta.get("document_title", "Legal Document"),
                    page=int(meta.get("page", 1)),
                    clause_section=meta.get("section", "Section"),
                    clearance_level=meta.get("clearance_level", "INTERNAL"),
                    verbatim_passage=doc.page_content,
                    similarity_score=round(score, 3)
                ))
                context_snippets.append(
                    f"[Document: {meta.get('document_title')} | Page: {meta.get('page')} | Clearance: {meta.get('clearance_level')}]\n"
                    f"{doc.page_content}"
                )

        # Generate synthesis via LLM or deterministic fallback
        llm = get_llm(provider=req.provider or "auto")
        provider_label = "Local Qwen 3.5 2B"
        generated_answer = ""

        if llm is not None:
            try:
                full_context_text = "\n\n---\n\n".join(context_snippets)
                messages = [
                    SystemMessage(content=RAG_SYSTEM_PROMPT),
                    HumanMessage(content=RAG_USER_PROMPT.format(
                        query=req.query,
                        clearances=", ".join(permitted_clearances),
                        context=full_context_text
                    ))
                ]
                llm_response = llm.invoke(messages)
                generated_answer = llm_response.content.strip()
                provider_label = f"LLM ({getattr(llm, 'model', getattr(llm, 'model_name', 'Qwen 3.5 2B'))})"
            except Exception as e:
                print(f"[WARN] LLM synthesis failed ({e}). Using extractive legal synthesizer.")
                generated_answer = ""

        if not generated_answer:
            # Deterministic extractive legal synthesizer
            top_cite = citations[0]
            generated_answer = (
                f"Based on {top_cite.document_title} (Page {top_cite.page}, {top_cite.clause_section}):\n\n"
                f"{top_cite.verbatim_passage.splitlines()[-1] if len(top_cite.verbatim_passage.splitlines()) > 1 else top_cite.verbatim_passage}\n\n"
                f"[Source Verification: Verified under security clearance {top_cite.clearance_level}. Similarity score: {top_cite.similarity_score}]"
            )
            provider_label = "Extractive Legal Synthesizer"

        elapsed = round(time.time() - start_time, 2)
        evidence_strength = "STRONG" if best_authorized_score >= 0.60 else "MODERATE"

        return QueryResponse(
            query=req.query,
            user_id=user_id,
            user_role=role,
            clearances_searched=permitted_clearances,
            status="ANSWERED",
            answer=generated_answer,
            abstention_reason=None,
            evidence_strength=evidence_strength,
            citations=citations,
            documents_retrieved_count=len(citations),
            processing_time_seconds=elapsed,
            provider_used=provider_label
        )
