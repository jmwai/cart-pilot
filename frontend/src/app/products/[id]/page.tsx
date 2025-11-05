import { notFound } from 'next/navigation';
import Link from 'next/link';
import { shoppingAPI } from '@/lib/shopping-api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Chatbox from '@/components/Chatbox';
import ProductImage from '@/components/ProductImage';
import { Product } from '@/types';

interface ProductPageProps {
  params: Promise<{
    id: string;
  }>;
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
    // First, try to get image-based similar products
    const similarProducts = await shoppingAPI.getSimilarProducts(excludeId, limit);
    
    if (similarProducts.length > 0) {
      return similarProducts.slice(0, limit);
    }
    
    // Fallback: If no similar products found, use random products
    const allProducts = await shoppingAPI.getProducts();
    // Filter out the current product and get random selection
    const filtered = allProducts.filter(p => p.id !== excludeId);
    // Shuffle and take limit
    const shuffled = filtered.sort(() => Math.random() - 0.5);
    return shuffled.slice(0, limit);
  } catch (error) {
    console.error('Failed to fetch related products', error);
    // Fallback to random products on error
    try {
      const allProducts = await shoppingAPI.getProducts();
      const filtered = allProducts.filter(p => p.id !== excludeId);
      const shuffled = filtered.sort(() => Math.random() - 0.5);
      return shuffled.slice(0, limit);
    } catch (fallbackError) {
      console.error('Failed to fetch fallback products', fallbackError);
      return [];
    }
  }
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { id } = await params;
  const product = await getProduct(id);
  const relatedProducts = await getRelatedProducts(id, 4);

  if (!product) {
    notFound();
  }

  return (
    <div className="min-h-screen flex flex-col layout-with-chatbox">
      <Header />
      
      <main className="flex-1 main-content">
        {/* Product Detail Section */}
        <section className="mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-16 w-full max-w-full lg:max-w-[calc(100%-var(--chatbox-width)-2rem)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16">
            {/* Product Image */}
            <div>
              <div className="aspect-square bg-white border border-gray-200 rounded-lg relative overflow-hidden">
                <ProductImage
                  src={product.product_image_url || product.picture}
                  alt={product.name}
                />
              </div>
            </div>

            {/* Product Info */}
            <div className="flex flex-col justify-center">
              <h1 className="text-2xl font-medium text-gray-900 mb-4">
                {product.name}
              </h1>
              {product.price !== null && product.price !== undefined && (
                <p className="text-lg font-normal text-gray-900 mb-8">
                  ${product.price.toFixed(2)}
                </p>
              )}

              {/* Description */}
              {product.description && (
                <div className="mb-8">
                  <p className="text-sm font-normal text-gray-600 leading-relaxed">
                    {product.description}
                  </p>
                </div>
              )}

              {/* Add to Cart Button */}
              <button className="w-full py-3 bg-black text-white hover:bg-gray-900 transition-colors font-medium text-sm mb-8">
                Add to Cart
              </button>
            </div>
          </div>
        </section>

        {/* You Might Also Like */}
        {relatedProducts.length > 0 && (
          <section className="border-t border-gray-200 py-8 sm:py-16">
            <div className="mx-auto px-4 sm:px-6 lg:px-8 w-full max-w-full lg:max-w-[calc(100%-var(--chatbox-width)-2rem)]">
              <h2 className="text-sm font-medium text-gray-900 mb-6 sm:mb-8">You Might Also Like</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4">
                {relatedProducts.map((relatedProduct) => (
                  <Link
                    key={relatedProduct.id}
                    href={`/products/${relatedProduct.id}`}
                    className="group"
                  >
                    <div className="aspect-square bg-white border border-gray-200 rounded-lg relative overflow-hidden mb-2">
                      <ProductImage
                        src={relatedProduct.product_image_url || relatedProduct.picture}
                        alt={relatedProduct.name}
                      />
                    </div>
                    <div>
                      <h3 className="text-xs font-medium text-gray-900 mb-1">
                        {relatedProduct.name}
                      </h3>
                      {relatedProduct.price !== null && relatedProduct.price !== undefined && (
                        <p className="text-xs font-normal text-gray-900">
                          ${relatedProduct.price.toFixed(2)}
                        </p>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>

      <Footer />
      <Chatbox />
    </div>
  );
}
