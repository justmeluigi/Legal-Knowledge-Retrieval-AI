import os
import urllib.request
from typing import Optional


def is_ollama_running() -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Legal AI Knowledge Retrieval"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_llm(provider: str = "auto", api_key: Optional[str] = None, model_name: Optional[str] = None):
    """Factory returning LangChain chat model or None for rule-based synthesis."""
    provider = provider.lower().strip()

    if provider == "auto":
        env_provider = os.getenv("LLM_PROVIDER", "").lower().strip()
        if env_provider and env_provider != "auto":
            provider = env_provider
        elif is_ollama_running():
            provider = "qwen"
        elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            provider = "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        else:
            return None

    if provider in ["qwen", "ollama", "qwen3.5", "qwen3.5:2b"]:
        try:
            from langchain_ollama import ChatOllama
            target_model = model_name or os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return ChatOllama(
                model=target_model,
                base_url=base_url,
                temperature=0.1
            )
        except Exception as e:
            print(f"[WARN] Failed to load local Qwen ({e}). Falling back.")
            return None

    elif provider == "gemini":
        gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_key:
            return None
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = model_name or "gemini-2.5-flash"
        return ChatGoogleGenerativeAI(model=model, google_api_key=gemini_key, temperature=0.1)

    elif provider == "openai":
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return None
        from langchain_openai import ChatOpenAI
        model = model_name or "gpt-4o-mini"
        return ChatOpenAI(model=model, api_key=openai_key, temperature=0.1)

    elif provider == "groq":
        groq_key = api_key or os.getenv("GROQ_API_KEY")
        if not groq_key:
            return None
        from langchain_groq import ChatGroq
        model = model_name or "llama-3.3-70b-versatile"
        return ChatGroq(model_name=model, groq_api_key=groq_key, temperature=0.1)

    return None
