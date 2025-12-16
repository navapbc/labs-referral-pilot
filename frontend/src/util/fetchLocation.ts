interface ZippopotamPlace {
  "place name": string; // city name
  state: string;
  "state abbreviation": string;
  longitude: string;
  latitude: string;
}

interface ZippopotamResponse {
  places?: ZippopotamPlace[];
}

// Cache for storing zip code lookup results
const zipCodeCache = new Map<string, string | null>();

export async function fetchLocationFromZip(
  zipCode: string,
  timeoutMs: number = 5000,
): Promise<string | null> {
  // Check cache first
  if (zipCodeCache.has(zipCode)) {
    return zipCodeCache.get(zipCode) ?? null;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`https://api.zippopotam.us/us/${zipCode}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      // Cache null result for failed lookups
      zipCodeCache.set(zipCode, null);
      return null;
    }

    const data = (await response.json()) as ZippopotamResponse;
    const place = data.places?.[0];
    if (place) {
      const result = `${place["place name"]}, ${place["state abbreviation"]}`;
      // Cache successful result
      zipCodeCache.set(zipCode, result);
      return result;
    }

    // Cache null if no place found
    zipCodeCache.set(zipCode, null);
    return null;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      console.error("Zip code lookup timed out:", zipCode);
    } else {
      console.error("Error fetching city/state from zip code:", error);
    }
    // Cache null result for errors (including timeouts)
    zipCodeCache.set(zipCode, null);
    return null;
  }
}
