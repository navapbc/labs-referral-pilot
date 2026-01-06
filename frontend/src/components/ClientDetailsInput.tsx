import React from "react";
import {
  Accessibility,
  Baby,
  Briefcase,
  Building,
  DollarSign,
  Flag,
  GraduationCap,
  HandHelping,
  Heart,
  Home,
  Layers,
  MapPin,
  RotateCcw,
  Scale,
  Search,
  Shield,
  Sparkles,
  Stethoscope,
  UserRound,
  Users,
  Utensils,
  Car,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";

export const resourceCategories = [
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

interface ClientDetailsInputProps {
  selectedCategories: string[];
  locationText: string;
  selectedResourceTypes: string[];
  clientDescription: string;
  loading: boolean;
  onToggleCategory: (categoryId: string) => void;
  onClearAllFilters: () => void;
  onToggleResourceType: (type: string) => void;
  onLocationChange: (location: string) => void;
  onClientDescriptionChange: (description: string) => void;
  onFindResources: () => void;
}

export function ClientDetailsInput({
  selectedCategories,
  locationText,
  selectedResourceTypes,
  clientDescription,
  loading,
  onToggleCategory,
  onClearAllFilters,
  onToggleResourceType,
  onLocationChange,
  onClientDescriptionChange,
  onFindResources,
}: ClientDetailsInputProps) {
  return (
    <div className="flex flex-col gap-4 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex flex-col items-center text-center py-6">
        <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
          <HandHelping className="w-8 h-8 text-purple-600" />
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
          Let's Find the Right Resources for Your Clients
        </h1>
        <p className="text-gray-600 max-w-xl">
          Share some details about your client's situation, and we'll help you
          discover the perfect resources and referrals tailored to their
          specific needs.
        </p>
      </div>

      {/* Tell us about your client */}
      <Card
        className="bg-gray-50 border-gray-200"
        data-testid="clientDescriptionInputSection"
      >
        <CardContent className="p-4">
          <label
            htmlFor="clientDescriptionInput"
            className="font-medium text-gray-900 mb-3 flex items-center gap-2"
          >
            <UserRound className="w-4 h-4 text-blue-600" />
            Tell us about your client
          </label>
          <Textarea
            placeholder="Example: My client is looking for medical assistant training, diapers and clothes for job interviews."
            id="clientDescriptionInput"
            value={clientDescription}
            onChange={(e) => onClientDescriptionChange(e.target.value)}
            className="min-h-[8rem] min-w-[16rem] text-base bg-white mt-2"
            data-testid="clientDescriptionInput"
            disabled={loading}
          />
        </CardContent>
      </Card>

      {/* Location */}
      <Card
        className="bg-gray-50 border-gray-200"
        data-testid="locationFilterSection"
      >
        <CardContent className="p-4">
          <h4 className="font-medium text-gray-900 mb-1 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            Location
          </h4>
          <p className="text-sm text-gray-500 mb-3">
            Optional - helps find resources near your client
          </p>
          <Input
            placeholder="Enter zip code, city name, or neighborhood..."
            value={locationText}
            onChange={(e) => onLocationChange(e.target.value)}
            className="border-gray-300 bg-white focus:ring-blue-500 focus:border-blue-500"
            data-testid="locationFilterInput"
            disabled={loading}
            aria-label="Location"
          />
        </CardContent>
      </Card>

      {/* Resource Categories */}
      <Card
        className="bg-gray-50 border-gray-200"
        data-testid="referralFiltersSection"
      >
        <CardContent className="p-4">
          <h4 className="font-medium text-gray-900 mb-1 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            Resource Categories
          </h4>
          <p className="text-sm text-gray-500 mb-3">
            Optional - select categories to narrow your search
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {resourceCategories.map((category) => {
              const Icon = category.icon;
              const isSelected = selectedCategories.includes(category.id);
              return (
                <Button
                  key={category.id}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  className={`text-sm flex-col justify-center px-1 min-h-20 w-auto whitespace-normal break-words h-auto cursor-pointer disabled:cursor-not-allowed ${
                    isSelected
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                  onClick={() => onToggleCategory(category.id)}
                  data-testid={"resourceCategoryToggle-" + category.id}
                  aria-pressed={isSelected}
                  disabled={loading}
                >
                  <Icon className="mr-2 w-6 h-6" />
                  {category.label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Resource Provider Selection */}
      <Card
        className="bg-gray-50 border-gray-200"
        data-testid="resourceProviderSection"
      >
        <CardContent className="p-4">
          <h4 className="font-medium text-gray-900 mb-1 flex items-center gap-2">
            <Search className="w-4 h-4 text-blue-600" />
            Resource Provider Selection
          </h4>
          <p className="text-sm text-gray-500 mb-3">
            Select up to 3 provider types, or leave empty to search all
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Button
              variant={
                selectedResourceTypes.includes("goodwill")
                  ? "default"
                  : "outline"
              }
              size="sm"
              className={`h-12 text-sm cursor-pointer disabled:cursor-not-allowed ${
                selectedResourceTypes.includes("goodwill")
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
              onClick={() => onToggleResourceType("goodwill")}
              data-testid={"resourceCategoryToggle-goodwill"}
              aria-pressed={selectedResourceTypes.includes("goodwill")}
              disabled={loading}
            >
              <Heart className="w-4 h-4 mr-2" />
              Goodwill
            </Button>
            <Button
              variant={
                selectedResourceTypes.includes("government")
                  ? "default"
                  : "outline"
              }
              size="sm"
              className={`h-12 text-sm cursor-pointer disabled:cursor-not-allowed ${
                selectedResourceTypes.includes("government")
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
              onClick={() => onToggleResourceType("government")}
              data-testid={"resourceCategoryToggle-government"}
              aria-pressed={selectedResourceTypes.includes("government")}
              disabled={loading}
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
              className={`h-12 text-sm cursor-pointer disabled:cursor-not-allowed ${
                selectedResourceTypes.includes("community")
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
              onClick={() => onToggleResourceType("community")}
              data-testid={"resourceCategoryToggle-community"}
              aria-pressed={selectedResourceTypes.includes("community")}
              disabled={loading}
            >
              <Users className="w-4 h-4 mr-2" />
              Community
            </Button>
          </div>

        </CardContent>
      </Card>

      {/* Clear All Button - outside cards since it clears all filters */}
      {(selectedCategories.length > 0 ||
        selectedResourceTypes.length > 0 ||
        locationText) && (
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={onClearAllFilters}
            className="text-gray-600 border-gray-300 hover:bg-gray-100 hover:text-gray-900 hover:border-gray-400 cursor-pointer disabled:cursor-not-allowed"
            data-testid="clearFiltersButton"
            disabled={loading}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Clear All Filters
          </Button>
        </div>
      )}

      {/* Spacer to account for fixed button at bottom */}
      <div className="h-20" />

      {/* Fixed floating button at bottom of viewport */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 shadow-lg z-50">
        <Button
          type="button"
          onClick={onFindResources}
          disabled={
            loading ||
            (selectedCategories.length === 0 && !clientDescription.trim())
          }
          className="min-w-[16rem] w-full max-w-3xl mx-auto generate-referrals-button text-lg pt-6 pb-6 cursor-pointer disabled:!cursor-not-allowed"
          data-testid="findResourcesButton"
        >
          {!loading && (
            <>
              <Sparkles className="w-5 h-5" /> Find Referrals
            </>
          )}
          {loading && (
            <>
              <Spinner className="w-5 h-5" />
              Finding Resources...
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
