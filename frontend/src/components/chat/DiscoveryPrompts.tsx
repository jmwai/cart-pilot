/**
 * Discovery prompts component for suggesting queries
 */
interface DiscoveryPromptsProps {
  prompts: string[];
  onPromptClick: (prompt: string) => void;
  isLoading: boolean;
}

export default function DiscoveryPrompts({ prompts, onPromptClick, isLoading }: DiscoveryPromptsProps) {
  if (isLoading) return null;

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 font-medium">Try asking:</p>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onPromptClick(prompt)}
            className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors text-gray-700"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}

