'use client';

import { Product } from '@/types';
import Link from 'next/link';
import ProductImage from './ProductImage';

interface ProductCardProps {
  product: Product;
  onAddToCart?: (productId: string) => void;
  onViewDetails: (productId: string) => void;
}

export default function ProductCard({ product, onAddToCart, onViewDetails }: ProductCardProps) {
  // Use standardized image_url field, fallback to other fields
  const imageUrl = product.image_url || product.product_image_url || product.picture || '';
  const displayPrice = product.price && product.price > 0 
    ? product.price.toFixed(2) 
    : (product.price_usd_units ? (product.price_usd_units / 100).toFixed(2) : 'N/A');
  
  return (
    <div className="group block">
      <Link 
        href={`/products/${product.id}`}
        className="block"
        onClick={() => onViewDetails(product.id)}
      >
        <div className="aspect-square bg-white border border-gray-200 rounded-lg relative overflow-hidden mb-3">
          <ProductImage
            src={imageUrl}
            alt={product.name}
          />
        </div>
        
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-1">
            {product.name}
          </h3>
          <p className="text-sm font-normal text-gray-900">
            ${displayPrice}
          </p>
        </div>
      </Link>
      
      {onAddToCart && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onAddToCart(product.id);
          }}
          className="mt-2 w-full px-4 py-2 bg-gray-200 text-gray-800 text-sm rounded-lg hover:bg-gray-300 transition-colors"
        >
          Add to Cart
        </button>
      )}
    </div>
  );
}

