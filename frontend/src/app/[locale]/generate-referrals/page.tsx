"use client";
import React, { useEffect, useState } from "react";
import { ChevronLeft, Printer, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

import { fetchResources } from "@/util/fetchResources";
import { Resource } from "@/types/resources";
import "@/app/globals.css";

import { PrintableReferralsReport } from "@/util/printReferrals";
import { fetchActionPlan, ActionPlan } from "@/util/fetchActionPlan";
import { ActionPlanSection } from "@/components/ActionPlanSection";

import ResourcesList from "@/components/ResourcesList";
import { useSearchParams } from "next/navigation";
import { UploadIntakeTab } from "@/components/UploadIntakeTab";
import { EmailReferralsButton } from "@/components/EmailReferralsButton";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload } from "lucide-react";
import WelcomeUserInputScreen from "@/components/WelcomeUserInputScreen";
import { PilotFeedbackBanner } from "@/components/PilotFeedbackBanner";
import { GoodwillReferralToolHeaderPilot } from "@/components/GoodwillReferralToolHeaderPilot";
import ClientDetailsPromptBubble from "@/components/ClientDetailsPromptBubble";
import {
  ClientDetailsInput,
  resourceCategories,
} from "@/components/ClientDetailsInput";

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
  const [errorMessage, setErrorMessage] = useState<string | undefined>(
    undefined,
  );

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
    setErrorMessage(undefined);
    try {
      const request = clientDescription + getCollatedReferralOptions();
      const { resultId, resources, errorMessage } = await fetchResources(
        request,
        userEmail,
        prompt_version_id,
      );
      setResultId(resultId);
      setErrorMessage(errorMessage);
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
    setErrorMessage(undefined);
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
    setErrorMessage(undefined);

    try {
      const { actionPlan: plan, errorMessage: planError } =
        await fetchActionPlan(selectedResources, userEmail);
      setActionPlan(plan);
      if (planError) {
        setErrorMessage(planError);
      }
    } catch (error) {
      console.error("Error generating action plan:", error);
      setErrorMessage(
        "The server encountered an unexpected error. Please try again later.",
      );
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
          <PilotFeedbackBanner />
          <GoodwillReferralToolHeaderPilot />
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
                  <ClientDetailsInput
                    selectedCategories={selectedCategories}
                    locationText={locationText}
                    selectedResourceTypes={selectedResourceTypes}
                    clientDescription={clientDescription}
                    loading={loading}
                    onToggleCategory={toggleCategory}
                    onClearAllFilters={clearAllFilters}
                    onToggleResourceType={toggleResourceType}
                    onLocationChange={setLocationText}
                    onClientDescriptionChange={setClientDescription}
                    onFindResources={() => void handleClick()}
                  />
                )}
              </TabsContent>

              <TabsContent value="upload-forms">
                {!readyToPrint && (
                  <UploadIntakeTab
                    userEmail={userEmail}
                    onResources={onResources}
                  />
                )}
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
                <ClientDetailsPromptBubble
                  clientDescription={clientDescription}
                />
                <ResourcesList
                  resources={result ?? []}
                  errorMessage={errorMessage}
                />
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
        <PrintableReferralsReport
          resources={result ?? []}
          clientDescription={clientDescription}
        />
      </div>
    </>
  );
}
