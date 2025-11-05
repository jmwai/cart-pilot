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


def image_vector_search(tool_context: ToolContext) -> List[Dict[str, Any]]:
    """
    Performs visual similarity search for products based on an image using SQLAlchemy and pgvector.
    The image bytes should be in the user's Content message (passed in the request).

    Args:
        tool_context: ADK tool context providing access to state
    Returns:
        A list of up to 10 visually similar products.
    """
    image_bytes = None

    # Primary: Get image from state (stored by executor from request)
    image_bytes = tool_context.state.get("current_image_bytes")
    if image_bytes:
        print(
            f"DEBUG image_vector_search: Found image in state (primary), size: {len(image_bytes) if isinstance(image_bytes, bytes) else 'unknown'} bytes", flush=True)

    # Fallback: Try to extract image from the Content message (user's request)
    # Check if we can access the invocation context's content
    if not image_bytes:
        print(f"DEBUG image_vector_search: Image not in state, trying Content message...", flush=True)
        try:
            ic = tool_context._invocation_context
            print(
                f"DEBUG image_vector_search: invocation_context type: {type(ic)}", flush=True)
            print(
                f"DEBUG image_vector_search: invocation_context dir: {[a for a in dir(ic) if not a.startswith('_')][:20]}", flush=True)

            # Try multiple ways to access content
            content = None
            if hasattr(ic, 'content'):
                content = ic.content
                print(
                    f"DEBUG image_vector_search: Found content via ic.content: {type(content)}", flush=True)
            elif hasattr(ic, 'message'):
                content = ic.message
                print(
                    f"DEBUG image_vector_search: Found content via ic.message: {type(content)}", flush=True)
            elif hasattr(ic, 'user_message'):
                content = ic.user_message
                print(
                    f"DEBUG image_vector_search: Found content via ic.user_message: {type(content)}", flush=True)
            elif hasattr(ic, 'conversation'):
                conv = ic.conversation
                print(
                    f"DEBUG image_vector_search: Found conversation: {type(conv)}", flush=True)
                if hasattr(conv, 'contents') and conv.contents:
                    # Get the last user message
                    for msg in reversed(conv.contents):
                        if hasattr(msg, 'role') and msg.role == 'user':
                            content = msg
                            print(
                                f"DEBUG image_vector_search: Found user message in conversation", flush=True)
                            break

            if content:
                print(
                    f"DEBUG image_vector_search: Content type: {type(content)}", flush=True)
                if hasattr(content, 'parts'):
                    parts = content.parts
                    print(
                        f"DEBUG image_vector_search: Content has {len(parts) if parts else 0} parts", flush=True)
                    for i, part in enumerate(parts):
                        print(
                            f"DEBUG image_vector_search: Part {i}: type={type(part)}, dir={[a for a in dir(part) if not a.startswith('_')][:10]}", flush=True)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_bytes = part.inline_data.data
                            print(
                                f"DEBUG image_vector_search: Found image in Content part {i}, size: {len(image_bytes)} bytes", flush=True)
                            break
                        elif hasattr(part, 'file_data') and part.file_data:
                            # Alternative structure
                            image_bytes = part.file_data.data
                            print(
                                f"DEBUG image_vector_search: Found image in Content part {i} (file_data), size: {len(image_bytes)} bytes", flush=True)
                            break
        except Exception as e:
            print(
                f"DEBUG image_vector_search: Could not access Content from invocation_context: {e}", flush=True)
            import traceback
            traceback.print_exc()

    # Debug: Log state information
    state_keys = list(tool_context.state.keys()) if hasattr(
        tool_context.state, 'keys') else []
    session_id = None
    try:
        session_id = tool_context._invocation_context.session.id if hasattr(
            tool_context._invocation_context, 'session') else 'unknown'
    except Exception:
        session_id = 'unknown'

    print(
        f"DEBUG image_vector_search: Session {session_id}, State keys: {state_keys}")
    print(
        f"DEBUG image_vector_search: current_image_bytes type: {type(image_bytes)}, present: {image_bytes is not None}")

    if not image_bytes:
        available_keys = ', '.join(state_keys) if state_keys else 'none'
        raise ValueError(
            f"No image found in Content message or state for session {session_id}. "
            f"Available state keys: {available_keys}. "
            f"Please ensure an image was uploaded in the request.")

    # Ensure image_bytes is bytes type
    if isinstance(image_bytes, str):
        # If it's a base64 string, decode it
        import base64
        image_bytes = base64.b64decode(image_bytes)
    elif not isinstance(image_bytes, bytes):
        raise ValueError(
            f"Invalid image_bytes type: {type(image_bytes)}. Expected bytes or base64 string.")

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
