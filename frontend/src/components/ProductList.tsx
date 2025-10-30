'use client';

import { Product } from '@/types';

interface ProductListProps {
  products: Product[];
  onAddToCart?: (productId: string) => void;
  onViewDetails?: (productId: string) => void;
}

export default function ProductList({ products, onAddToCart, onViewDetails }: ProductListProps) {
  if (products.length === 0) {
    return null;
  }
  
  const formatPrice = (product: Product): string => {
    if (product.price && product.price > 0) {
      return product.price.toFixed(2);
    }
    if (product.price_usd_units) {
      return (product.price_usd_units / 100).toFixed(2);
    }
    return 'N/A';
  };
  
  const getImageUrl = (product: Product): string => {
    return product.image_url || product.product_image_url || product.picture || '';
  };
  
  return (
    <div className="product-list">
      <div className="product-list-items">
        {products.map((product) => (
          <div key={product.id} className="product-list-item">
            <div className="product-list-item-image-container">
              {getImageUrl(product) ? (
                <img 
                  src={getImageUrl(product)} 
                  alt={product.name}
                  className="product-list-item-image"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling;
                    if (placeholder) {
                      (placeholder as HTMLElement).style.display = 'flex';
                    }
                  }}
                />
              ) : null}
              <div 
                className="product-list-item-image-placeholder"
                style={{ display: getImageUrl(product) ? 'none' : 'flex' }}
              >
                <span>No Image</span>
              </div>
            </div>
            
            <div className="product-list-item-details">
              <h4 className="product-list-item-name">{product.name}</h4>
              {product.description && (
                <p className="product-list-item-description">{product.description}</p>
              )}
              <div className="product-list-item-footer">
                <span className="product-list-item-price">${formatPrice(product)}</span>
                {onAddToCart && (
                  <button
                    onClick={() => onAddToCart(product.id)}
                    className="product-list-item-add-btn"
                  >
                    Add to Cart
                  </button>
                )}
              </div>
            </div>
            
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(product.id)}
                className="product-list-item-view-btn"
                aria-label="View details"
              >
                →
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

