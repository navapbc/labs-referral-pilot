import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FileText, List } from "lucide-react";

export type PrintMode = "action-plan-only" | "full-referrals";

interface PrintOptionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectMode: (mode: PrintMode) => void;
  hasActionPlan: boolean;
}

export function PrintOptionsDialog({
  open,
  onOpenChange,
  onSelectMode,
  hasActionPlan,
}: PrintOptionsDialogProps) {
  const handleSelect = (mode: PrintMode) => {
    onSelectMode(mode);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>What would you like to print?</DialogTitle>
          <DialogDescription>
            Choose what to include in your printed report.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3 mt-4">
          {hasActionPlan && (
            <Button
              variant="outline"
              className="h-auto py-4 px-4 justify-start text-left"
              onClick={() => handleSelect("action-plan-only")}
              data-testid="print-action-plan-only"
            >
              <FileText className="w-5 h-5 mr-3 flex-shrink-0 text-blue-600" />
              <div>
                <div className="font-semibold">Action Plan Only</div>
                <div className="text-sm text-gray-500 font-normal">
                  Includes contact info for selected resources (no descriptions)
                </div>
              </div>
            </Button>
          )}
          <Button
            variant="outline"
            className="h-auto py-4 px-4 justify-start text-left"
            onClick={() => handleSelect("full-referrals")}
            data-testid="print-full-referrals"
          >
            <List className="w-5 h-5 mr-3 flex-shrink-0 text-blue-600" />
            <div>
              <div className="font-semibold">
                {hasActionPlan
                  ? "Action Plan + Full Referrals"
                  : "Full Referrals"}
              </div>
              <div className="text-sm text-gray-500 font-normal">
                Includes complete resource details with descriptions
              </div>
            </div>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
