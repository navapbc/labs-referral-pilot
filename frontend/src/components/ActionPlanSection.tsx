import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Resource } from "@/types/resources";
import { ActionPlan } from "@/util/fetchActionPlan";
import { parseMarkdownToHTML } from "@/util/markdown";

interface ActionPlanSectionProps {
  resources: Resource[];
  selectedResources: Resource[];
  actionPlan: ActionPlan | null;
  isGeneratingActionPlan: boolean;
  onResourceSelection: (resource: Resource, checked: boolean) => void;
  onSelectAllResources: () => void;
  onGenerateActionPlan: () => void;
}

export function ActionPlanSection({
  resources,
  selectedResources,
  actionPlan,
  isGeneratingActionPlan,
  onResourceSelection,
  onSelectAllResources,
  onGenerateActionPlan,
}: ActionPlanSectionProps) {
  return (
    <>
      {/* Action Plan Section */}
      <Card className="bg-white shadow-sm mb-5">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Select Resources for Action Plan
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={onSelectAllResources}
              className="text-xs"
            >
              {selectedResources.length === resources.length
                ? "Deselect All"
                : "Select All"}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {resources.map((resource, index) => (
              <div key={index} className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id={`resource-${index}`}
                  className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  onChange={(e) =>
                    onResourceSelection(resource, e.target.checked)
                  }
                  checked={selectedResources.some(
                    (r) => r.name === resource.name,
                  )}
                />
                <label
                  htmlFor={`resource-${index}`}
                  className="flex-1 cursor-pointer"
                >
                  <div className="font-medium text-gray-900">
                    {resource.name}
                  </div>
                  {resource.description && (
                    <div className="text-sm text-gray-600">
                      {resource.description}
                    </div>
                  )}
                </label>
              </div>
            ))}
          </div>
          {selectedResources.length > 0 && (
            <div className="mt-4 pt-3 border-t">
              <Button
                onClick={onGenerateActionPlan}
                disabled={isGeneratingActionPlan}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {!isGeneratingActionPlan && (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Action Plan ({selectedResources.length} selected)
                  </>
                )}
                {isGeneratingActionPlan && (
                  <>
                    <Spinner />
                    Generating Action Plan...
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Plan Display */}
      {actionPlan && (
        <Card className="bg-blue-50 border-blue-200 shadow-sm mb-5">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-blue-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              {actionPlan.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3 text-black text-base">
              {actionPlan.summary}
            </div>
            <div
              className="prose prose-sm max-w-none text-gray-800"
              dangerouslySetInnerHTML={{
                __html: parseMarkdownToHTML(actionPlan.content),
              }}
            />
          </CardContent>
        </Card>
      )}
    </>
  );
}
