import Link from 'next/link';
import { mockProducts } from '@/lib/mock-products';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="bg-gray-50 py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Find Your Perfect Pair
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Discover premium footwear curated by AI. The future of shopping is here.
            </p>
          </div>
        </section>

        {/* Products Grid */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {mockProducts.map((product) => (
              <Link
                key={product.id}
                href={`/products/${product.id}`}
                className="group bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow"
              >
                {/* Product Image */}
                <div className="aspect-square bg-gray-100 flex items-center justify-center relative overflow-hidden">
                  <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                    <span className="text-gray-400 text-sm">No Image</span>
                  </div>
                </div>

                {/* Product Info */}
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {product.name}
                  </h3>
                  <p className="text-xl font-bold text-gray-900">
                    ${product.price}
                  </p>
                  <button className="mt-4 w-full py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors">
                    Add to Cart
                  </button>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </main>

      <Footer />
      <Chatbox />
    </div>
  );
}