"use client";

import React, { useState } from "react";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { emailResult } from "@/util/emailResult";

interface EmailReferralsProps {
  resultId: string;
}

export function EmailReferralsButton({ resultId }: EmailReferralsProps) {
  const [email, setEmail] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSendEmail = async () => {
    setIsLoading(true);
    setStatusMessage("");

    try {
      const { emailAddr } = await emailResult(resultId, email);

      setEmailSent(true);
      setStatusMessage(`Email sent successfully to ${emailAddr}`);
    } catch (error) {
      console.error("Error sending email:", error);
      setStatusMessage("There was an error sending the email, please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    console.log("Closing");
    setEmailSent(false);
    setStatusMessage("");
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="hover:bg-gray-100 hover:text-gray-900"
          data-testid="emailReferralsButton"
        >
          <Mail className="w-4 h-4" />
          Email Referrals
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Email Referrals</DialogTitle>
          <DialogDescription>
            Enter your email address to receive the referrals.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              data-testid="emailInput"
            />
          </div>
        </div>
        <DialogFooter>
          <div className="w-full space-y-2">
            <div className="flex gap-2 justify-end">
              <DialogClose asChild>
                <Button
                  type="button"
                  onClick={handleClose}
                  disabled={isLoading}
                  variant="outline"
                  data-testid="cancelEmailButton"
                >
                  {emailSent ? "Close" : "Cancel"}
                </Button>
              </DialogClose>
              <Button
                type="submit"
                onClick={() => void handleSendEmail()}
                disabled={!email.trim() || isLoading || emailSent}
                data-testid="sendEmailButton"
              >
                {isLoading ? "Sending..." : "Send Email"}
              </Button>
            </div>
            {statusMessage && (
              <p
                className={`text-sm ${
                  statusMessage.includes("Failed")
                    ? "text-red-500"
                    : "text-green-900"
                }`}
              >
                {statusMessage}
              </p>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
