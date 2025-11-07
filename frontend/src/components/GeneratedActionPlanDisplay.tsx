import { ActionPlan } from "@/util/fetchActionPlan";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import { parseMarkdownToHTML } from "@/util/markdown";
export function GeneratedActionPlanDisplay({
  actionPlan,
}: {
  actionPlan: ActionPlan;
}) {
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
