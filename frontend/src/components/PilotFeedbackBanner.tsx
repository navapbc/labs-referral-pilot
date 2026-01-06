import { Button } from "@/components/ui/button";
import { MessageCircle } from "lucide-react";

export function PilotFeedbackBanner() {
  return (
    <div className="bg-amber-50 border-b border-amber-200 px-6 py-4">
      <div className="flex items-center justify-between gap-4">
        {/* Left section with icon and text */}
        <div className="flex items-start gap-3">
          <div className="text-2xl">🚧</div>
          <div>
            <p className="font-semibold text-amber-900">
              Pilot Version - Work in Progress
            </p>
            <p className="text-sm text-amber-900">
              This tool is being tested with Goodwill staff. Please share
              feedback if you spot issues or have suggestions!
            </p>
          </div>
        </div>

        {/* Right section with button */}
        <Button
          variant="outline"
          className="bg-white hover:bg-amber-100 border-amber-300 text-amber-900 hover:text-amber-900 hover:border-amber-400 cursor-pointer"
          onClick={() =>
            window.open("https://forms.gle/nfBWHpVbXT1kdSX3A", "_blank")
          }
        >
          <MessageCircle className="w-4 h-4" />
          Share Feedback
        </Button>
      </div>
    </div>
  );
}
