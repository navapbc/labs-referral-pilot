"use client";
import React, { useState } from "react";
import Link from "next/link";
import {
  Accessibility,
  Baby,
  Briefcase,
  Building,
  Car,
  ChevronLeft,
  DollarSign,
  FileText,
  Flag,
  GraduationCap,
  Heart,
  Home,
  MapPin,
  Printer,
  Scale,
  Shield,
  Sparkles,
  Stethoscope,
  Users,
  Utensils,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

import { fetchResources } from "@/util/fetchResources";
import { Resource } from "@/types/resources";
import "@/app/globals.css";

import { PrintableReferralsReport } from "@/util/printReferrals";
import { Input } from "@/components/ui/input";

const resourceCategories = [
  {
    id: "employment",
    label: "Employment & Job Training",
    icon: Briefcase,
  },
  {
    id: "housing",
    label: "Housing & Shelter",
    icon: Home,
  },
  {
    id: "food",
    label: "Food Assistance",
    icon: Utensils,
  },
  {
    id: "transportation",
    label: "Transportation",
    icon: Car,
  },
  {
    id: "healthcare",
    label: "Healthcare & Mental Health",
    icon: Stethoscope,
  },
  {
    id: "childcare",
    label: "Childcare",
    icon: Baby,
  },
  {
    id: "financial",
    label: "Financial Assistance",
    icon: DollarSign,
  },
  {
    id: "education",
    label: "Education & GED",
    icon: GraduationCap,
  },
  {
    id: "legal",
    label: "Legal Services",
    icon: Scale,
  },
  {
    id: "substance",
    label: "Substance Abuse Treatment",
    icon: Shield,
  },
  {
    id: "disability",
    label: "Disability Services",
    icon: Accessibility,
  },
  {
    id: "veterans",
    label: "Veterans Services",
    icon: Flag,
  },
];

export default function Page() {
  const [clientDescription, setClientDescription] = useState("");
  const [result, setResult] = useState<Resource[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [readyToPrint, setReadyToPrint] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [locationText, setLocationText] = useState("");
  const [selectedResourceTypes, setSelectedResourceTypes] = useState<string[]>(
    [],
  );

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId],
    );
  };

  const clearAllFilters = () => {
    setSelectedCategories([]);
    setLocationText("");
    setSelectedResourceTypes([]);
  };

  const toggleResourceType = (type: string) => {
    setSelectedResourceTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  };

  async function handleClick() {
    setLoading(true);
    setResult(null);
    try {
      const request = clientDescription + getCollatedReferralOptions();
      const resources = await fetchResources(request); // returns Resource[]
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

  function handleReturnToSearch() {
    setReadyToPrint(false);
  }

  const normalizeUrl = (url: string) => {
    const trimmed = url.trim();
    if (/^(https?:)?\/\//i.test(trimmed) || /^(mailto:|tel:)/i.test(trimmed)) {
      return trimmed.startsWith("//") ? `https:${trimmed}` : trimmed;
    }
    return `https://${trimmed}`;
  };

  const getCollatedReferralOptions = (): string => {
    const resourceTypeFiltersPrefix =
      "\nInclude resources that support the following categories: ";
    const resourceTypeFilters = selectedCategories
      .map((categoryId) => {
        const category = resourceCategories.find((c) => c.id === categoryId);
        return category?.label;
      })
      .filter(Boolean)
      .join(", ");

    const providerTypeFiltersPrefix =
      "\nInclude the following types of providers: ";
    const providerTypeFilters = selectedResourceTypes.join(", ");

    const locationFilterPrefix =
      "\nFocus on resources close to the following location: ";

    return (
      (resourceTypeFilters.length > 0
        ? resourceTypeFiltersPrefix + resourceTypeFilters
        : "") +
      (providerTypeFilters
        ? providerTypeFiltersPrefix + providerTypeFilters
        : "") +
      (locationText.length > 0 ? locationFilterPrefix + locationText : "")
    );
  };

  return (
    <>
      {/* ----- App chrome (hidden when printing) ----- */}
      <div className="print:hidden">
        <div className="flex flex-col gap-2 pl-24 pr-24 mt-8 mb-8">
          {!readyToPrint && (
            <>
              <Card className="bg-gray-50 border-gray-200">
                <CardContent className="p-4 space-y-4">
                  {/* Resource Categories */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600" />
                      Focus on Specific Resource Types
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                      {resourceCategories.map((category) => {
                        const Icon = category.icon;
                        const isSelected = selectedCategories.includes(
                          category.id,
                        );
                        return (
                          <Button
                            key={category.id}
                            variant={isSelected ? "default" : "outline"}
                            size="sm"
                            className={`text-sm flex-col justify-center px-1 min-h-20 w-auto whitespace-normal break-words h-auto ${
                              isSelected
                                ? "bg-blue-600 text-white hover:bg-blue-700"
                                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                            }`}
                            onClick={() => toggleCategory(category.id)}
                            data-testid={
                              "resourceCategoryToggle-" + category.id
                            }
                            aria-pressed={isSelected}
                            role="button"
                          >
                            <Icon className="mr-2 size-2.5 w-6 h-6" />
                            {category.label}
                          </Button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <Building className="w-4 h-4 text-blue-600" />
                      Resource Provider Types
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <Button
                        variant={
                          selectedResourceTypes.includes("goodwill")
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        className={`h-12 ${
                          selectedResourceTypes.includes("goodwill")
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                        }`}
                        onClick={() => toggleResourceType("goodwill")}
                        data-testid={"resourceCategoryToggle-goodwill"}
                        aria-pressed={selectedResourceTypes.includes(
                          "goodwill",
                        )}
                        role="button"
                      >
                        <Heart className="w-4 h-4 mr-2" />
                        Goodwill Internal
                      </Button>
                      <Button
                        variant={
                          selectedResourceTypes.includes("government")
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        className={`h-12 ${
                          selectedResourceTypes.includes("government")
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                        }`}
                        onClick={() => toggleResourceType("government")}
                        data-testid={"resourceCategoryToggle-government"}
                        aria-pressed={selectedResourceTypes.includes(
                          "government",
                        )}
                        role="button"
                      >
                        <Building className="w-4 h-4 mr-2" />
                        Government
                      </Button>
                      <Button
                        variant={
                          selectedResourceTypes.includes("community")
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        className={`h-12 ${
                          selectedResourceTypes.includes("community")
                            ? "bg-blue-600 text-white hover:bg-blue-700"
                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                        }`}
                        onClick={() => toggleResourceType("community")}
                        data-testid={"resourceCategoryToggle-community"}
                        aria-pressed={selectedResourceTypes.includes(
                          "community",
                        )}
                        role="button"
                      >
                        <Users className="w-4 h-4 mr-2" />
                        Community
                      </Button>
                    </div>
                  </div>

                  {/* Location Filters */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      Location Preferences
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-1 gap-3">
                      <Input
                        placeholder="Enter location (city, area, zip code, etc.)"
                        value={locationText}
                        onChange={(e) => setLocationText(e.target.value)}
                        className="border-gray-300 bg-white focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  {/* Clear All Button */}
                  {(selectedCategories.length > 0 ||
                    selectedResourceTypes.length > 0 ||
                    locationText) && (
                    <div className="flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearAllFilters}
                        className="text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                        data-testid="clearFiltersButton"
                      >
                        Clear All Filters
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
              <div className="mt-4 mb-2">
                <Label
                  className="font-medium text-gray-900 text-lg mb-2"
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
                className="min-w-[16rem] generate-referrals-button text-lg pt-6 pb-6"
                data-testid="findResourcesButton"
              >
                <Sparkles className="w-5 h-5" />
                {loading ? "Generating Resources..." : "Find Resources"}
              </Button>
            </>
          )}

          {readyToPrint && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pt-3">
                <Button
                  onClick={handleReturnToSearch}
                  variant="outline"
                  className="hover:bg-gray-100 hover:text-gray-900"
                  data-testid="returnToSearchButton"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Return To Search
                </Button>
                <Button
                  onClick={handlePrint}
                  variant="outline"
                  className="hover:bg-gray-100 hover:text-gray-900"
                >
                  <Printer
                    data-testid="printReferralsButton"
                    className="w-4 h-4"
                  />
                  Print Referrals
                </Button>
              </div>
            </div>
          )}

          {readyToPrint && result && result.length === 0 && (
            <div className="m-3">No resources found.</div>
          )}
          {readyToPrint && result && result.length > 0 && (
            <div className="mt-2">
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
