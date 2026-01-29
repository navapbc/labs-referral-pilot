import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, CheckCircle } from "lucide-react";
import { parseMarkdownToHTML } from "@/util/markdown";

interface ReasoningDisplayProps {
  reasoningText: string;
  isThinking: boolean;
}

/**
 * Displays the AI's reasoning process during resource generation.
 * Shows a streaming "thinking" state while the model reasons, then
 * displays the complete reasoning summary when done.
 */
export function ReasoningDisplay({
  reasoningText,
  isThinking,
}: ReasoningDisplayProps) {
  if (!reasoningText) return null;

  return (
    <Card className="bg-blue-50 border-blue-200 shadow-sm mb-4">
      <CardContent className="pt-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {isThinking ? (
              <Sparkles
                className="h-5 w-5 text-blue-600 animate-pulse motion-reduce:animate-none"
                aria-hidden="true"
              />
            ) : (
              <CheckCircle
                className="h-5 w-5 text-blue-600"
                aria-hidden="true"
              />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-blue-800 mb-1">
              {isThinking ? "Analyzing your request..." : "Analysis complete"}
            </h4>
            <div
              className="text-sm text-blue-700 prose prose-sm max-w-none prose-headings:text-blue-800 prose-strong:text-blue-800"
              dangerouslySetInnerHTML={{
                __html: parseMarkdownToHTML(reasoningText),
              }}
            />
            {isThinking && (
              <span
                className="inline-block w-2 h-3 bg-blue-600 animate-pulse motion-reduce:animate-none ml-1 align-middle"
                aria-hidden="true"
              />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
