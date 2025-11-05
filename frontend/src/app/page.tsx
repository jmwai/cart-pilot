'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { shoppingAPI } from '@/lib/shopping-api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';
import ProductImage from '@/components/ProductImage';
import { Product } from '@/types';

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const fetchedProducts = await shoppingAPI.getProducts();
        setProducts(fetchedProducts);
      } catch (err) {
        console.error('Failed to fetch products:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load products';
        setError(errorMessage);
        setProducts([]); // Fallback to empty array
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, []); // Empty dependency array = run once on mount

  return (
    <div className="min-h-screen flex flex-col layout-with-chatbox">
      <Header />
      
      <main className="flex-1 main-content">
        {/* Products Grid */}
        <section className="mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full max-w-full lg:max-w-[calc(100%-var(--chatbox-width)-2rem)]">
          {/* Landing Page Message */}
          <div className="mb-8 text-center">
            <p className="text-base sm:text-lg text-gray-700 px-4">
             <b>I have thousands of shoes like this. Use the Shopping Assistant to find and buy any type of shoes</b>
            </p>
          </div>
          
          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-12">
              <div className="flex items-center justify-center gap-2 mb-4">
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
              </div>
              <p className="text-gray-600">Loading products...</p>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">Failed to load products: {error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setIsLoading(true);
                  shoppingAPI.getProducts()
                    .then(setProducts)
                    .catch((err) => {
                      setError(err instanceof Error ? err.message : 'Failed to load products');
                      setProducts([]);
                    })
                    .finally(() => setIsLoading(false));
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && products.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-600">No products available at the moment.</p>
            </div>
          )}

          {/* Products Grid */}
          {!isLoading && !error && products.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {products.map((product) => (
              <Link
                key={product.id}
                href={`/products/${product.id}`}
                className="group block"
              >
                {/* Product Image */}
                <div className="aspect-square bg-white border border-gray-200 rounded-lg relative overflow-hidden mb-3 w-full">
                  <ProductImage
                    src={product.product_image_url || product.picture}
                    alt={product.name}
                  />
                </div>

                {/* Product Info */}
                <div className="text-left">
                  <h3 className="text-sm font-medium text-gray-900 mb-1 line-clamp-2">
                    {product.name}
                  </h3>
                  {product.price !== null && product.price !== undefined && (
                    <p className="text-sm font-normal text-gray-900">
                      ${product.price.toFixed(2)}
                    </p>
                  )}
                </div>
              </Link>
              ))}
            </div>
          )}
        </section>
      </main>

      <Footer />
      <Chatbox />
    </div>
  );
}