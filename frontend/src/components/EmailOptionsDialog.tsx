import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FileText, List } from "lucide-react";

export type EmailMode = "action-plan-only" | "full-referrals";

interface EmailOptionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectMode: (mode: EmailMode) => void;
  hasActionPlan: boolean;
}

export function EmailOptionsDialog({
  open,
  onOpenChange,
  onSelectMode,
  hasActionPlan,
}: EmailOptionsDialogProps) {
  const handleSelect = (mode: EmailMode) => {
    onSelectMode(mode);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-lg"
        aria-describedby="email-options-description"
      >
        <DialogHeader>
          <DialogTitle>What would you like to email?</DialogTitle>
          <DialogDescription id="email-options-description">
            Choose what to include in your email.
          </DialogDescription>
        </DialogHeader>
        <div
          className="flex flex-col gap-3 mt-4"
          role="group"
          aria-label="Email options"
        >
          {hasActionPlan && (
            <Button
              variant="outline"
              className="h-auto py-4 px-5 justify-start text-left border-gray-300 hover:bg-blue-50 hover:border-blue-300 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              onClick={() => handleSelect("action-plan-only")}
              data-testid="email-action-plan-only"
              aria-describedby="email-action-plan-only-desc"
            >
              <FileText
                className="w-5 h-5 mr-3 flex-shrink-0 text-blue-700"
                aria-hidden="true"
              />
              <div>
                <div className="font-semibold text-gray-900">
                  Action Plan Only
                </div>
                <div
                  id="email-action-plan-only-desc"
                  className="text-sm text-gray-700 font-normal"
                >
                  Includes contact info for selected resources (no descriptions)
                </div>
              </div>
            </Button>
          )}
          <Button
            variant="outline"
            className="h-auto py-4 px-5 justify-start text-left border-gray-300 hover:bg-blue-50 hover:border-blue-300 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            onClick={() => handleSelect("full-referrals")}
            data-testid="email-full-referrals"
            aria-describedby="email-full-referrals-desc"
          >
            <List
              className="w-5 h-5 mr-3 flex-shrink-0 text-blue-700"
              aria-hidden="true"
            />
            <div>
              <div className="font-semibold text-gray-900">
                {hasActionPlan
                  ? "Action Plan + Full Referrals"
                  : "Full Referrals"}
              </div>
              <div
                id="email-full-referrals-desc"
                className="text-sm text-gray-700 font-normal"
              >
                Includes complete resource details with descriptions
              </div>
            </div>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
