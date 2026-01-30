import { fetchLocationFromZip } from "./fetchLocation";
import { resourceCategories } from "@/components/ClientDetailsInput";

/**
 * Replaces zip codes in text with "city, state zip_code" format
 */
async function replaceZipCodes(text: string): Promise<string> {
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
      const zipRegex = new RegExp(`\\b${zipCode.replace(/-/g, "\\-")}\\b`, "g");
      result = result.replace(zipRegex, `${location} ${zipCode}`);
    }
  }

  return result;
}

export interface RequestParams {
  clientDescription: string;
  locationText: string;
  selectedCategories: string[];
  selectedResourceTypes: string[];
}

/**
 * Builds a request string with resolved zip codes and filters
 */
export async function buildRequestWithResolvedZipCodes(
  params: RequestParams,
): Promise<string> {
  const {
    clientDescription,
    locationText,
    selectedCategories,
    selectedResourceTypes,
  } = params;

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
}
