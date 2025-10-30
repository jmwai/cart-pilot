// Product Types
export interface Product {
  id: string;
  name: string;
  description?: string;
  picture?: string;
  product_image_url?: string;
  image_url?: string;  // Standardized image URL field
  price?: number;
  price_usd_units?: number;
  category?: string;
  distance?: number;
}

export interface ProductListData {
  type: "product_list";
  products: Product[];
}

export interface CartData {
  type: "cart";
  items: CartItem[];
  total_items: number;
  subtotal: number;
}

export interface A2AArtifact {
  artifactId?: string;
  name: string;
  parts: A2APart[];
}

export interface A2APart {
  kind: "text" | "data" | "file";
  text?: string;
  data?: any;
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

export interface OrderItem {
  product_id: string;
  name: string;
  quantity: number;
  price: number;
  picture?: string;
  subtotal?: number;
}

export interface Order {
  order_id: string;
  status: string;
  items: OrderItem[];
  total_amount: number;
  shipping_address?: string;
  created_at?: string;
}

export interface OrderData {
  type: "order";
  order_id: string;
  status: string;
  items: OrderItem[];
  total_amount: number;
  shipping_address?: string;
  created_at?: string;
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
