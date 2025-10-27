// Product Types
export interface Product {
  id: string;
  name: string;
  description?: string;
  picture?: string;
  price: number;
  category?: string;
}

export interface CartItem {
  cart_item_id: string;
  product_id: string;
  name: string;
  picture?: string;
  quantity: number;
  price: number;
  subtotal: number;
}

export interface Order {
  order_id: string;
  status: string;
  items: OrderItem[];
  total_amount: number;
  shipping_address?: string;
  created_at?: string;
}

export interface OrderItem {
  product_id: string;
  name: string;
  quantity: number;
  price: number;
}

// Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// UI State Types
export interface ProductFilters {
  category?: string;
  priceRange?: [number, number];
  searchQuery?: string;
}
