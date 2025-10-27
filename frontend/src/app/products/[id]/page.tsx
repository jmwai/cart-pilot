import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getProductById, getRelatedProducts } from '@/lib/mock-products';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';

interface ProductPageProps {
  params: {
    id: string;
  };
}

export default function ProductPage({ params }: ProductPageProps) {
  const product = getProductById(params.id);
  const relatedProducts = getRelatedProducts(params.id, 4);

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
              <span className="text-gray-900">{product.category || 'Products'}</span>
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
              <div className="aspect-square bg-gray-100 rounded-lg mb-4 flex items-center justify-center">
                <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                  <span className="text-gray-400 text-lg">Product Image</span>
                </div>
              </div>

              {/* Thumbnails */}
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center border-2 border-transparent hover:border-blue-600 transition-colors cursor-pointer"
                  >
                    <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                      <span className="text-gray-400 text-xs">Img {i}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Product Info */}
            <div>
              <div className="text-sm text-gray-600 mb-2">
                {product.category || "Men's Shoes"}
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                {product.name}
              </h1>
              <p className="text-3xl font-bold text-gray-900 mb-6">
                ${product.price}
              </p>

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
                  <div className="aspect-square bg-gray-100 flex items-center justify-center">
                    <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                      <span className="text-gray-400 text-xs">Image</span>
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                      {relatedProduct.name}
                    </h3>
                    <p className="text-lg font-bold text-gray-900">
                      ${relatedProduct.price}
                    </p>
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
