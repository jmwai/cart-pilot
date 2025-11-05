'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ProductImageProps {
  src: string | null | undefined;
  alt: string;
  className?: string;
}

export default function ProductImage({ src, alt }: ProductImageProps) {
  const [imageError, setImageError] = useState(false);

  if (!src || imageError) {
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center">
        <span className="text-gray-400 text-xs">No Image</span>
      </div>
    );
  }

  // Handle external URLs and local images
  const isExternalUrl = src.startsWith('http://') || src.startsWith('https://');
  
  return (
    <Image
      src={src}
      alt={alt}
      fill
      className="object-contain"
      onError={() => setImageError(true)}
      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      unoptimized={isExternalUrl}
      priority={false}
    />
  );
}

