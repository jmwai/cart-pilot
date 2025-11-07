/**
 * Message bubble component for displaying individual messages
 */
import { MessageWithArtifacts } from '@/types/chat';

interface MessageBubbleProps {
  message: MessageWithArtifacts;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] px-4 py-2 rounded-lg ${
          message.role === 'user'
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        {/* Display image if present */}
        {message.imageUrl && (
          <div className="mb-2">
            <img
              src={message.imageUrl}
              alt="Uploaded"
              className="max-w-full h-auto rounded-lg max-h-64 object-contain"
            />
          </div>
        )}
        <p className="text-sm whitespace-pre-wrap">
          {typeof message.content === 'string' ? message.content : String(message.content || '')}
        </p>
        <p className="text-xs mt-1 opacity-70">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

