/**
 * Chat input component with text input and image upload
 */
import { RefObject } from 'react';

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  selectedImage: File | null;
  onImageSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isInitialized: boolean;
  inputRef: RefObject<HTMLInputElement | null>;
  fileInputRef: RefObject<HTMLInputElement | null>;
}

export default function ChatInput({
  input,
  setInput,
  selectedImage,
  onImageSelect,
  onSubmit,
  isLoading,
  isInitialized,
  inputRef,
  fileInputRef,
}: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="p-4 border-t border-gray-200 bg-white flex-shrink-0">
      <div className="flex gap-2">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={onImageSelect}
          className="hidden"
        />

        {/* Camera icon button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || !isInitialized}
          className="px-3 py-3 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          aria-label="Upload image"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>

        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={selectedImage ? 'Add optional text...' : 'Type your message...'}
          className="flex-1 px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading || !isInitialized}
        />
        <button
          type="submit"
          disabled={isLoading || (!input.trim() && !selectedImage) || !isInitialized}
          className="px-5 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      {/* Show selected image preview */}
      {selectedImage && (
        <div className="mt-2 text-sm text-gray-600">
          Selected: {selectedImage.name} ({(selectedImage.size / 1024 / 1024).toFixed(2)} MB)
        </div>
      )}
    </form>
  );
}

