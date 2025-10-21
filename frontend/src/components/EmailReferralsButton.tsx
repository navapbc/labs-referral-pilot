"use client";

import React, { useState } from "react";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { emailResult } from "@/util/emailResult";

interface EmailReferralsProps {
  resultId: string;
}

export function EmailReferralsButton({ resultId }: EmailReferralsProps) {
  const [email, setEmail] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendEmail = async () => {
    setIsLoading(true);
    setStatusMessage("");

    try {
      const { emailAddr, message } = await emailResult(resultId, email);

      setStatusMessage(`Referrals sent to ${emailAddr}`);
      setTimeout(() => {
        setIsOpen(false);
        setStatusMessage("");
      }, 10000);
    } catch (error) {
      console.error("Error sending email:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      setStatusMessage(`Failed to send referrals: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          className="hover:bg-gray-100 hover:text-gray-900"
          data-testid="emailReferralsButton"
        >
          <Mail className="w-4 h-4" />
          Email Referrals
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Email Referrals</SheetTitle>
          <SheetDescription>
            Enter your email address to receive the referrals.
          </SheetDescription>
        </SheetHeader>
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
        <SheetFooter>
          <div>
            <Button
              type="submit"
              onClick={handleSendEmail}
              disabled={!email.trim() || isLoading}
              data-testid="sendEmailButton"
            >
              {isLoading ? "Sending..." : "Send Email"}
            </Button>
            {statusMessage && (
              <p
                className={`mt-2 text-sm ${
                  statusMessage.includes("Failed")
                    ? "text-red-500"
                    : "text-black-600"
                }`}
              >
                {statusMessage}
              </p>
            )}
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
