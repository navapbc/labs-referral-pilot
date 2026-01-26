import { Resource } from "@/types/resources";
import { extractField, extractArrayField } from "./parseStreamingUtils";

/**
 * Partial resource type for streaming - all fields are optional
 * but we only render resources that have at least a name
 */
export type PartialResource = Partial<Resource>;

/**
 * Parses streaming JSON to extract an array of partial resources
 * Handles incomplete JSON gracefully - captures partial objects and fields
 * Builds resources incrementally as data streams in
 */
export function parseStreamingResources(jsonStr: string): PartialResource[] {
  const resources: PartialResource[] = [];

  try {
    // Find the start of the resources array
    const resourcesKeyMatch = jsonStr.match(/"resources"\s*:\s*\[/);

    if (!resourcesKeyMatch) {
      return resources;
    }

    // Find the position right after the opening bracket
    const arrayStartPos =
      resourcesKeyMatch.index! + resourcesKeyMatch[0].length;

    // Manually find the matching closing bracket by tracking depth
    let bracketDepth = 1; // We're already inside the resources array
    let inString = false;
    let prevChar = "";
    let arrayEndPos = jsonStr.length; // Default to end of string for incomplete streams

    for (let i = arrayStartPos; i < jsonStr.length; i++) {
      const char = jsonStr[i];

      // Track string state to ignore brackets inside strings
      if (char === '"' && prevChar !== "\\") {
        inString = !inString;
      }

      if (!inString) {
        if (char === "[") {
          bracketDepth++;
        } else if (char === "]") {
          bracketDepth--;
          if (bracketDepth === 0) {
            // Found the matching closing bracket for the resources array
            arrayEndPos = i;
            break;
          }
        }
      }

      prevChar = char;
    }

    // Extract the array content (everything between the opening bracket and either
    // the closing bracket or the end of the string for incomplete streams)
    const arrayContent = jsonStr.substring(arrayStartPos, arrayEndPos);

    // Find all resource object boundaries by tracking brace depth
    // We want to identify each `{...}` at the top level of the array
    const resourceRanges: Array<{ start: number; end: number }> = [];
    let braceDepth = 0;
    inString = false; // Reset the string tracking flag
    prevChar = ""; // Reset the previous char tracker
    let resourceStart = -1;

    for (let i = 0; i < arrayContent.length; i++) {
      const char = arrayContent[i];

      // Track string state to ignore braces inside strings
      if (char === '"' && prevChar !== "\\") {
        inString = !inString;
      }

      if (!inString) {
        if (char === "{") {
          if (braceDepth === 0) {
            // Start of a new resource object
            resourceStart = i;
          }
          braceDepth++;
        } else if (char === "}") {
          braceDepth--;
          if (braceDepth === 0 && resourceStart !== -1) {
            // End of a resource object
            resourceRanges.push({ start: resourceStart, end: i + 1 });
            resourceStart = -1;
          }
        }
      }

      prevChar = char;
    }

    // If we have an incomplete resource (braceDepth > 0), include it
    if (resourceStart !== -1 && braceDepth > 0) {
      resourceRanges.push({ start: resourceStart, end: arrayContent.length });
    }

    // Parse each resource object (including incomplete ones)
    for (let i = 0; i < resourceRanges.length; i++) {
      const range = resourceRanges[i];
      const resourceStr = arrayContent.substring(range.start, range.end);
      const resource = parsePartialResource(resourceStr);

      // Only include resources that have a name (per user requirement)
      if (resource.name) {
        resources.push(resource);
      }
    }
  } catch (e) {
    console.error("Error parsing streaming resources:", e);
  }

  return resources;
}

/**
 * Parses a single partial resource object from JSON string
 */
function parsePartialResource(resourceStr: string): PartialResource {
  const resource: PartialResource = {};

  // Extract simple string fields
  const name = extractField(resourceStr, "name");
  if (name) resource.name = name;

  const description = extractField(resourceStr, "description");
  if (description) resource.description = description;

  const website = extractField(resourceStr, "website");
  if (website) resource.website = website;

  const referral_type = extractField(resourceStr, "referral_type");
  if (
    referral_type &&
    ["external", "goodwill", "government"].includes(referral_type)
  ) {
    resource.referral_type = referral_type as
      | "external"
      | "goodwill"
      | "government";
  }

  const justification = extractField(resourceStr, "justification");
  if (justification) resource.justification = justification;

  // Extract array fields
  const addresses = extractArrayField(resourceStr, "addresses");
  if (addresses.length > 0) {
    resource.addresses = addresses;
  }

  const phones = extractArrayField(resourceStr, "phones");
  if (phones.length > 0) {
    resource.phones = phones;
  }

  const emails = extractArrayField(resourceStr, "emails");
  if (emails.length > 0) {
    resource.emails = emails;
  }

  return resource;
}
