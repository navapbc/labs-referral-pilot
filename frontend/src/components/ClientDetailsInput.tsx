import React from "react";
import {
  Accessibility,
  Baby,
  Briefcase,
  Building,
  DollarSign,
  FileText,
  Flag,
  GraduationCap,
  Heart,
  Home,
  MapPin,
  Scale,
  Shield,
  Sparkles,
  Stethoscope,
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
                const isSelected = selectedCategories.includes(category.id);
                return (
                  <Button
                    key={category.id}
                    variant={isSelected ? "default" : "outline"}
                    size="sm"
                    className={`text-sm flex-col justify-center px-1 min-h-20 w-auto whitespace-normal break-words h-auto disabled:cursor-not-allowed ${
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
                className={`h-12 text-sm disabled:cursor-not-allowed ${
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
                Goodwill Internal
              </Button>
              <Button
                variant={
                  selectedResourceTypes.includes("government")
                    ? "default"
                    : "outline"
                }
                size="sm"
                className={`h-12 text-sm disabled:cursor-not-allowed ${
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
                className={`h-12 text-sm disabled:cursor-not-allowed ${
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
          </div>

          {/* Location Filters */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600" />
              Location Preferences
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-1 gap-3">
              <Input
                placeholder="Enter location (city, county, area, etc.)"
                value={locationText}
                onChange={(e) => onLocationChange(e.target.value)}
                className="border-gray-300 bg-white focus:ring-blue-500 focus:border-blue-500"
                data-testid="locationFilterInput"
                disabled={loading}
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
                onClick={onClearAllFilters}
                className="text-gray-700 hover:bg-gray-100 hover:text-gray-900 disabled:cursor-not-allowed"
                data-testid="clearFiltersButton"
                disabled={loading}
              >
                Clear All Filters
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      <div className="mt-4 mb-2" data-testid={"clientDescriptionInputSection"}>
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
          onChange={(e) => onClientDescriptionChange(e.target.value)}
          className="min-h-[8rem] min-w-[16rem] text-base"
          data-testid="clientDescriptionInput"
          disabled={loading}
        />
      </div>

      <Button
        type="button"
        onClick={onFindResources}
        disabled={
          loading ||
          (selectedCategories.length === 0 && !clientDescription.trim())
        }
        className="min-w-[16rem] w-full row-auto generate-referrals-button text-lg pt-6 pb-6 cursor-pointer disabled:!cursor-not-allowed"
        data-testid="findResourcesButton"
      >
        {!loading && (
          <>
            <Sparkles className="w-5 h-5" /> Find Resources
          </>
        )}
        {loading && (
          <>
            <Spinner className="w-5 h-5" />
            Generating Resources...
          </>
        )}
      </Button>
    </>
  );
}
