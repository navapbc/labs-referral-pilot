"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Printer, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

import { fetchResources } from "@/util/fetchResources";
import { Resource } from "@/types/resources";
import "@/app/globals.css";

import { PrintableReferralsReport } from "@/util/printReferrals";

export default function Page() {
  const [clientDescription, setClientDescription] = useState("");
  const [result, setResult] = useState<Resource[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [readyToPrint, setReadyToPrint] = useState(false);

  useEffect(() => {
    if (result === null) return;
    // optional side effects on result change
  }, [result]);

  async function handleClick() {
    setLoading(true);
    setResult(null);
    try {
      const resources = await fetchResources(clientDescription); // returns Resource[]
      setResult(resources);
      setReadyToPrint(true);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Unknown error";
      console.error(message);
      setResult([]); // or keep null to hide area
    } finally {
      setLoading(false);
    }
  }

  function handlePrint() {
    // App chrome will hide; print-only section will show
    window.print();
  }

  return (
    <>
      {/* ----- App chrome (hidden when printing) ----- */}
      <div className="print:hidden">
        {readyToPrint && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 justify-end pr-20 pt-4">
              <Button
                onClick={handlePrint}
                variant="outline"
                className="hover:bg-gray-100 hover:text-gray-900"
              >
                <Printer
                  data-testid="printReferralsButton"
                  className="w-4 h-4 mr-2"
                />
                Print Referrals
              </Button>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-2 pl-20 pr-20 mt-8 mb-8">
          <div className="m-3">
            <Label
              className="font-medium text-gray-900 text-lg mb-1"
              htmlFor="clientDescriptionInput"
            >
              Tell us about your client
            </Label>
            <Textarea
              placeholder="Add details about the client's specific situation, needs, and circumstances here..."
              id="clientDescriptionInput"
              value={clientDescription}
              onChange={(e) => setClientDescription(e.target.value)}
              className="min-h-[8rem] min-w-[16rem] text-base"
              data-testid="clientDescriptionInput"
            />
          </div>

          <Button
            type="button"
            onClick={() => void handleClick()}
            disabled={!clientDescription.trim() || loading}
            className="min-w-[16rem] ml-3 mr-3 generate-referrals-button text-lg pt-6 pb-6"
            data-testid="findResourcesButton"
          >
            <Sparkles className="w-5 h-5" />
            {loading ? "Generating Resources..." : "Find Resources"}
          </Button>

          {/* On-screen results (normal cards) */}
          {result && result.length === 0 && (
            <div className="m-3">No resources found.</div>
          )}
          {result && result.length > 0 && (
            <div className="m-3">
              {result.map((r, i) => (
                <Card key={i} className="bg-white shadow-sm mb-5 min-w-[16rem]">
                  <CardHeader>
                    <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                      <span className="flex-shrink-0 w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-m font-medium">
                        {i + 1}
                      </span>
                      {r.name}
                      {!!r.website && (
                        <Link
                          href={r.website}
                          rel="noopener noreferrer"
                          target="_blank"
                          className="text-base text-gray-500 flex items-center gap-2"
                        >
                          {r.website}
                        </Link>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="ml-4 mr-4">
                    {r.description && (
                      <div className="font-medium mb-2">{r.description}</div>
                    )}
                    {r.addresses && r.addresses?.length > 0 && (
                      <div className="mt-1">
                        <span className="font-semibold">
                          Address{r.addresses.length > 1 ? "es" : ""}:
                        </span>{" "}
                        {r.addresses.join(" | ")}
                      </div>
                    )}
                    {r.phones && r.phones?.length > 0 && (
                      <div className="mt-1">
                        <span className="font-semibold">Phone:</span>{" "}
                        {r.phones.join(" | ")}
                      </div>
                    )}
                    {r.emails && r.emails?.length > 0 && (
                      <div className="mt-1">
                        <span className="font-semibold">Email:</span>{" "}
                        {r.emails.join(" | ")}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ----- Print-only section ----- */}
      <div className="hidden print:block">
        <PrintableReferralsReport resources={result ?? []} />
      </div>
    </>
  );
}
