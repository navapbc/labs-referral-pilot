import { ActionPlan, PartialActionPlan } from "@/util/fetchActionPlan";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import {
  parseMarkdownToHTML,
  extractCitations,
  Citation,
} from "@/util/markdown";

interface ActionPlanDisplayProps {
  actionPlan: ActionPlan | null;
  streamingPlan?: PartialActionPlan | null;
  isStreaming?: boolean;
}

// Split content into sections by h2 headings for better visual separation
function splitIntoSections(content: string): string[] {
  // Split on h2 markdown headings (## Title)
  const sections = content.split(/(?=^## )/m).filter((s) => s.trim());
  return sections;
}

// Validate URL uses safe protocol (http/https only)
function isSafeUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

// Sources section component
function SourcesSection({ citations }: { citations: Citation[] }) {
  // Filter to only citations with safe URLs
  const safeCitations = citations.filter((c) => isSafeUrl(c.url));
  if (safeCitations.length === 0) return null;

  return (
    <nav aria-label="Sources" className="mt-6 pt-4 border-t border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Sources</h3>
      <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
        {safeCitations.map((citation, index) => (
          <li key={index}>
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              {citation.domain}
              <span className="sr-only"> (opens in new tab)</span>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
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
      <Card className="bg-gray-100 border-gray-200 shadow-sm mb-5">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" aria-hidden="true" />
            {displayTitle}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Show summary if available */}
          {streamingPlan.summary && (
            <div className="mb-4 text-gray-800 text-base">
              {streamingPlan.summary}
            </div>
          )}

          {/* Show content with markdown rendering and blinking cursor */}
          {streamingPlan.content && (
            <div className="relative bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
              <div
                className="prose prose-sm max-w-none text-gray-800"
                dangerouslySetInnerHTML={{
                  __html: parseMarkdownToHTML(streamingPlan.content),
                }}
              />
              {/* Blinking cursor to indicate streaming */}
              <span
                className="inline-block w-2 h-4 bg-blue-600 animate-pulse motion-reduce:animate-none ml-1 align-middle"
                aria-hidden="true"
              />
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Otherwise show parsed action plan (final complete version)
  if (!actionPlan) return null;

  // Extract citations from content for the sources section
  const { content: contentWithRefs, citations } = extractCitations(
    actionPlan.content,
  );
  const sections = splitIntoSections(contentWithRefs);

  return (
    <Card className="bg-gray-100 border-gray-200 shadow-sm mb-5">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" aria-hidden="true" />
          {actionPlan.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-6 text-gray-800 text-base">{actionPlan.summary}</div>

        {/* Render each resource section in its own card */}
        <div className="space-y-6">
          {sections.map((section, index) => (
            <div
              key={index}
              className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm"
            >
              <div
                className="prose prose-sm max-w-none text-gray-800"
                dangerouslySetInnerHTML={{
                  __html: parseMarkdownToHTML(section),
                }}
              />
            </div>
          ))}
        </div>

        {/* Sources section at bottom */}
        <SourcesSection citations={citations} />
      </CardContent>
    </Card>
  );
}
