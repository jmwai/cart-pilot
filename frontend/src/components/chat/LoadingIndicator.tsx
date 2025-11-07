/**
 * Loading indicator component with typing animation
 */
import { renderLoadingMessage } from '@/lib/utils/statusMessageUtils';

interface LoadingIndicatorProps {
  message: string;
}

export default function LoadingIndicator({ message }: LoadingIndicatorProps) {
  return (
    <div className="flex justify-start">
      <div className="bg-white text-gray-800 px-4 py-3 rounded-lg border border-gray-200 flex items-center gap-2">
        {/* Typing animation */}
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
        </div>
        <p className="text-sm">
          {renderLoadingMessage(message)}
        </p>
      </div>
    </div>
  );
}

