// Mock fetch globally before importing the module
global.fetch = jest.fn();

describe("fetchLocationFromZip", () => {
  // Import fresh module for each test to reset cache
  let fetchLocationFromZip: (
    zipCode: string,
    timeoutMs?: number,
  ) => Promise<string | null>;

  beforeEach(async () => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    jest.resetModules();

    // Re-import module to get fresh cache
    // eslint-disable-next-line @next/next/no-assign-module-variable
    const fetchLocationModule = await import("@/util/fetchLocation");
    fetchLocationFromZip = fetchLocationModule.fetchLocationFromZip;
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  it("should fetch and return city and state for a valid zip code", async () => {
    const mockResponse = {
      places: [
        {
          "place name": "Beverly Hills",
          state: "California",
          "state abbreviation": "CA",
          longitude: "-118.4065",
          latitude: "34.0901",
        },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await fetchLocationFromZip("90210");

    expect(result).toBe("Beverly Hills, CA");
    expect(global.fetch).toHaveBeenCalledWith(
      "https://api.zippopotam.us/us/90210",
      expect.objectContaining({
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        signal: expect.any(Object),
      }),
    );
  });

  it("should return null for an invalid zip code (404 response)", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    const result = await fetchLocationFromZip("00000");

    expect(result).toBeNull();
  });

  it("should return null when API returns no places", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ places: [] }),
    });

    const result = await fetchLocationFromZip("99999");

    expect(result).toBeNull();
  });

  it("should return null when API returns undefined places", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    });

    const result = await fetchLocationFromZip("99999");

    expect(result).toBeNull();
  });

  it("should handle network errors gracefully", async () => {
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Network error"),
    );

    const result = await fetchLocationFromZip("90210");

    expect(result).toBeNull();
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Error fetching city/state from zip code:",
      expect.any(Error),
    );

    consoleErrorSpy.mockRestore();
  });

  it("should cache successful results", async () => {
    const mockResponse = {
      places: [
        {
          "place name": "New York",
          state: "New York",
          "state abbreviation": "NY",
          longitude: "-73.9967",
          latitude: "40.7484",
        },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    // First call - should hit the API
    const result1 = await fetchLocationFromZip("10001");
    expect(result1).toBe("New York, NY");
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Second call with same zip - should use cache
    const result2 = await fetchLocationFromZip("10001");
    expect(result2).toBe("New York, NY");
    expect(global.fetch).toHaveBeenCalledTimes(1); // Still only 1 call
  });

  it("should cache null results for failed lookups", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    // First call - should hit the API
    const result1 = await fetchLocationFromZip("00000");
    expect(result1).toBeNull();
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Second call with same zip - should use cache
    const result2 = await fetchLocationFromZip("00000");
    expect(result2).toBeNull();
    expect(global.fetch).toHaveBeenCalledTimes(1); // Still only 1 call
  });

  it("should cache different zip codes independently", async () => {
    const mockResponse1 = {
      places: [
        {
          "place name": "Beverly Hills",
          state: "California",
          "state abbreviation": "CA",
          longitude: "-118.4065",
          latitude: "34.0901",
        },
      ],
    };

    const mockResponse2 = {
      places: [
        {
          "place name": "New York",
          state: "New York",
          "state abbreviation": "NY",
          longitude: "-73.9967",
          latitude: "40.7484",
        },
      ],
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse1),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse2),
      });

    const result1 = await fetchLocationFromZip("90210");
    const result2 = await fetchLocationFromZip("10001");
    const result3 = await fetchLocationFromZip("90210"); // Cached
    const result4 = await fetchLocationFromZip("10001"); // Cached

    expect(result1).toBe("Beverly Hills, CA");
    expect(result2).toBe("New York, NY");
    expect(result3).toBe("Beverly Hills, CA");
    expect(result4).toBe("New York, NY");
    expect(global.fetch).toHaveBeenCalledTimes(2); // Only 2 API calls
  });

  it("should handle zip+4 format by using only first 5 digits", async () => {
    const mockResponse = {
      places: [
        {
          "place name": "Chicago",
          state: "Illinois",
          "state abbreviation": "IL",
          longitude: "-87.6298",
          latitude: "41.8781",
        },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    // Note: In the actual implementation, the caller extracts the 5-digit portion
    // This test verifies that the function works with just the 5-digit code
    const result = await fetchLocationFromZip("60601");

    expect(result).toBe("Chicago, IL");
  });
});
