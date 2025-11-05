"""Product API handlers for fetching products from the database."""

import logging
from typing import Dict, List
from starlette.responses import JSONResponse
from starlette.requests import Request
from sqlalchemy import func, text as sql_text
import requests

from app.common.db import get_db_session
from app.common.models import CatalogItem


def convert_catalog_item_to_product(item: CatalogItem) -> Dict:
    """Convert CatalogItem model to Product API format."""
    # Convert price_usd_units to price (float in dollars)
    # Based on cart_agent usage, price_usd_units is used directly as dollars
    price = None
    if item.price_usd_units is not None:
        price = float(item.price_usd_units)

    return {
        "id": item.id,
        "name": item.name,
        "description": item.description or "",
        "picture": item.picture,
        "product_image_url": item.product_image_url or item.picture,
        "price": price,
    }


def vector_literal(values: list[float]) -> str:
    """Convert list of floats to pgvector array literal format."""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def _embed_image_from_url(image_url: str) -> List[float]:
    """
    Download image from URL and create embedding vector.
    Reuses the embedding function from product_discovery_agent tools.
    """
    try:
        # Import the embedding function from tools module
        from app.shopping_agent.sub_agents.product_discovery_agent.tools import (
            _embed_image_1408_from_bytes
        )

        # Download image from URL
        response = requests.get(image_url, timeout=10.0)
        response.raise_for_status()
        image_bytes = response.content

        # Create embedding
        embedding = _embed_image_1408_from_bytes(image_bytes)
        return embedding
    except Exception as e:
        logging.error(f"Failed to embed image from URL {image_url}: {e}")
        raise


async def get_products(request: Request) -> JSONResponse:
    """
    Get 20 random products from the catalog.
    Uses PostgreSQL RANDOM() function to efficiently select random products directly from the database.

    Returns:
        JSONResponse with list of products
    """
    try:
        with get_db_session() as db:

            selected_products = db.query(CatalogItem).order_by(
                func.random()
            ).limit(20).all()

            # Convert to API format
            products = [convert_catalog_item_to_product(
                item) for item in selected_products]

            return JSONResponse({"products": products})

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to fetch products: {str(e)}"},
            status_code=500
        )


async def get_product_by_id(request: Request) -> JSONResponse:
    """
    Get a single product by ID.

    Returns:
        JSONResponse with product data or 404 if not found
    """
    try:
        product_id = request.path_params.get("id")

        # Log for debugging
        logging.info(f"Fetching product with ID: {product_id}")
        logging.info(f"Path params: {request.path_params}")
        logging.info(f"URL path: {request.url.path}")

        if not product_id:
            return JSONResponse(
                {"error": "Product ID is required"},
                status_code=400
            )

        with get_db_session() as db:
            product = db.query(CatalogItem).filter(
                CatalogItem.id == product_id
            ).first()

            if not product:
                return JSONResponse(
                    {"error": f"Product with ID '{product_id}' not found"},
                    status_code=404
                )

            product_data = convert_catalog_item_to_product(product)
            return JSONResponse(product_data)

    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to fetch product: {str(e)}"},
            status_code=500
        )


async def get_similar_products_by_image(request: Request) -> JSONResponse:
    """
    Get products similar to a given product based on image visual similarity.

    Uses image vector search to find visually similar products by:
    1. Fetching the product by ID
    2. Downloading the product's image
    3. Creating an image embedding
    4. Finding products with similar embeddings using pgvector

    Returns:
        JSONResponse with list of similar products (excluding the original product)
    """
    try:
        product_id = request.path_params.get("id")

        if not product_id:
            return JSONResponse(
                {"error": "Product ID is required"},
                status_code=400
            )

        # Get query parameters
        limit = int(request.query_params.get("limit", "6"))

        with get_db_session() as db:
            # Fetch the product
            product = db.query(CatalogItem).filter(
                CatalogItem.id == product_id
            ).first()

            if not product:
                return JSONResponse(
                    {"error": f"Product with ID '{product_id}' not found"},
                    status_code=404
                )

            # Get product image URL
            image_url = product.product_image_url or product.picture

            if not image_url:
                # No image available - return empty results
                logging.info(f"Product {product_id} has no image URL")
                return JSONResponse({"products": []})

            # Download image and create embedding
            try:
                logging.info(
                    f"Creating embedding for product {product_id} image: {image_url}")
                embedding = _embed_image_from_url(image_url)
                qvec = vector_literal(embedding)
            except Exception as e:
                logging.error(
                    f"Failed to create embedding for product {product_id}: {e}")
                # Return empty results if embedding fails
                return JSONResponse({"products": []})

            # Query for similar products using pgvector
            # Exclude the current product and order by distance (lower is more similar)
            # Use parameterized query for safety
            query = sql_text(
                "SELECT id, name, description, picture, "
                "COALESCE(product_image_url, picture) as product_image_url, "
                "price_usd_units, "
                f"(product_image_embedding <=> '{qvec}'::vector) AS distance "
                "FROM catalog_items "
                "WHERE id != :product_id "
                "ORDER BY distance ASC LIMIT :limit"
            )
            result = db.execute(
                query, {"product_id": product_id, "limit": limit})

            products = []
            for row in result:
                products.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2] or "",
                    "picture": row[3],
                    "product_image_url": row[4],
                    "price": float(row[5]) if row[5] is not None else None,
                })

            logging.info(
                f"Found {len(products)} similar products for product {product_id}")
            return JSONResponse({"products": products})

    except Exception as e:
        logging.error(f"Failed to fetch similar products: {e}", exc_info=True)
        return JSONResponse(
            {"error": f"Failed to fetch similar products: {str(e)}"},
            status_code=500
        )
