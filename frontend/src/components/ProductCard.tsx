'use client';

import { Product } from '@/types';
import { useState } from 'react';

interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string) => void;
  onViewDetails: (productId: string) => void;
}

export default function ProductCard({ product, onAddToCart, onViewDetails }: ProductCardProps) {
  const [imageError, setImageError] = useState(false);
  
  const imageUrl = product.product_image_url || product.picture || '/placeholder-product.png';
  const displayPrice = product.price?.toFixed(2) || 'N/A';
  
  return (
    <div 
      className="product-card" 
      onClick={() => onViewDetails(product.id)}
    >
      <div className="product-image-container">
        {!imageError ? (
          <img 
            src={imageUrl} 
            alt={product.name}
            onError={() => setImageError(true)}
            className="product-image"
          />
        ) : (
          <div className="product-image-placeholder">
            <span>No Image</span>
          </div>
        )}
      </div>
      
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        {product.description && (
          <p className="product-description">{product.description}</p>
        )}
        <div className="product-footer">
          <span className="product-price">${displayPrice}</span>
          <button 
            className="add-to-cart-btn"
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart(product.id);
            }}
          >
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}

