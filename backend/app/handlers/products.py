"""Product API handlers for fetching products from the database."""

import logging
from typing import Dict
from starlette.responses import JSONResponse
from starlette.requests import Request
from sqlalchemy import func

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
