"use client";
import React, { useEffect, useState } from "react";
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
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

import { fetchResources } from "@/util/fetchResources";
import { Resource } from "@/types/resources";
import "@/app/globals.css";

import { PrintableReferralsReport } from "@/util/printReferrals";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { fetchActionPlan, ActionPlan } from "@/util/fetchActionPlan";
import { ActionPlanSection } from "@/components/ActionPlanSection";

import ResourcesList from "@/components/ResourcesList";
import { useSearchParams } from "next/navigation";
import { UploadIntakeTab } from "@/components/UploadIntakeTab";
import { EmailReferralsButton } from "@/components/EmailReferralsButton";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload } from "lucide-react";
import WelcomeUserInputScreen from "@/components/WelcomeUserInputScreen";

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
  const [resultId, setResultId] = useState("");
  const [loading, setLoading] = useState(false);
  const [readyToPrint, setReadyToPrint] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [locationText, setLocationText] = useState("");
  const [selectedResourceTypes, setSelectedResourceTypes] = useState<string[]>(
    [],
  );
  const [selectedResources, setSelectedResources] = useState<Resource[]>([]);
  const [actionPlan, setActionPlan] = useState<ActionPlan | null>(null);
  const [isGeneratingActionPlan, setIsGeneratingActionPlan] = useState(false);
  const [activeTab, setActiveTab] = useState("find-referrals");

  const searchParams = useSearchParams();

  // User info state
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isCheckingUser, setIsCheckingUser] = useState(true);

  // Check if user has provided info on first load
  useEffect(() => {
    const storedUserName = localStorage.getItem("userName");
    const storedUserEmail = localStorage.getItem("userEmail");

    if (storedUserName && storedUserEmail) {
      setUserName(storedUserName);
      setUserEmail(storedUserEmail);
    }
    setIsCheckingUser(false);
  }, []);

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

  const onResources = (resources: Resource[]) => {
    setResult(resources);
    setReadyToPrint(true);
  };

  async function handleClick() {
    const prompt_version_id = searchParams?.get("prompt_version_id") ?? null;

    setLoading(true);
    setResult(null);
    try {
      const request = clientDescription + getCollatedReferralOptions();
      const { resultId, resources } = await fetchResources(
        request,
        userEmail,
        prompt_version_id,
      );
      setResultId(resultId);
      onResources(resources);
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
    setResult([]);
    setResultId("");
    setLocationText("");
    setSelectedCategories([]);
    setSelectedResourceTypes([]);
    setClientDescription("");
    setSelectedResources([]);
    setActionPlan(null);
  }

  function handleResourceSelection(resource: Resource, checked: boolean) {
    if (checked) {
      setSelectedResources((prev) => [...prev, resource]);
    } else {
      setSelectedResources((prev) =>
        prev.filter((r) => r.name !== resource.name),
      );
    }
  }

  function handleSelectAllResources() {
    if (!result) return;
    if (selectedResources.length === result.length) {
      setSelectedResources([]);
    } else {
      setSelectedResources(result);
    }
  }

  async function generateActionPlan() {
    if (selectedResources.length === 0) return;

    setIsGeneratingActionPlan(true);
    setActionPlan(null);

    try {
      const plan = await fetchActionPlan(selectedResources, userEmail);
      setActionPlan(plan);
    } catch (error) {
      console.error("Error generating action plan:", error);
    } finally {
      setIsGeneratingActionPlan(false);
    }
  }

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

  // Show nothing while checking localStorage to prevent flash
  if (isCheckingUser) {
    return null;
  }

  return (
    <>
      {!userName || !userEmail ? (
        <WelcomeUserInputScreen
          setUserName={setUserName}
          setUserEmail={setUserEmail}
        />
      ) : (
        <div className="print:hidden">
          <div className="flex flex-col gap-2 m-4">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="mb-6"
            >
              {!readyToPrint && (
                <TabsList className="grid w-full grid-cols-2 bg-gray-100">
                  <TabsTrigger
                    value="find-referrals"
                    className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-blue-600"
                  >
                    <Sparkles className="w-4 h-4" />
                    Find Referrals
                  </TabsTrigger>
                  <TabsTrigger
                    value="upload-forms"
                    className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-blue-600"
                  >
                    <Upload className="w-4 h-4" />
                    Upload Intake Form
                  </TabsTrigger>
                </TabsList>
              )}

              <TabsContent value="find-referrals">
                {!readyToPrint && (
                  // TODO: Move the following tab content into a separate component
                  <>
                    <Card
                      className="bg-gray-50 border-gray-200"
                      data-testid="referralFiltersSection"
                    >
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
                              className={`h-12 text-sm ${
                                selectedResourceTypes.includes("goodwill")
                                  ? "bg-blue-600 text-white hover:bg-blue-700"
                                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                              }`}
                              onClick={() => toggleResourceType("goodwill")}
                              data-testid={"resourceCategoryToggle-goodwill"}
                              aria-pressed={selectedResourceTypes.includes(
                                "goodwill",
                              )}
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
                              className={`h-12 text-sm ${
                                selectedResourceTypes.includes("government")
                                  ? "bg-blue-600 text-white hover:bg-blue-700"
                                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                              }`}
                              onClick={() => toggleResourceType("government")}
                              data-testid={"resourceCategoryToggle-government"}
                              aria-pressed={selectedResourceTypes.includes(
                                "government",
                              )}
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
                              className={`h-12 text-sm ${
                                selectedResourceTypes.includes("community")
                                  ? "bg-blue-600 text-white hover:bg-blue-700"
                                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                              }`}
                              onClick={() => toggleResourceType("community")}
                              data-testid={"resourceCategoryToggle-community"}
                              aria-pressed={selectedResourceTypes.includes(
                                "community",
                              )}
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
                              data-testid="locationFilterInput"
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
                    <div
                      className="mt-4 mb-2"
                      data-testid={"clientDescriptionInputSection"}
                    >
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
                      {!loading && (
                        <>
                          <Sparkles className="w-5 h-5" /> Find Resources
                        </>
                      )}
                      {loading && (
                        <>
                          <Spinner className="" />
                          Generating Resources...
                        </>
                      )}
                    </Button>
                  </>
                )}
              </TabsContent>

              <TabsContent value="upload-forms">
                {!readyToPrint && <UploadIntakeTab onResources={onResources} />}
              </TabsContent>
            </Tabs>

            {readyToPrint && (
              <div className="space-y-4" data-testid="readyToPrintSection">
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
                  <div className="flex gap-2">
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
                    {resultId && <EmailReferralsButton resultId={resultId} />}
                  </div>
                </div>
                <ResourcesList resources={result ?? []} />
                {result && result.length > 0 && (
                  <ActionPlanSection
                    resources={result}
                    selectedResources={selectedResources}
                    actionPlan={actionPlan}
                    isGeneratingActionPlan={isGeneratingActionPlan}
                    onResourceSelection={handleResourceSelection}
                    onSelectAllResources={handleSelectAllResources}
                    onGenerateActionPlan={() => void generateActionPlan()}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ----- Print-only section ----- */}
      <div className="hidden print:block">
        <PrintableReferralsReport resources={result ?? []} />
      </div>
    </>
  );
}
