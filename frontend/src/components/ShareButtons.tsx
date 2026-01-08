import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmailReferralsButton } from "@/components/EmailReferralsButton";
import { cn } from "@/lib/utils";

interface ShareButtonsProps {
  onPrint: () => void;
  resourcesResultId: string;
  actionPlanResultId: string;
  className?: string;
}

export function ShareButtons({
  onPrint,
  resourcesResultId,
  actionPlanResultId,
  className,
}: ShareButtonsProps) {
  return (
    <div className={cn("flex gap-2", className)}>
      <Button
        onClick={onPrint}
        variant="outline"
        className="hover:bg-gray-100 hover:text-gray-900"
        data-testid="printReferralsButton"
      >
        <Printer className="w-4 h-4" aria-hidden="true" />
        Print
      </Button>
      {resourcesResultId && (
        <EmailReferralsButton
          resultId={resourcesResultId}
          actionPlanResultId={actionPlanResultId || undefined}
        />
      )}
    </div>
  );
}
