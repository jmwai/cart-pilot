import Link from 'next/link';
import { shoppingAPI } from '@/lib/shopping-api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';
import ProductImage from '@/components/ProductImage';
import { Product } from '@/types';

async function getProducts(): Promise<Product[]> {
  try {
    return await shoppingAPI.getProducts();
  } catch (error) {
    console.error('Failed to fetch products:', error);
    return [];
  }
}

export default async function Home() {
  const products = await getProducts();

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
          {products.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No products available at the moment.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {products.map((product) => (
              <Link
                key={product.id}
                href={`/products/${product.id}`}
                className="group bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow"
              >
                {/* Product Image */}
                <div className="aspect-square bg-gray-100 relative overflow-hidden">
                  <ProductImage
                    src={product.product_image_url || product.picture}
                    alt={product.name}
                  />
                </div>

                {/* Product Info */}
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {product.name}
                  </h3>
                  {product.price !== null && product.price !== undefined && (
                    <p className="text-xl font-bold text-gray-900">
                      ${product.price.toFixed(2)}
                    </p>
                  )}
                  <button className="mt-4 w-full py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors">
                    Add to Cart
                  </button>
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