"""LLM Model Management Service.

Manages LLM model configurations stored in Supabase.
Allows runtime updates without redeployment.
"""

from typing import Optional
from dataclasses import dataclass

from src.clients.supabase_client import get_supabase_admin_client


@dataclass
class LLMModelConfig:
    """LLM Model configuration from database."""

    id: str
    provider: str  # groq, gemini, huggingface, openai
    model_id: str  # e.g., llama-3.3-70b-versatile
    display_name: str
    is_active: bool
    priority: int  # Higher = tried first


def get_active_models() -> list[LLMModelConfig]:
    """Get all active LLM models from database, sorted by priority.

    Returns:
        List of active LLMModelConfig sorted by priority (descending).
    """
    try:
        supabase = get_supabase_admin_client()

        result = (
            supabase.table("llm_models")
            .select("*")
            .eq("is_active", True)
            .order("priority", desc=True)
            .execute()
        )

        models = []
        for row in result.data or []:
            models.append(
                LLMModelConfig(
                    id=row.get("id", ""),
                    provider=row.get("provider", ""),
                    model_id=row.get("model_id", ""),
                    display_name=row.get("display_name", row.get("model_id", "")),
                    is_active=row.get("is_active", True),
                    priority=row.get("priority", 0),
                )
            )

        return models

    except Exception as e:
        print(f"[MODEL] Failed to fetch models from DB, using defaults: {e}")
        return get_default_models()


def get_models_by_provider(provider: str) -> list[LLMModelConfig]:
    """Get active models for a specific provider.

    Args:
        provider: Provider name (groq, gemini, huggingface, openai)

    Returns:
        List of active models for the provider.
    """
    all_models = get_active_models()
    return [m for m in all_models if m.provider == provider]


def get_default_models() -> list[LLMModelConfig]:
    """Get default fallback models when database is unavailable."""
    return [
        LLMModelConfig(
            id="default-groq",
            provider="groq",
            model_id="llama-3.3-70b-versatile",
            display_name="Llama 3.3 70B (Groq)",
            is_active=True,
            priority=100,
        ),
        LLMModelConfig(
            id="default-gemini",
            provider="gemini",
            model_id="gemini-1.5-flash-latest",
            display_name="Gemini 1.5 Flash",
            is_active=True,
            priority=90,
        ),
        LLMModelConfig(
            id="default-hf",
            provider="huggingface",
            model_id="mistralai/Mistral-7B-Instruct-v0.3",
            display_name="Mistral 7B",
            is_active=True,
            priority=80,
        ),
        LLMModelConfig(
            id="default-openai",
            provider="openai",
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            is_active=True,
            priority=70,
        ),
    ]


# SQL for creating the table (for reference)
CREATE_TABLE_SQL = """
CREATE TABLE llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    display_name TEXT,
    is_active BOOLEAN DEFAULT true,
    priority INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_models_provider ON llm_models(provider);
CREATE INDEX idx_llm_models_priority ON llm_models(priority DESC);

-- Seed initial models
INSERT INTO llm_models (provider, model_id, display_name, is_active, priority) VALUES
('groq', 'llama-3.3-70b-versatile', 'Llama 3.3 70B (Groq)', true, 100),
('groq', 'llama-3.1-8b-instant', 'Llama 3.1 8B Instant (Groq)', true, 95),
('gemini', 'gemini-1.5-flash-latest', 'Gemini 1.5 Flash', true, 90),
('gemini', 'gemini-2.0-flash', 'Gemini 2.0 Flash', true, 85),
('huggingface', 'mistralai/Mistral-7B-Instruct-v0.3', 'Mistral 7B', true, 80),
('openai', 'gpt-4o-mini', 'GPT-4o Mini', true, 70);
"""
