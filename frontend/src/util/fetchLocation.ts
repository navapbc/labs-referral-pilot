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

interface FCCCounty {
  FIPS: string;
  name: string;
}

interface FCCState {
  FIPS: string;
  code: string;
  name: string;
}

interface FCCResponse {
  status: string;
  County?: FCCCounty;
  State?: FCCState;
}

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

    if (!response.ok) {
      // Cache empty string for failed lookups
      zipCodeCache.set(zipCode, "");
      return "";
    }

    const data = (await response.json()) as ZippopotamResponse;
    const place = data.places?.[0];
    if (!place) {
      // Cache empty string if no place found
      zipCodeCache.set(zipCode, "");
      return "";
    }

    // Query FCC API via our server-side API route to avoid CORS issues
    try {
      const fccResponse = await fetch(
        `/api/fcc-lookup?latitude=${place.latitude}&longitude=${place.longitude}`,
        {
          signal: ac.signal,
        },
      );
      clearTimeout(timeoutId);

      if (!fccResponse.ok) {
        // Fall back to zippopotam data if FCC fails
        const result = `${place["place name"]}, ${place["state abbreviation"]}`;
        zipCodeCache.set(zipCode, result);
        return result;
      }

      const fccData = (await fccResponse.json()) as FCCResponse;

      // Use county name from FCC and state abbreviation
      if (fccData.County && fccData.State) {
        const result = `${place["place name"]} (${fccData.County.name} county), ${fccData.State.code}`;
        zipCodeCache.set(zipCode, result);
        return result;
      }

      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (fccError) {
      // If FCC API throws any error, fall back to zippopotam's city and state
      clearTimeout(timeoutId);
      const result = `${place["place name"]}, ${place["state abbreviation"]}`;
      zipCodeCache.set(zipCode, result);
      return result;
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      console.warn("Zip code lookup timed out:", zipCode);
    } else {
      console.warn("Error fetching city/state from zip code:", error);
    }
    // Cache empty string if errors (including timeouts)
    zipCodeCache.set(zipCode, "");
    return "";
  }
}
