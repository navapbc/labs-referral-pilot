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

export async function fetchLocationFromZip(
  zipCode: string,
  timeoutMs: number = 5000,
): Promise<string | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`https://api.zippopotam.us/us/${zipCode}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }
    const data = (await response.json()) as ZippopotamResponse;
    const place = data.places?.[0];
    if (place) {
      return `${place["place name"]}, ${place["state abbreviation"]}`;
    }
    return null;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      console.error("Zip code lookup timed out:", zipCode);
    } else {
      console.error("Error fetching city/state from zip code:", error);
    }
    return null;
  }
}
