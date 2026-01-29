import { ShareOptionsDialog, ShareMode } from "./ShareOptionsDialog";

export type EmailMode = ShareMode;

interface EmailOptionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectMode: (mode: EmailMode) => void;
  hasActionPlan: boolean;
}

export function EmailOptionsDialog(props: EmailOptionsDialogProps) {
  return <ShareOptionsDialog {...props} variant="email" />;
}
