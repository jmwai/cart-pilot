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
          
          {products.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No products available at the moment.</p>
            </div>
          ) : (
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