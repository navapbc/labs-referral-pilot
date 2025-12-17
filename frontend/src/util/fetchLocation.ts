import { LRUCache } from "lru-cache";

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

// Cache for storing zip code lookup results (max 100 entries)
const zipCodeCache = new LRUCache<string, string>({
  max: 100,
});

export async function fetchLocationFromZip(zipCode: string): Promise<string> {
  // Check cache first
  const cachedValue = zipCodeCache.get(zipCode);
  if (cachedValue !== undefined) {
    return cachedValue;
  }

  const ac = new AbortController();
  const timeoutId = setTimeout(() => ac.abort(), 5_000);

  try {
    const response = await fetch(`https://api.zippopotam.us/us/${zipCode}`, {
      signal: ac.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      // Cache empty string for failed lookups
      zipCodeCache.set(zipCode, "");
      return "";
    }

    const data = (await response.json()) as ZippopotamResponse;
    const place = data.places?.[0];
    if (place) {
      const result = `${place["place name"]}, ${place["state abbreviation"]}`;
      // Cache successful result
      zipCodeCache.set(zipCode, result);
      return result;
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      console.error("Zip code lookup timed out:", zipCode);
    } else {
      console.error("Error fetching city/state from zip code:", error);
    }
  }

  // Cache empty string if no place found or errors (including timeouts)
  zipCodeCache.set(zipCode, "");
  return "";
}
