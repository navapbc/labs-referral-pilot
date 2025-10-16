import { Resource, ResourcesSchema } from "@/types/resources";

const generateReferralsFromDocURL =
  process.env.ENVIRONMENT == "local"
    ? "http://0.0.0.0:3000/generate_referrals_from_doc/run"
    : "https://referral-pilot-dev.navateam.com/generate_referrals_from_doc/run";

/**
 * Extracts JSON from text that may contain a prefix or suffix
 * Finds the first { and matching } to extract the JSON object
 */
function extractJSON(text: string): string {
  const firstBrace = text.indexOf("{");
  if (firstBrace === -1) {
    throw new Error("No JSON object found in response");
  }

  // Find the matching closing brace by counting braces
  let braceCount = 0;
  let endIndex = firstBrace;

  for (let i = firstBrace; i < text.length; i++) {
    if (text[i] === "{") {
      braceCount++;
    } else if (text[i] === "}") {
      braceCount--;
      if (braceCount === 0) {
        endIndex = i;
        break;
      }
    }
  }

  if (braceCount !== 0) {
    throw new Error("Malformed JSON in response");
  }

  return text.substring(firstBrace, endIndex + 1);
}

export async function uploadPdfDocument(file: File): Promise<Resource[]> {
  const url = generateReferralsFromDocURL;

  const formData = new FormData();
  formData.append("files", file);

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 60_000); // 60 seconds timeout for file upload

  try {
    const upstream = await fetch(url, {
      method: "POST",
      body: formData,
      cache: "no-store",
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!upstream.ok) {
      throw new Error(`HTTP error! status: ${upstream.status}`);
    }

    /* eslint-disable */
    const responseData = await upstream.json();
    const responseText = responseData.result.llm.replies[0]._content[0].text;
    console.log("Response text:", responseText);
    const jsonString = extractJSON(responseText);
    const resourcesJson = JSON.parse(jsonString);
    console.log("Parsed resources JSON:", resourcesJson);
    const resources = ResourcesSchema.parse(resourcesJson);
    const resourcesAsArray: Resource[] = resources.resources;
    /* eslint-enable */

    return resourcesAsArray;
  } catch (error) {
    console.error("Error uploading PDF:", error);
    throw error;
  }
}
