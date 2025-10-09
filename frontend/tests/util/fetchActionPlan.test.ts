import { fetchActionPlan } from "src/util/fetchActionPlan";
import { Resource } from "src/types/resources";

// Mock fetch globally
global.fetch = jest.fn();

describe("fetchActionPlan", () => {
  const mockResources: Resource[] = [
    {
      name: "Test Resource",
      description: "Test description",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns action plan when API call succeeds", async () => {
    const mockActionPlan = {
      title: "Test Action Plan",
      summary: "Test summary",
      content: "## Test Content\n\nSome content here",
    };

    const mockResponse = {
      result: {
        llm: {
          replies: [
            {
              _content: [
                {
                  text: JSON.stringify(mockActionPlan),
                },
              ],
            },
          ],
        },
      },
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await fetchActionPlan(mockResources);

    expect(result).toEqual(mockActionPlan);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ resources: mockResources }),
      })
    );
  });

  it("handles JSON with unescaped newlines", async () => {
    const mockActionPlan = {
      title: "Test",
      summary: "Summary",
      content: "Line 1\nLine 2",
    };

    // Simulate LLM returning JSON with literal newlines in the content
    const brokenJson = `{
  "title": "Test",
  "summary": "Summary",
  "content": "Line 1
Line 2"
}`;

    const mockResponse = {
      result: {
        llm: {
          replies: [
            {
              _content: [
                {
                  text: brokenJson,
                },
              ],
            },
          ],
        },
      },
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await fetchActionPlan(mockResources);

    expect(result).toEqual(mockActionPlan);
  });

  it("returns null when API call fails", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      statusText: "Internal Server Error",
    });

    const result = await fetchActionPlan(mockResources);

    expect(result).toBeNull();
  });

  it("returns null when fetch throws an error", async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

    const result = await fetchActionPlan(mockResources);

    expect(result).toBeNull();
  });
});
