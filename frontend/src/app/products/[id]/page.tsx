import { notFound } from 'next/navigation';
import Link from 'next/link';
import { shoppingAPI } from '@/lib/shopping-api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';
import ProductImage from '@/components/ProductImage';
import { Product } from '@/types';

interface ProductPageProps {
  params: {
    id: string;
  };
}

async function getProduct(id: string): Promise<Product | null> {
  try {
    return await shoppingAPI.getProductById(id);
  } catch (error) {
    console.error(`Failed to fetch product ${id}:`, error);
    return null;
  }
}

async function getRelatedProducts(excludeId: string, limit: number = 4): Promise<Product[]> {
  try {
    const allProducts = await shoppingAPI.getProducts();
    // Filter out the current product and get random selection
    const filtered = allProducts.filter(p => p.id !== excludeId);
    // Shuffle and take limit
    const shuffled = filtered.sort(() => Math.random() - 0.5);
    return shuffled.slice(0, limit);
  } catch (error) {
    console.error('Failed to fetch related products:', error);
    return [];
  }
}

export default async function ProductPage({ params }: ProductPageProps) {
  const product = await getProduct(params.id);
  const relatedProducts = await getRelatedProducts(params.id, 4);

  if (!product) {
    notFound();
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
            {/* Breadcrumb */}
        <div className="bg-gray-50 py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="text-sm">
              <Link href="/" className="text-gray-600 hover:text-blue-600">
                Home
              </Link>
              <span className="mx-2 text-gray-400">/</span>
              <span className="text-gray-900">Products</span>
              <span className="mx-2 text-gray-400">/</span>
              <span className="text-gray-900">{product.name}</span>
            </nav>
          </div>
        </div>

        {/* Product Detail Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Product Images */}
            <div>
              {/* Main Image */}
              <div className="aspect-square bg-gray-100 rounded-lg mb-4 relative overflow-hidden">
                <ProductImage
                  src={product.product_image_url || product.picture}
                  alt={product.name}
                />
              </div>

              {/* Thumbnails - Show same image as thumbnail for now */}
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="aspect-square bg-gray-100 rounded-lg relative overflow-hidden border-2 border-transparent hover:border-blue-600 transition-colors cursor-pointer"
                  >
                    <ProductImage
                      src={product.product_image_url || product.picture}
                      alt={`${product.name} thumbnail ${i}`}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Product Info */}
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                {product.name}
              </h1>
              {product.price !== null && product.price !== undefined && (
                <p className="text-3xl font-bold text-gray-900 mb-6">
                  ${product.price.toFixed(2)}
                </p>
              )}

              {/* Description */}
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Description</h2>
                <p className="text-gray-600 leading-relaxed">
                  {product.description || 'Premium quality product with excellent craftsmanship and design.'}
                </p>
              </div>

              {/* Size Selection */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Select Size (US)</h3>
                <div className="flex flex-wrap gap-2">
                  {[7, 8, 9, 10, 11, 12].map((size) => (
                    <button
                      key={size}
                      className={`px-4 py-2 border-2 rounded-lg font-medium transition-colors ${
                        size === 8
                          ? 'border-blue-600 bg-blue-50 text-blue-900'
                          : 'border-gray-300 hover:border-gray-400 text-gray-700'
                      }`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              {/* Add to Cart Button */}
              <button className="w-full py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold text-lg mb-4">
                Add to Cart
              </button>

              {/* Additional Info */}
              <div className="text-sm text-gray-600 space-y-2">
                <p>✓ Free shipping on orders over $100</p>
                <p>✓ 30-day return policy</p>
                <p>✓ Secure checkout</p>
              </div>
            </div>
          </div>
        </section>

        {/* You Might Also Like */}
        <section className="bg-gray-50 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-8">You Might Also Like</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {relatedProducts.map((relatedProduct) => (
                <Link
                  key={relatedProduct.id}
                  href={`/products/${relatedProduct.id}`}
                  className="group bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow"
                >
                  <div className="aspect-square bg-gray-100 relative overflow-hidden">
                    <ProductImage
                      src={relatedProduct.product_image_url || relatedProduct.picture}
                      alt={relatedProduct.name}
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                      {relatedProduct.name}
                    </h3>
                    {relatedProduct.price !== null && relatedProduct.price !== undefined && (
                      <p className="text-lg font-bold text-gray-900">
                        ${relatedProduct.price.toFixed(2)}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
      <Chatbox />
    </div>
  );
}
