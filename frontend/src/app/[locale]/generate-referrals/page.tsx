"use client";
import React, { useEffect, useState } from "react";
import { ChevronLeft, Printer, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

import { fetchResources } from "@/util/fetchResources";
import { Resource } from "@/types/resources";
import "@/app/globals.css";
import { fetchLocationFromZip } from "@/util/fetchLocation";

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
import { RemoveResourceNotification } from "@/components/RemoveResourceNotification";

export default function Page() {
  const [clientDescription, setClientDescription] = useState("");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [result, setResult] = useState<Resource[] | null>(null);
  const [resourcesResultId, setResourcesResultId] = useState("");
  const [actionPlanResultId, setActionPlanResultId] = useState("");
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
  const [requestAfterZipResolution, setRequestAfterZipResolution] =
    useState("");

  const searchParams = useSearchParams();

  // User info state
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isCheckingUser, setIsCheckingUser] = useState(true);

  // Remove functionality state
  const [retainedResources, setRetainedResources] = useState<Resource[]>();
  const [recentlyRemoved, setRecentlyRemoved] = useState<Resource | null>(null);
  const [removedResourceIndex, setRemovedResourceIndex] = useState<
    number | null
  >(null);

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
    setRetainedResources(resources); // this creates a copy of the original list of resources, may be edited by the user
    setReadyToPrint(true);
  };

  async function findResources() {
    const suffix = searchParams?.get("suffix") ?? undefined;

    setLoading(true);
    setResult(null);
    setErrorMessage(undefined);
    try {
      const request = await buildRequestWithResolvedZipCodes();
      setRequestAfterZipResolution(request);
      const { resultId, resources, errorMessage } = await fetchResources(
        request,
        userEmail,
        suffix,
      );
      setResourcesResultId(resultId);
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
    setResourcesResultId("");
    setActionPlanResultId("");
    setLocationText("");
    setSelectedCategories([]);
    setSelectedResourceTypes([]);
    setClientDescription("");
    setSelectedResources([]);
    setActionPlan(null);
    setErrorMessage(undefined);
    setRequestAfterZipResolution("");
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
    if (!retainedResources) return;
    if (selectedResources.length === retainedResources.length) {
      setSelectedResources([]);
    } else {
      setSelectedResources(retainedResources);
    }
  }

  async function generateActionPlan() {
    if (selectedResources.length === 0) return;

    const suffix = searchParams?.get("suffix") ?? undefined;

    setIsGeneratingActionPlan(true);
    setActionPlan(null);
    setErrorMessage(undefined);

    try {
      const {
        actionPlan: plan,
        resultId,
        errorMessage: planError,
      } = await fetchActionPlan(
        selectedResources,
        userEmail,
        clientDescription,
        suffix,
      );
      setActionPlan(plan);
      setActionPlanResultId(resultId);
      if (planError) {
        setErrorMessage(planError);
        setActionPlanResultId(""); // set the Action PLan Id to "" so we don't email an empty or errant result
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

  const buildRequestWithResolvedZipCodes = async (): Promise<string> => {
    // Helper function to replace zip codes with "city, state zip_code" format
    const replaceZipCodes = async (text: string): Promise<string> => {
      if (!text) return text;

      const zipCodeRegex = /\b\d{5}(?:-\d{4})?\b/g;
      const matches = Array.from(text.matchAll(zipCodeRegex));

      if (matches.length === 0) return text;

      // Collect unique zip codes to avoid duplicate API calls
      const uniqueZipCodes = Array.from(new Set(matches.map((m) => m[0])));

      // Fetch locations for all unique zip codes
      const zipToLocation = new Map<string, string>();
      const locationPromises = uniqueZipCodes.map(async (zipCode) => {
        // For zip+4 format, only use the 5-digit part for lookup
        const zipForLookup = zipCode.split("-")[0];
        const location = await fetchLocationFromZip(zipForLookup);
        zipToLocation.set(zipCode, location);
      });
      await Promise.all(locationPromises);

      // Replace all zip codes with their city, state prepended
      let result = text;
      for (const [zipCode, location] of zipToLocation.entries()) {
        if (location) {
          // Use a global replace to handle all occurrences of this zip code
          const zipRegex = new RegExp(
            `\\b${zipCode.replace(/-/g, "\\-")}\\b`,
            "g",
          );
          result = result.replace(zipRegex, `${location} ${zipCode}`);
        }
      }

      return result;
    };

    // Process both locationText and clientDescription for zip codes
    const processedLocationText = await replaceZipCodes(locationText);
    const processedClientDescription = await replaceZipCodes(clientDescription);

    const resourceTypeFilters = selectedCategories
      .map((categoryId) => {
        const category = resourceCategories.find((c) => c.id === categoryId);
        return category?.label;
      })
      .filter(Boolean)
      .join(", ");

    const options =
      (resourceTypeFilters.length > 0
        ? "\nInclude resources that support the following categories: " +
          resourceTypeFilters
        : "") +
      (selectedResourceTypes.length > 0
        ? "\nInclude the following types of providers: " +
          selectedResourceTypes.join(", ")
        : "") +
      (processedLocationText.length > 0
        ? "\nFocus on resources close to the following location: " +
          processedLocationText
        : "");

    return processedClientDescription + options;
  };

  // Show nothing while checking localStorage to prevent flash
  if (isCheckingUser) {
    return null;
  }

  // Remove resource handler
  const handleRemoveResource = (resourceToRemove: Resource) => {
    // Find and store the index before removing
    const index = retainedResources?.findIndex(
      (r) => r.name === resourceToRemove.name,
    );
    if (index !== undefined && index !== -1) {
      setRemovedResourceIndex(index);
    }

    setRecentlyRemoved(resourceToRemove);

    // Immediately remove from retainedResources
    setRetainedResources((current) =>
      current?.filter((r) => r.name !== resourceToRemove.name),
    );

    // Remove from selectedResources as well
    setSelectedResources((current) =>
      current.filter((r) => r.name !== resourceToRemove.name),
    );

    // Auto-clear the undo notification after 7.5 seconds
    setTimeout(() => {
      setRecentlyRemoved((current) => {
        // If the resource is still marked as recently removed, clear it
        if (current === resourceToRemove) {
          return null;
        }
        return current;
      });
      setRemovedResourceIndex(null);
    }, 7500);
  };

  // Undo remove handler
  const handleUndoRemove = () => {
    if (recentlyRemoved) {
      // Add the resource back to retainedResources at its original index
      setRetainedResources((current) => {
        if (!current) {
          return [recentlyRemoved];
        }

        // If we have a stored index, insert at that position
        if (removedResourceIndex !== null && removedResourceIndex >= 0) {
          const newArray = [...current];
          newArray.splice(removedResourceIndex, 0, recentlyRemoved);
          return newArray;
        }

        // Fallback: append to the end
        return [...current, recentlyRemoved];
      });

      // Clear the recently removed state
      setRecentlyRemoved(null);
      setRemovedResourceIndex(null);
    }
  };

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
                    onFindResources={() => void findResources()}
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
                    {resourcesResultId && (
                      <EmailReferralsButton
                        resultId={resourcesResultId}
                        actionPlanResultId={actionPlanResultId || undefined}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}

            {requestAfterZipResolution && (
              <ClientDetailsPromptBubble
                clientDescription={requestAfterZipResolution}
              />
            )}

            {readyToPrint && (
              <ResourcesList
                resources={retainedResources ?? []}
                errorMessage={errorMessage}
                handleRemoveResource={handleRemoveResource}
              />
            )}

            {readyToPrint &&
              retainedResources &&
              retainedResources.length > 0 && (
                <ActionPlanSection
                  resources={retainedResources}
                  selectedResources={selectedResources}
                  actionPlan={actionPlan}
                  isGeneratingActionPlan={isGeneratingActionPlan}
                  onResourceSelection={handleResourceSelection}
                  onSelectAllResources={handleSelectAllResources}
                  onGenerateActionPlan={() => void generateActionPlan()}
                />
              )}
          </div>
        </div>
      )}

      {recentlyRemoved && (
        <RemoveResourceNotification handleUndoRemove={handleUndoRemove} />
      )}

      {/* ----- Print-only section ----- */}
      <div className="hidden print:block">
        <PrintableReferralsReport
          resources={retainedResources ?? []}
          clientDescription={clientDescription}
          actionPlan={actionPlan}
        />
      </div>
    </>
  );
}
