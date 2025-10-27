'use client';

import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
              <span className="text-white font-bold text-lg">SS</span>
            </div>
            <span className="text-xl font-bold text-gray-900">Sole Search</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              New Arrivals
            </Link>
            <Link href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              Brands
            </Link>
            <Link href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              Men
            </Link>
            <Link href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              Women
            </Link>
            <Link href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              Sale
            </Link>
          </nav>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
            <button className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
              Sign Up
            </button>
            <button className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors">
              Login
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
