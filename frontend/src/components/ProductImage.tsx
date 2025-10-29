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
      <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
        <span className="text-gray-400 text-sm">No Image</span>
      </div>
    );
  }

  return (
    <Image
      src={src}
      alt={alt}
      fill
      className="object-cover"
      onError={() => setImageError(true)}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      unoptimized
    />
  );
}

