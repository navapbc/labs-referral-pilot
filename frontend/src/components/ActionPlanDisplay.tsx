import { ActionPlan, PartialActionPlan } from "@/util/fetchActionPlan";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import { parseMarkdownToHTML } from "@/util/markdown";

interface ActionPlanDisplayProps {
  actionPlan: ActionPlan | null;
  streamingPlan?: PartialActionPlan | null;
  isStreaming?: boolean;
}

export function ActionPlanDisplay({
  actionPlan,
  streamingPlan,
  isStreaming,
}: ActionPlanDisplayProps) {
  // If streaming, show partial content with progressive rendering
  if (isStreaming && streamingPlan) {
    const displayTitle = streamingPlan.title || "Generating Action Plan...";

    return (
      <Card className="bg-blue-50 border-blue-200 shadow-sm mb-5">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-blue-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            {displayTitle}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Show summary if available */}
          {streamingPlan.summary && (
            <div className="mb-3 text-black text-base">
              {streamingPlan.summary}
            </div>
          )}

          {/* Show content with markdown rendering and blinking cursor */}
          {streamingPlan.content && (
            <div className="relative">
              <div
                className="prose prose-sm max-w-none text-gray-800"
                dangerouslySetInnerHTML={{
                  __html: parseMarkdownToHTML(streamingPlan.content),
                }}
              />
              {/* Blinking cursor to indicate streaming */}
              <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1 align-middle">
                |
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Otherwise show parsed action plan (final complete version)
  if (!actionPlan) return null;

  return (
    <Card className="bg-blue-50 border-blue-200 shadow-sm mb-5">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-blue-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          {actionPlan.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 text-black text-base">{actionPlan.summary}</div>
        <div
          className="prose prose-sm max-w-none text-gray-800"
          dangerouslySetInnerHTML={{
            __html: parseMarkdownToHTML(actionPlan.content),
          }}
        />
      </CardContent>
    </Card>
  );
}
