import os
from typing import List, Tuple, Dict, Any, Optional
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from core.document_indexer import LegalDocumentIndexer, DOCUMENT_CLEARANCE_MAP
from core.schemas import IndexedDocumentSummary


DEFAULT_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
DEFAULT_CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "legal_corpus")


class LegalVectorStoreManager:
    """Manages persistent ChromaDB vector store with semantic embeddings and RBAC metadata filtering."""

    _instance: Optional['LegalVectorStoreManager'] = None
    _vectorstore: Optional[Chroma] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None

    def __init__(self, persist_dir: str = DEFAULT_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection_name = "legal_knowledge_base"
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )

    @classmethod
    def get_instance(cls, persist_dir: str = DEFAULT_PERSIST_DIR) -> 'LegalVectorStoreManager':
        if cls._instance is None:
            cls._instance = cls(persist_dir=persist_dir)
        return cls._instance

    def index_corpus(self, corpus_dir: str = DEFAULT_CORPUS_DIR, force_reindex: bool = False) -> int:
        """Indexes all legal documents in the corpus directory into ChromaDB."""
        current_count = self.vectorstore._collection.count()
        if current_count > 0 and not force_reindex:
            print(f"[INFO] Vector store already indexed with {current_count} chunks. Skipping re-indexing.")
            return current_count

        if force_reindex and current_count > 0:
            print("[INFO] Clearing existing collection for re-indexing...")
            self.client.delete_collection(self.collection_name)
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )

        print(f"[INFO] Indexing documents from {corpus_dir}...")
        docs = LegalDocumentIndexer.index_directory(corpus_dir)
        if docs:
            self.vectorstore.add_documents(docs)
            print(f"[SUCCESS] Indexed {len(docs)} legal chunks into ChromaDB.")
        return len(docs)

    def search_with_rbac(
        self,
        query: str,
        permitted_clearances: List[str],
        top_k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        Executes vector similarity search with strict RBAC clearance filtering.
        Chunks outside permitted_clearances are fundamentally excluded at the vector database level.
        Returns normalized similarity scores between 0.0 and 1.0.
        """
        if not permitted_clearances:
            return []

        # ChromaDB metadata filter
        if len(permitted_clearances) == 1:
            where_filter = {"clearance_level": permitted_clearances[0]}
        else:
            where_filter = {"clearance_level": {"$in": permitted_clearances}}

        # Similarity search with distance score
        raw_results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=where_filter
        )

        results_with_normalized_scores = []
        for doc, distance in raw_results:
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            # Normalized similarity: 1.0 - (distance / 2.0)
            norm_sim = max(0.0, min(1.0, 1.0 - (float(distance) / 2.0)))
            results_with_normalized_scores.append((doc, norm_sim))

        # Sort descending by normalized similarity
        results_with_normalized_scores.sort(key=lambda x: x[1], reverse=True)
        return results_with_normalized_scores

    def get_indexed_documents_summary(self, corpus_dir: str = DEFAULT_CORPUS_DIR) -> List[IndexedDocumentSummary]:
        summaries = []
        if not os.path.exists(corpus_dir):
            return summaries

        for fname in sorted(os.listdir(corpus_dir)):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(corpus_dir, fname)
                chunks = LegalDocumentIndexer.index_pdf_file(fpath)
                clearance, category = DOCUMENT_CLEARANCE_MAP.get(fname, ("INTERNAL", "General"))
                title = chunks[0].metadata.get("document_title", fname) if chunks else fname
                total_pages = max([c.metadata.get("page", 1) for c in chunks], default=1)

                summaries.append(IndexedDocumentSummary(
                    doc_id=fname.replace(".pdf", ""),
                    title=title,
                    category=category,
                    clearance_level=clearance,
                    total_pages=total_pages,
                    total_chunks=len(chunks),
                    summary=f"Contains {len(chunks)} indexed legal sections with security classification [{clearance}]."
                ))
        return summaries
