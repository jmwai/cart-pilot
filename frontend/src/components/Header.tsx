'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="mx-auto flex items-center justify-between h-16 w-full">
          {/* Logo */}
          <Link href="/" className="flex items-center flex-shrink-0">
            <Image 
              src="/logo.png" 
              alt="Cart Pilot" 
              width={120} 
              height={40}
              className="h-8 w-auto"
              priority
            />
          </Link>

          {/* Navigation - Hidden on mobile, visible on tablet and up */}
          <nav className="hidden md:flex items-center flex-1 justify-center">
            <span className="text-sm font-medium text-gray-900">Find Your Perfect Pair</span>
          </nav>

          {/* Auth Buttons - Compact on mobile */}
          <div className="flex items-center gap-2 sm:gap-4">
            <button className="text-xs font-normal text-gray-900 hover:text-gray-600 transition-colors whitespace-nowrap">
              Sign Up
            </button>
            <button className="text-xs font-normal text-gray-900 hover:text-gray-600 transition-colors whitespace-nowrap">
              Login
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
