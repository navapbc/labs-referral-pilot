import { Resource, ResourcesSchema } from "@/types/resources";

const generateReferralsFromDocURL =
  process.env.ENVIRONMENT == "local"
    ? "http://0.0.0.0:3000/generate_referrals_from_doc/run"
    : "https://referral-pilot-dev.navateam.com/generate_referrals_from_doc/run";

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
    const resourcesJson = JSON.parse(
      responseData.result.llm.replies[0]._content[0].text,
    );
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
