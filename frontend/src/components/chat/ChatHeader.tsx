/**
 * Chat header component with title and close button
 */
interface ChatHeaderProps {
  onClose?: () => void;
  showCloseButton?: boolean;
}

export default function ChatHeader({ onClose, showCloseButton = false }: ChatHeaderProps) {
  return (
    <div className="bg-blue-600 text-white px-4 py-4 flex items-center justify-between border-b border-blue-700 h-16 flex-shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="font-semibold">Shopping Assistant</span>
      </div>
      {showCloseButton && onClose && (
        <button
          onClick={onClose}
          className="hover:bg-blue-700 rounded p-1 transition-colors"
          aria-label="Close chat"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

