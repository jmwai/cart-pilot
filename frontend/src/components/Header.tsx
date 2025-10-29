'use client';

import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <span className="text-sm font-medium text-gray-900">Sole Search</span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center">
            <span className="text-sm font-medium text-gray-900">Find Your Perfect Pair</span>
          </nav>

          {/* Auth Buttons */}
          <div className="flex items-center gap-4">
            <button className="text-xs font-normal text-gray-900 hover:text-gray-600 transition-colors">
              Sign Up
            </button>
            <button className="text-xs font-normal text-gray-900 hover:text-gray-600 transition-colors">
              Login
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
