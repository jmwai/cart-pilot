from __future__ import annotations

import tempfile
from typing import Any, Dict, List, Optional
import requests

from fastapi import HTTPException
from sqlalchemy import text as sql_text
from google.adk.tools import ToolContext

from app.common.config import Settings, get_settings
from app.common.db import get_db_session
from app.common.models import CatalogItem


_mme = None
_vertex_inited = False
_embedding_cache = {}


def vector_literal(values: list[float]) -> str:
    # pgvector array literal format
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def _ensure_vertex():
    global _mme, _vertex_inited
    if not _vertex_inited:
        try:
            import vertexai  # type: ignore
            from vertexai.vision_models import MultiModalEmbeddingModel  # type: ignore
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Vertex AI SDK not available: {exc}")
        s = get_settings()
        vertexai.init(project=s.PROJECT_ID, location=s.REGION)
        _mme = MultiModalEmbeddingModel.from_pretrained(
            "multimodalembedding@001")
        _vertex_inited = True


def _embed_text_1408(text: str) -> List[float]:
    if text in _embedding_cache:
        return _embedding_cache[text]

    _ensure_vertex()
    # multimodalembedding@001 supports text-only; return 1408-d vector
    try:
        # type: ignore[attr-defined]
        emb = _mme.get_embeddings(text=text, dimension=1408)
        # Some SDK versions return named tuple; support both
        vec = getattr(emb, "text_embedding", None)
        if vec is None:
            vec = emb.values if hasattr(emb, "values") else None
        if vec is None:
            raise RuntimeError("Empty text embedding")

        result = list(vec)
        _embedding_cache[text] = result
        return result
    except TypeError:
        # Fallback if signature differs: try contextual_text
        # type: ignore[attr-defined]
        emb = _mme.get_embeddings(contextual_text=text, dimension=1408)
        vec = getattr(emb, "text_embedding", None)
        if vec is None:
            raise RuntimeError("Empty text embedding (contextual_text)")

        result = list(vec)
        _embedding_cache[text] = result
        return result


def _embed_image_1408_from_bytes(data: bytes) -> List[float]:
    if data in _embedding_cache:
        return _embedding_cache[data]

    _ensure_vertex()
    from vertexai.vision_models import Image  # type: ignore

    with tempfile.NamedTemporaryFile(suffix=".img") as tmp:
        tmp.write(data)
        tmp.flush()
        img = Image.load_from_file(tmp.name)
        # type: ignore[attr-defined]
        emb = _mme.get_embeddings(image=img, dimension=1408)
        vec = getattr(emb, "image_embedding", None)
        if vec is None:
            raise RuntimeError("Empty image embedding")

        result = list(vec)
        _embedding_cache[data] = result
        return result


def text_vector_search(tool_context: ToolContext, query: str) -> List[Dict[str, Any]]:
    """
    Performs semantic text search over catalog products using SQLAlchemy and pgvector.
    Args:
        tool_context: ADK tool context providing access to state
        query: The natural language search query.
    Returns:
        A list of up to 10 products matching the search query.
    """
    vec = _embed_text_1408(query)
    qvec = vector_literal(vec)

    with get_db_session() as db:
        # Use raw SQL for pgvector distance calculation
        # Embedding the vector literal directly (safe since it's from the embedding model)
        result = db.execute(
            sql_text(
                f"SELECT id, name, description, picture, "
                f"COALESCE(product_image_url, picture) as product_image_url, "
                f"price_usd_units, "
                f"(product_image_embedding <=> '{qvec}'::vector) AS distance "
                f"FROM catalog_items "
                f"ORDER BY distance ASC LIMIT 3"
            )
        )

        out = []
        for row in result:
            out.append({
                "id": row[0],
                "name": row[1],
                "description": row[2] or "",  # Include description
                "picture": row[3],
                "product_image_url": row[4],
                "price_usd_units": row[5],  # Include price
                "distance": float(row[6]),
            })

        # Store results in state for product selection
        tool_context.state["current_results"] = out

        return out


def image_vector_search(tool_context: ToolContext, image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Performs visual similarity search for products based on an image using SQLAlchemy and pgvector.
    Args:
        tool_context: ADK tool context providing access to state
        image_bytes: The raw bytes of the image to search with.
    Returns:
        A list of up to 10 visually similar products.
    """
    vec = _embed_image_1408_from_bytes(image_bytes)
    qvec = vector_literal(vec)

    with get_db_session() as db:
        # Use raw SQL for pgvector distance calculation
        # Embedding the vector literal directly (safe since it's from the embedding model)
        result = db.execute(
            sql_text(
                f"SELECT id, name, description, picture, "
                f"COALESCE(product_image_url, picture) as product_image_url, "
                f"price_usd_units, "
                f"(product_image_embedding <=> '{qvec}'::vector) AS distance "
                f"FROM catalog_items "
                f"ORDER BY distance ASC LIMIT 10"
            )
        )

        out = []
        for row in result:
            out.append({
                "id": row[0],
                "name": row[1],
                "description": row[2] or "",  # Include description
                "picture": row[3],
                "product_image_url": row[4],
                "price_usd_units": row[5],  # Include price
                "distance": float(row[6]),
            })

        # Store results in state for product selection
        tool_context.state["current_results"] = out

        return out
