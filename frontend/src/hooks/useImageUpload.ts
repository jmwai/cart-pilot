/**
 * Hook for handling image uploads
 */
import { useState, useRef, useCallback } from 'react';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const VALID_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export function useImageUpload() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!VALID_IMAGE_TYPES.includes(file.type)) {
      alert('Please select a valid image file (JPEG, PNG, or WebP)');
      e.target.value = ''; // Reset input
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      alert('Image size must be less than 10MB');
      e.target.value = ''; // Reset input
      return;
    }

    // Store selected image
    setSelectedImage(file);
  }, []);

  const clearImage = useCallback(() => {
    setSelectedImage(null);
    setImageUrl(undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const createImageUrl = useCallback((file: File | null): string | undefined => {
    if (!file) return undefined;
    return URL.createObjectURL(file);
  }, []);

  const openFileDialog = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return {
    selectedImage,
    imageUrl,
    fileInputRef,
    handleImageSelect,
    clearImage,
    createImageUrl,
    openFileDialog,
  };
}

