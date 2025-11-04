'use client';

import { Product } from '@/types';
import ProductCard from './ProductCard';

interface ProductGridProps {
  products: Product[];
  onAddToCart?: (productId: string) => void;
  onViewDetails: (productId: string) => void;
}

export default function ProductGrid({ products, onAddToCart, onViewDetails }: ProductGridProps) {
  if (products.length === 0) {
    return null;
  }
  
  return (
    <div className="product-grid-horizontal">
      <div className="product-grid-scroll">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onAddToCart={onAddToCart}
            onViewDetails={onViewDetails}
          />
        ))}
      </div>
    </div>
  );
}

