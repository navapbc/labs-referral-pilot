"use client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

import "@/app/globals.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Label } from "@/components/ui/label";
import { fetchResources, Resource } from "@/util/fetchResources";

export default function Page() {
  const [clientDescription, setClientDescription] = useState("");
  const [result, setResult] = useState<Resource[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    setResult(null);

    try {
      const resources = await fetchResources(clientDescription);
      // @ts-expect-error we can trust this will be a list of Resources coming from our API endpoint
      setResult(resources);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Unknown error";
      console.error(message);
      setResult([]); // or keep `null` if you prefer to hide the results area
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="flex flex-col gap-2 pl-20 pr-20 mt-8 mb-8">
        <div className="m-3">
          <Label className="font-medium text-gray-900 text-lg mb-1" htmlFor="clientDescriptionInput">
            Tell us about your client
          </Label>
          <Textarea
            placeholder="Add details about the client's specific situation, needs, and circumstances here..."
            id="clientDescriptionInput"
            value={clientDescription}
            onChange={(e) => setClientDescription(e.target.value)}
            className="min-h-[8rem] min-w-[16rem] text-base border-gray-300 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <Button
          type="button"
          onClick={() => void handleClick()}
          disabled={!clientDescription.trim() || loading}
          className="min-w-[16rem] ml-3 mr-3 generate-referrals-button text-lg pt-6 pb-6"
        >
          <Sparkles className="w-5 h-5" />
          {loading ? "Generating Resources..." : "Find Resources"}
        </Button>
        {displayResourcesFromResult(result)}
      </div>
    </>
  );
}

function displayResourcesFromResult(result: Resource[] | null) {
  if (result == null) return null;
  if (result.length === 0)
    return <div className="margin-top-2">No resources found.</div>;

  return (
    <div className="m-3">
      {result.map((r, i) => (
        <Card key={i} className="bg-white shadow-sm mb-5 min-w-[16rem]">
          <CardHeader>
            <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <span className="flex-shrink-0 w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-m font-medium">
                {i + 1}
              </span>
              {r.name}
              <Link
                href={r.website}
                rel="noopener noreferrer"
                className="text-base text-gray-500 flex items-center gap-2"
              >
                {r.website}
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent className="ml-4 mr-4">
            {r.description && (
              <div className="text-bold mb-2">{r.description}</div>
            )}

            {r.addresses?.length > 0 && (
              <div className="mt-1">
                <span className="font-semibold">
                  Address{r.addresses.length > 1 ? "es" : ""}:
                </span>{" "}
                {r.addresses.join(" | ")}
              </div>
            )}

            {r.phones?.length > 0 && (
              <div className="mt-1">
                <span className="font-semibold">Phone:</span>{" "}
                {r.phones.join(" | ")}
              </div>
            )}
            {r.emails?.length > 0 && (
              <div className="mt-1">
                <span className="font-semibold">Email:</span>{" "}
                {r.emails.join(" | ")}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
