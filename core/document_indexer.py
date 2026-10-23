import os
import re
import pymupdf as fitz
from typing import List, Dict, Any
from langchain_core.documents import Document
from core.schemas import IndexedDocumentSummary


DOCUMENT_CLEARANCE_MAP = {
    "01_public_code_of_conduct.pdf": ("PUBLIC", "Corporate Governance & Ethics"),
    "02_employee_handbook_and_ip.pdf": ("INTERNAL", "Human Resources & IP"),
    "03_master_saas_agreement.pdf": ("INTERNAL", "Commercial Contracts"),
    "04_data_privacy_and_security_dpa.pdf": ("LEGAL_COUNSEL", "Data Privacy & Compliance"),
    "05_confidential_merger_due_diligence.pdf": ("EXECUTIVE_BOARD", "Strategic M&A & Corporate Finance")
}


class LegalDocumentIndexer:
    """Extracts, chunks, and prepares legal documents with RBAC security tags and page anchors."""

    @classmethod
    def index_pdf_file(cls, file_path: str) -> List[Document]:
        filename = os.path.basename(file_path)
        clearance, category = DOCUMENT_CLEARANCE_MAP.get(
            filename,
            ("INTERNAL", "General Legal")
        )

        doc = fitz.open(file_path)
        chunks: List[Document] = []
        doc_title = filename.replace(".pdf", "").replace("_", " ").title()

        try:
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                page_text = page.get_text("text").strip()
                if not page_text:
                    continue

                # Parse document title from page 1 if available
                if page_idx == 0:
                    lines = [l.strip() for l in page_text.split("\n") if l.strip()]
                    for l in lines:
                        if any(w in l.upper() for w in ["CODE", "HANDBOOK", "AGREEMENT", "ADDENDUM", "MEMORANDUM", "PROJECT"]):
                            doc_title = l
                            break

                # Split page into section blocks
                sections = cls._extract_sections_from_page(page_text)

                for sec_header, sec_body in sections:
                    full_chunk_text = f"[{doc_title}] (Page {page_num}) - {sec_header}\n{sec_body}"
                    chunks.append(Document(
                        page_content=full_chunk_text,
                        metadata={
                            "doc_id": filename.replace(".pdf", ""),
                            "filename": filename,
                            "document_title": doc_title,
                            "category": category,
                            "clearance_level": clearance,
                            "page": page_num,
                            "section": sec_header,
                            "chunk_len": len(full_chunk_text)
                        }
                    ))
        finally:
            doc.close()

        return chunks

    @classmethod
    def _extract_sections_from_page(cls, text: str) -> List[tuple]:
        """Identifies Section headers within a legal page."""
        lines = text.split("\n")
        sections = []
        current_header = "General Provisions"
        current_lines = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("SECURITY CLASSIFICATION"):
                continue

            # Identify Section markers like SECTION 1: ...
            if re.match(r"^SECTION\s+\d+:", trimmed, re.IGNORECASE):
                if current_lines:
                    sections.append((current_header, "\n".join(current_lines).strip()))
                    current_lines = []
                current_header = trimmed
            else:
                current_lines.append(trimmed)

        if current_lines:
            sections.append((current_header, "\n".join(current_lines).strip()))

        return sections or [("Full Page Text", text)]

    @classmethod
    def index_directory(cls, dir_path: str) -> List[Document]:
        all_docs = []
        for fname in sorted(os.listdir(dir_path)):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(dir_path, fname)
                chunks = cls.index_pdf_file(fpath)
                all_docs.extend(chunks)
        return all_docs
