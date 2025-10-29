'use client';

import { Product } from '@/types';
import Link from 'next/link';
import ProductImage from './ProductImage';

interface ProductCardProps {
  product: Product;
  onViewDetails: (productId: string) => void;
}

export default function ProductCard({ product, onViewDetails }: ProductCardProps) {
  const displayPrice = product.price?.toFixed(2) || 'N/A';
  
  return (
    <Link 
      href={`/products/${product.id}`}
      className="group block"
      onClick={() => onViewDetails(product.id)}
    >
      <div className="aspect-square bg-white border border-gray-200 rounded-lg relative overflow-hidden mb-3">
        <ProductImage
          src={product.product_image_url || product.picture}
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
  );
}

