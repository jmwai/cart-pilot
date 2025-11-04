import { Product } from '@/types';

// Mock product data for Cart Pilot
export const mockProducts: Product[] = [
  {
    id: 'air-jordan-1',
    name: 'Air Jordan 1',
    description: 'The legendary Air Jordan 1 with classic colorway. Iconic design meets timeless style.',
    picture: '/products/air-jordan-1.jpg',
    price: 170,
    category: 'Sneakers',
  },
  {
    id: 'adidas-ultraboost',
    name: 'Adidas Ultraboost',
    description: 'Premium running shoe with responsive cushioning and energy return.',
    picture: '/products/adidas-ultraboost.jpg',
    price: 180,
    category: 'Running',
  },
  {
    id: 'new-balance-550',
    name: 'New Balance 550',
    description: 'Retro-inspired basketball sneaker with modern comfort.',
    picture: '/products/new-balance-550.jpg',
    price: 110,
    category: 'Sneakers',
  },
  {
    id: 'salomon-xt6',
    name: 'Salomon XT-6',
    description: 'Trail running shoe built for rugged terrain and technical trails.',
    picture: '/products/salomon-xt6.jpg',
    price: 190,
    category: 'Trail Running',
  },
  {
    id: 'nike-dunk-low',
    name: 'Nike Dunk Low',
    description: 'Classic skateboarding shoe with timeless appeal.',
    picture: '/products/nike-dunk-low.jpg',
    price: 110,
    category: 'Sneakers',
  },
  {
    id: 'asics-gel-kayano-14',
    name: 'ASICS GEL-Kayano 14',
    description: 'Premium stability running shoe with advanced cushioning.',
    picture: '/products/asics-gel-kayano.jpg',
    price: 150,
    category: 'Running',
  },
  {
    id: 'common-projects-achilles',
    name: 'Common Projects Achilles',
    description: 'Minimalist Italian leather sneaker with understated luxury.',
    picture: '/products/common-projects.jpg',
    price: 415,
    category: 'Luxury',
  },
  {
    id: 'on-cloud-5',
    name: 'On Cloud 5',
    description: 'Swiss-engineered running shoe with cloud cushioning technology.',
    picture: '/products/on-cloud-5.jpg',
    price: 140,
    category: 'Running',
  },
  {
    id: 'hoka-clifton-9',
    name: 'Hoka Clifton 9',
    description: 'Maximum cushioning running shoe for long distance comfort.',
    picture: '/products/hoka-clifton.jpg',
    price: 145,
    category: 'Running',
  },
];

export const getProductById = (id: string): Product | undefined => {
  return mockProducts.find(product => product.id === id);
};

export const getRelatedProducts = (excludeId: string, limit: number = 4): Product[] => {
  return mockProducts
    .filter(product => product.id !== excludeId)
    .slice(0, limit);
};
