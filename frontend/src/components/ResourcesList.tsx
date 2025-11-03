import { Resource } from "@/types/resources";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import React from "react";
import { HandHeart, Landmark } from "lucide-react";

const referralTypeIndicator = (referralType: string | undefined) => {
  switch (referralType) {
    case "goodwill": {
      return (
        <span
          data-testid="goodwill_referral"
          className="inline-flex items-center gap-1.5 bg-transparent text-blue-800 ml-4 mt-3 px-2.5 py-1 max-w-[15rem] text-sm font-bold"
        >
          <img
            src="/img/Goodwill_Industries_Logo.svg"
            alt="Goodwill"
            className="h-5 w-5 shrink-0"
          />
          <span className="truncate">Goodwill</span>
        </span>
      );
    }
    case "government": {
      return (
        <span
          data-testid="government_referral"
          className="inline-flex items-center gap-1.5 bg-transparent text-gray-800 ml-4 mt-3 px-2.5 py-1 max-w-[15rem] text-sm font-bold"
        >
          <Landmark className="h-4 w-4 shrink-0" />
          <span className="truncate">Government</span>
        </span>
      );
    }
    case "external": {
      return (
        <span
          data-testid="external_referral"
          className="inline-flex items-center gap-1.5 bg-transparent text-green-800 ml-4 mt-3 px-2.5 py-1 max-w-[15rem] text-sm font-bold"
        >
          <HandHeart className="h-4 w-4 shrink-0" />
          <span className="truncate">External</span>
        </span>
      );
    }
    default: {
      return null;
    }
  }
};

const normalizeUrl = (url: string) => {
  const trimmed = url.trim();
  if (/^(https?:)?\/\//i.test(trimmed) || /^(mailto:|tel:)/i.test(trimmed)) {
    return trimmed.startsWith("//") ? `https:${trimmed}` : trimmed;
  }
  return `https://${trimmed}`;
};

const ResourcesList = ({
  resources,
  errorMessage,
}: {
  resources: Resource[];
  errorMessage?: string;
}) => {
  return resources.length === 0 ? (
    <div className="m-3">{errorMessage || "No resources found."}</div>
  ) : (
    <div className="mt-2">
      {resources.map((r, i) => (
        <Card key={i} className="bg-white shadow-sm mb-5 min-w-[16rem]">
          {referralTypeIndicator(r.referral_type)}
          <CardHeader className="p-3 ml-3">
            <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <span className="flex-shrink-0 w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-m font-medium">
                {i + 1}
              </span>
              <div>{r.name}</div>
              {!!r.website && (
                <Link
                  href={normalizeUrl(r.website)}
                  rel="noopener noreferrer"
                  target="_blank"
                  className="text-base text-gray-500 flex items-center gap-2"
                >
                  {r.website}
                </Link>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="ml-9 mr-4">
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
  );
};

export default ResourcesList;
