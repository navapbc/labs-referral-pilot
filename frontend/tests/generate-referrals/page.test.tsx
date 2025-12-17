import { render, screen, waitFor } from "tests/react-utils";
import userEvent from "@testing-library/user-event";
import Page from "src/app/[locale]/generate-referrals/page";
import * as fetchResourcesModule from "src/util/fetchResources";
import { Resource } from "src/types/resources";

// Mock the modules
jest.mock("src/util/fetchResources");
jest.mock("src/util/fetchActionPlan");
jest.mock("src/util/fetchLocation", () => ({
  fetchLocationFromZip: jest.fn(() => Promise.resolve(null)),
}));

// Mock only the markdown parser to avoid ESM module issues
jest.mock("src/util/markdown", () => ({
  parseMarkdownToHTML: jest.fn((content: string) => `<div>${content}</div>`),
}));

describe("Generate Referrals Page", () => {
  const mockResources: Resource[] = [
    {
      name: "Test Resource",
      addresses: ["123 Test St"],
      phones: ["555-1234"],
      emails: ["test@example.com"],
      website: "https://example.com",
      description: "Test description",
      justification: "Test justification",
    },
  ];
  const mockFetchResourcesResult = {
    resultId: "test-result-id",
    resources: mockResources,
  };

  // Suppress act() warnings for async useEffect updates
  const originalError = console.error;
  beforeAll(() => {
    console.error = (...args: unknown[]) => {
      if (
        typeof args[0] === "string" &&
        args[0].includes("was not wrapped in act")
      ) {
        return;
      }
      originalError.call(console, ...args);
    };
  });

  afterAll(() => {
    console.error = originalError;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage to set userName and userEmail
    Storage.prototype.getItem = jest.fn((key: string) => {
      if (key === "userName") return "Test User";
      if (key === "userEmail") return "test@example.com";
      return null;
    });
  });

  it("does not show print button before results are received", () => {
    render(<Page />);

    // Print button should not be present initially
    const printButton = screen.queryByTestId("printReferralsButton");
    expect(printButton).not.toBeInTheDocument();
  });

  it("shows print button only after results are received", async () => {
    const user = userEvent.setup();

    // Mock successful fetchResources call
    jest
      .spyOn(fetchResourcesModule, "fetchResources")
      .mockResolvedValue(mockFetchResourcesResult);

    render(<Page />);

    // Verify print button is not present initially
    expect(
      screen.queryByTestId("printReferralsButton"),
    ).not.toBeInTheDocument();

    // Enter client description
    const textarea = screen.getByTestId("clientDescriptionInput");
    await user.type(textarea, "Client needs housing assistance");

    // Click the "Find Resources" button
    const findButton = screen.getByTestId("findResourcesButton");
    await user.click(findButton);

    // Wait for the print button to appear after results are loaded
    await waitFor(() => {
      const printButton = screen.getByTestId("printReferralsButton");
      expect(printButton).toBeInTheDocument();
    });

    // Verify resources are displayed (check for multiple instances)
    const resourceElements = screen.getAllByText("Test Resource");
    expect(resourceElements.length).toBeGreaterThan(0);
  });

  describe("toggleCategory", () => {
    it("selects a category when clicked", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      await user.click(employmentButton);

      // Button should be selected
      expect(employmentButton).toHaveAttribute("aria-pressed", "true");
    });

    it("deselects a category when clicked twice", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );

      // Select
      await user.click(employmentButton);
      expect(employmentButton).toHaveAttribute("aria-pressed", "true");

      // Deselect
      await user.click(employmentButton);
      expect(employmentButton).not.toHaveAttribute("aria-pressed", "true");
    });

    it("allows multiple categories to be selected", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );

      await user.click(employmentButton);
      await user.click(housingButton);

      expect(employmentButton).toHaveAttribute("aria-pressed", "true");
      expect(housingButton).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("toggleResourceType", () => {
    it("selects a resource type when clicked", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      await user.click(goodwillButton);

      expect(goodwillButton).toHaveAttribute("aria-pressed", "true");
    });

    it("deselects a resource type when clicked twice", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );

      // Select
      await user.click(goodwillButton);
      expect(goodwillButton).toHaveAttribute("aria-pressed", "true");

      // Deselect
      await user.click(goodwillButton);
      expect(goodwillButton).not.toHaveAttribute("aria-pressed", "true");
    });

    it("allows multiple resource types to be selected", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      const governmentButton = screen.getByTestId(
        "resourceCategoryToggle-government",
      );

      await user.click(goodwillButton);
      await user.click(governmentButton);

      expect(goodwillButton).toHaveAttribute("aria-pressed", "true");
      expect(governmentButton).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("clearAllFilters", () => {
    it("clears all selected categories, resource types, and location when clear button is clicked", async () => {
      const user = userEvent.setup();
      render(<Page />);

      // Select categories
      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(employmentButton);
      await user.click(housingButton);

      // Select resource types
      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      const governmentButton = screen.getByTestId(
        "resourceCategoryToggle-government",
      );
      await user.click(goodwillButton);
      await user.click(governmentButton);

      // Enter location
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "Austin, TX");

      // Verify filters are set
      expect(employmentButton).toHaveAttribute("aria-pressed", "true");
      expect(housingButton).toHaveAttribute("aria-pressed", "true");
      expect(goodwillButton).toHaveAttribute("aria-pressed", "true");
      expect(governmentButton).toHaveAttribute("aria-pressed", "true");
      expect(locationInput).toHaveValue("Austin, TX");

      // Click clear filters button
      const clearButton = screen.getByTestId("clearFiltersButton");
      await user.click(clearButton);

      // Verify all filters are cleared
      expect(employmentButton).not.toHaveAttribute("aria-pressed", "true");
      expect(housingButton).not.toHaveAttribute("aria-pressed", "true");
      expect(goodwillButton).not.toHaveAttribute("aria-pressed", "true");
      expect(governmentButton).not.toHaveAttribute("aria-pressed", "true");
      expect(locationInput).toHaveValue("");
    });

    it("shows clear button only when filters are applied", async () => {
      const user = userEvent.setup();
      render(<Page />);

      // Clear button should not be present initially
      expect(
        screen.queryByTestId("clearFiltersButton"),
      ).not.toBeInTheDocument();

      // Select a category
      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      await user.click(employmentButton);

      // Clear button should now be present
      expect(screen.getByTestId("clearFiltersButton")).toBeInTheDocument();

      // Clear filters
      const clearButton = screen.getByTestId("clearFiltersButton");
      await user.click(clearButton);

      // Clear button should be hidden again
      expect(
        screen.queryByTestId("clearFiltersButton"),
      ).not.toBeInTheDocument();
    });
  });

  describe("handleClick", () => {
    it("calls fetchResources with client description and filters", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Enter client description
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help getting to work");

      // Select a category
      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      await user.click(employmentButton);

      // Click find resources
      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      // Now assert on the last call's args
      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).toEqual(
        expect.stringContaining("Client needs help getting to work"),
      );
      expect(arg).toEqual(expect.stringContaining("Employment & Job Training"));
    });

    it("disables button when client description is empty", () => {
      render(<Page />);

      const findButton = screen.getByTestId("findResourcesButton");
      expect(findButton).toBeDisabled();
    });

    it("shows loading state while fetching resources", async () => {
      const user = userEvent.setup();
      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockImplementation(
          () =>
            new Promise((resolve) =>
              setTimeout(() => resolve(mockFetchResourcesResult), 100),
            ),
        );

      render(<Page />);

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      expect(screen.getByText("Generating Resources...")).toBeInTheDocument();
    });

    it("handles errors gracefully", async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();
      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockRejectedValue(new Error("API Error"));

      render(<Page />);

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith("API Error");
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe("handlePrint", () => {
    it("calls window.print when print button is clicked", async () => {
      const user = userEvent.setup();
      const printSpy = jest.spyOn(window, "print").mockImplementation();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Generate resources first
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for print button to appear
      await waitFor(() => {
        expect(screen.getByTestId("printReferralsButton")).toBeInTheDocument();
      });

      // Click print button
      const printButton = screen.getByTestId("printReferralsButton");
      await user.click(printButton);

      expect(printSpy).toHaveBeenCalled();
      printSpy.mockRestore();
    });
  });

  describe("conditional section rendering based on readyToPrint state", () => {
    it("shows clientDescriptionInputSection and referralFiltersSection when readyToPrint is false", () => {
      render(<Page />);

      // Both sections should be visible initially (readyToPrint is false)
      expect(
        screen.getByTestId("clientDescriptionInputSection"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("referralFiltersSection")).toBeInTheDocument();

      // readyToPrintSection should not be visible
      expect(
        screen.queryByTestId("readyToPrintSection"),
      ).not.toBeInTheDocument();
    });

    it("shows readyToPrintSection and hides other sections when readyToPrint is true", async () => {
      const user = userEvent.setup();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Enter client description and generate resources
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs assistance");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for readyToPrintSection to appear (readyToPrint becomes true)
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // clientDescriptionInputSection and referralFiltersSection should not be visible
      expect(
        screen.queryByTestId("clientDescriptionInputSection"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("referralFiltersSection"),
      ).not.toBeInTheDocument();
    });

    it("clears all filters and inputs when returnToSearchButton is clicked", async () => {
      const user = userEvent.setup();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Set up filters and client description
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing assistance");

      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      await user.click(employmentButton);

      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      await user.click(goodwillButton);

      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "Austin, TX");

      // Generate resources
      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for readyToPrintSection to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Click return to search button
      const returnButton = screen.getByTestId("returnToSearchButton");
      await user.click(returnButton);

      // Verify we're back to the search view
      expect(
        screen.getByTestId("clientDescriptionInputSection"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("referralFiltersSection")).toBeInTheDocument();

      // Verify all inputs and filters are cleared
      const clearedTextarea = screen.getByTestId("clientDescriptionInput");
      expect(clearedTextarea).toHaveValue("");

      const clearedEmploymentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      expect(clearedEmploymentButton).not.toHaveAttribute(
        "aria-pressed",
        "true",
      );

      const clearedGoodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      expect(clearedGoodwillButton).not.toHaveAttribute("aria-pressed", "true");

      const clearedLocationInput = screen.getByTestId("locationFilterInput");
      expect(clearedLocationInput).toHaveValue("");
    });
  });

  describe("getCollatedReferralOptions", () => {
    it("includes selected categories in the prompt", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select categories
      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(employmentButton);
      await user.click(housingButton);

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client description");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).toContain(
        "Include resources that support the following categories:",
      );
      expect(arg).toContain("Employment & Job Training");
      expect(arg).toContain("Housing & Shelter");
    });

    it("includes selected resource types in the prompt", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      await user.click(goodwillButton);

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client description");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).toContain("Include the following types of providers:");
      expect(arg).toContain("goodwill");
    });

    it("includes location in the prompt", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "Austin, TX");

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client description");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).toContain(
        "Focus on resources close to the following location:",
      );
      expect(arg).toContain("Austin, TX");
    });

    it("does not include filter prefixes when no filters are selected", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client description");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).not.toContain(
        "Include resources that support the following categories:",
      );
      expect(arg).not.toContain("Include the following types of providers:");
      expect(arg).not.toContain(
        "Focus on resources close to the following location:",
      );
    });
  });

  describe("WelcomeUserInputScreen", () => {
    it("renders WelcomeUserInputScreen when userName and userEmail are not set", () => {
      // Override localStorage to return null for userName and userEmail
      Storage.prototype.getItem = jest.fn(() => null);

      render(<Page />);

      // Check that WelcomeUserInputScreen is rendered
      // You may need to adjust this based on what's visible in WelcomeUserInputScreen
      // For now, we'll check that the main content sections are NOT visible
      expect(
        screen.queryByTestId("clientDescriptionInputSection"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("referralFiltersSection"),
      ).not.toBeInTheDocument();
    });

    it("does not render WelcomeUserInputScreen when userName and userEmail are set", () => {
      // userName and userEmail are already set in beforeEach
      render(<Page />);

      // Check that main content sections ARE visible
      expect(
        screen.getByTestId("clientDescriptionInputSection"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("referralFiltersSection")).toBeInTheDocument();
    });
  });

  describe("Remove Resource", () => {
    it("removes a resource when the Remove button is clicked", async () => {
      const user = userEvent.setup();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Generate resources first
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for resources to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Verify the resource is initially present
      expect(screen.getAllByText("Test Resource")).toHaveLength(3); // resource card, print view, and action plan

      // Click the Remove button for the first resource
      const removeButton = screen.getAllByTestId("remove-resource-button-0")[0]; // Button is on the page twice, rendered and print view
      await user.click(removeButton);

      // Verify the resource is removed
      await waitFor(() => {
        expect(screen.queryAllByText("Test Resource")).toHaveLength(0);
      });

      // Verify undo notification appears
      expect(screen.getByText("Resource removed")).toBeInTheDocument();
    });

    it("adds the removed resource back when undo is clicked", async () => {
      const user = userEvent.setup();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Generate resources first
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for resources to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Click the Remove button
      const removeButton = screen.getAllByTestId("remove-resource-button-0")[0]; // [0] is rendered, not printed button
      await user.click(removeButton);

      // Wait for resource to be removed
      await waitFor(() => {
        expect(screen.queryAllByText("Test Resource")).toHaveLength(0);
      });

      // Click the Undo button
      const undoButton = screen.getByText("Undo");
      await user.click(undoButton);

      // Verify the resource is added back
      await waitFor(() => {
        expect(screen.getAllByText("Test Resource")).toHaveLength(3);
      });

      // Verify undo notification is gone
      expect(screen.queryByText("Resource removed")).not.toBeInTheDocument();
    });

    it("ensures removed resource is not in Generate Action Plan section", async () => {
      const user = userEvent.setup();

      // Create a mock with multiple resources
      const mockMultipleResources: Resource[] = [
        {
          name: "Test Resource 1",
          addresses: ["123 Test St"],
          phones: ["555-1234"],
          emails: ["test1@example.com"],
          website: "https://example1.com",
          description: "Test description 1",
          justification: "Test justification 1",
        },
        {
          name: "Test Resource 2",
          addresses: ["456 Test Ave"],
          phones: ["555-5678"],
          emails: ["test2@example.com"],
          website: "https://example2.com",
          description: "Test description 2",
          justification: "Test justification 2",
        },
      ];

      jest.spyOn(fetchResourcesModule, "fetchResources").mockResolvedValue({
        resultId: "test-result-id",
        resources: mockMultipleResources,
      });

      render(<Page />);

      // Generate resources
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for resources to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Remove the first resource
      const removeButton = screen.getAllByTestId("remove-resource-button-0")[0];
      await user.click(removeButton);

      // Wait for the first resource to be removed from the display
      await waitFor(() => {
        expect(screen.queryAllByText("Test Resource 1")).toHaveLength(0);
      });

      // Verify the second resource is still present
      expect(screen.getAllByText("Test Resource 2")).toHaveLength(3);
    });

    it("restores removed resource to the same index when undo is clicked", async () => {
      const user = userEvent.setup();

      // Create a mock with three resources
      const mockMultipleResources: Resource[] = [
        {
          name: "First Resource",
          addresses: ["111 First St"],
          phones: ["555-1111"],
          emails: ["first@example.com"],
          website: "https://first.com",
          description: "First description",
          justification: "First justification",
        },
        {
          name: "Second Resource",
          addresses: ["222 Second St"],
          phones: ["555-2222"],
          emails: ["second@example.com"],
          website: "https://second.com",
          description: "Second description",
          justification: "Second justification",
        },
        {
          name: "Third Resource",
          addresses: ["333 Third St"],
          phones: ["555-3333"],
          emails: ["third@example.com"],
          website: "https://third.com",
          description: "Third description",
          justification: "Third justification",
        },
      ];

      jest.spyOn(fetchResourcesModule, "fetchResources").mockResolvedValue({
        resultId: "test-result-id",
        resources: mockMultipleResources,
      });

      render(<Page />);

      // Generate resources
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for resources to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Remove the second resource (middle one, index 1)
      const removeButton = screen.getAllByTestId("remove-resource-button-1")[0];
      await user.click(removeButton);

      // Wait for the second resource to be removed
      await waitFor(() => {
        expect(screen.queryAllByText("Second Resource")).toHaveLength(0);
      });

      // Click undo
      const undoButton = screen.getByText("Undo");
      await user.click(undoButton);

      // Wait for the resource to be restored
      await waitFor(() => {
        expect(screen.getAllByText("Second Resource")).toHaveLength(3);
      });

      // Verify the order is correct by checking the remove buttons
      // The second resource should be at index 1 again
      const removeButtons = screen.getAllByTestId(/remove-resource-button-\d+/);

      // Get the first 3 buttons (not the print view duplicates)
      const renderViewButtons = removeButtons.slice(0, 3);

      // Check that button at index 1 corresponds to "Second Resource"
      const secondResourceButton = renderViewButtons[1];
      expect(secondResourceButton).toHaveAttribute(
        "data-testid",
        "remove-resource-button-1",
      );
    });

    it("removes resource from selectedResources when removed from retainedResources", async () => {
      const user = userEvent.setup();

      // Create a mock with multiple resources
      const mockMultipleResources: Resource[] = [
        {
          name: "Test Resource 1",
          addresses: ["123 Test St"],
          phones: ["555-1234"],
          emails: ["test1@example.com"],
          website: "https://example1.com",
          description: "Test description 1",
          justification: "Test justification 1",
        },
        {
          name: "Test Resource 2",
          addresses: ["456 Test Ave"],
          phones: ["555-5678"],
          emails: ["test2@example.com"],
          website: "https://example2.com",
          description: "Test description 2",
          justification: "Test justification 2",
        },
      ];

      jest.spyOn(fetchResourcesModule, "fetchResources").mockResolvedValue({
        resultId: "test-result-id",
        resources: mockMultipleResources,
      });

      render(<Page />);

      // Generate resources
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Wait for resources to appear
      await waitFor(() => {
        expect(screen.getByTestId("readyToPrintSection")).toBeInTheDocument();
      });

      // Select the first resource for the action plan
      const firstResourceCheckbox = screen.getAllByRole("checkbox")[0];
      await user.click(firstResourceCheckbox);

      // Verify the checkbox is checked
      await waitFor(() => {
        expect(firstResourceCheckbox).toBeChecked();
      });

      // Remove the first resource
      const removeButton = screen.getAllByTestId("remove-resource-button-0")[0];
      await user.click(removeButton);

      // Wait for the resource to be removed
      await waitFor(() => {
        expect(screen.queryAllByText("Test Resource 1")).toHaveLength(0);
      });

      // Wait for resource to be restored
      await waitFor(() => {
        expect(screen.queryAllByText("Test Resource 1")).toHaveLength(0);
      });
    });
  });

  describe("Zip code to city/state replacement", () => {
    let fetchLocationFromZipMock: jest.Mock;

    beforeEach(() => {
      // Get the mock function from the module
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      fetchLocationFromZipMock =
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
        jest.requireMock("src/util/fetchLocation").fetchLocationFromZip;
      fetchLocationFromZipMock.mockClear();
    });

    it("replaces single zip code with city/state automatically", async () => {
      const user = userEvent.setup();
      fetchLocationFromZipMock.mockResolvedValue("Beverly Hills, CA");

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select a category
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter zip code in location field
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "90210");

      // Wait for the zip code lookup to complete automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("90210");
      });

      // Enter client description
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing");

      // Click Find Resources
      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Verify fetchResources was called with the replaced location
      await waitFor(() => {
        expect(fetchResourcesModule.fetchResources).toHaveBeenCalledWith(
          expect.stringContaining("Beverly Hills, CA"),
          "test@example.com",
          null,
        );
      });
    });

    it("replaces multiple zip codes in location field", async () => {
      const user = userEvent.setup();
      // Use mockImplementation to return different values based on input
      fetchLocationFromZipMock.mockImplementation((zipCode: string) => {
        if (zipCode === "90210") return Promise.resolve("Beverly Hills, CA");
        if (zipCode === "10001") return Promise.resolve("New York, NY");
        return Promise.resolve(null);
      });

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select a category
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter multiple zip codes
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "90210 or 10001");

      // Wait for both lookups to happen automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("90210");
      });
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("10001");
      });

      // Enter client description and search
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Verify both locations were replaced in the request
      await waitFor(() => {
        expect(fetchResourcesModule.fetchResources).toHaveBeenCalled();
      });
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
      const call = (fetchResourcesModule.fetchResources as jest.Mock).mock
        .calls[0];
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      expect(call[0]).toContain("Beverly Hills, CA");
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      expect(call[0]).toContain("New York, NY");
    });

    it("handles ZIP+4 format by using only first 5 digits", async () => {
      const user = userEvent.setup();
      fetchLocationFromZipMock.mockResolvedValue("Chicago, IL");

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select a category
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter ZIP+4 format
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "60601-1234");

      // Verify only the first 5 digits were used for lookup automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("60601");
      });

      // Enter client description and search
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Verify the city/state was used
      await waitFor(() => {
        expect(fetchResourcesModule.fetchResources).toHaveBeenCalledWith(
          expect.stringContaining("Chicago, IL"),
          "test@example.com",
          null,
        );
      });
    });

    it("preserves zip code when lookup fails", async () => {
      const user = userEvent.setup();
      fetchLocationFromZipMock.mockResolvedValue(null);

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select a category
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter invalid zip code
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "00000");

      // Wait for lookup to happen automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("00000");
      });

      // Enter client description and search
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Verify original zip code was preserved
      await waitFor(() => {
        expect(fetchResourcesModule.fetchResources).toHaveBeenCalledWith(
          expect.stringContaining("00000"),
          "test@example.com",
          null,
        );
      });
    });

    it("does not replace non-zip code text in location field", async () => {
      const user = userEvent.setup();

      jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockFetchResourcesResult);

      render(<Page />);

      // Select a category
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter city name (no zip code)
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "Los Angeles");

      // Should not call fetchLocationFromZip since there's no zip code
      await waitFor(
        () => expect(fetchLocationFromZipMock).not.toHaveBeenCalled(),
        { timeout: 200 },
      );

      // Enter client description and search
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs housing");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      // Verify original text was preserved
      await waitFor(() => {
        expect(fetchResourcesModule.fetchResources).toHaveBeenCalledWith(
          expect.stringContaining("Los Angeles"),
          "test@example.com",
          null,
        );
      });
    });

    it("updates collatedOptions automatically as location changes", async () => {
      const user = userEvent.setup();
      fetchLocationFromZipMock.mockResolvedValue("Beverly Hills, CA");

      render(<Page />);

      // Select a category first
      const housingButton = screen.getByTestId(
        "resourceCategoryToggle-housing",
      );
      await user.click(housingButton);

      // Enter zip code
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "90210");

      // Wait for the zip code to be looked up and collatedOptions to update automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("90210");
      });

      // Wait for collatedOptions to be updated with the resolved location
      await waitFor(() => {
        expect(
          screen.getByTestId("collatedOptionsDisplay"),
        ).toBeInTheDocument();
      });
      const display = screen.getByTestId("collatedOptionsDisplay");
      expect(display).toHaveTextContent("Beverly Hills, CA");
    });

    it("displays collatedOptions in the UI when filters are active", async () => {
      const user = userEvent.setup();
      fetchLocationFromZipMock.mockResolvedValue("Beverly Hills, CA");

      render(<Page />);

      // Select employment category
      const employmentButton = screen.getByTestId(
        "resourceCategoryToggle-employment",
      );
      await user.click(employmentButton);

      // Wait for collatedOptions to update
      await waitFor(() => {
        expect(
          screen.getByTestId("collatedOptionsDisplay"),
        ).toBeInTheDocument();
      });
      let display = screen.getByTestId("collatedOptionsDisplay");
      expect(display).toHaveTextContent("Employment & Job Training");

      // Select goodwill provider type
      const goodwillButton = screen.getByTestId(
        "resourceCategoryToggle-goodwill",
      );
      await user.click(goodwillButton);

      // Wait for collatedOptions to update with provider type
      await waitFor(() => {
        expect(screen.getByTestId("collatedOptionsDisplay")).toHaveTextContent(
          "goodwill",
        );
      });

      // Enter zip code in location
      const locationInput = screen.getByTestId("locationFilterInput");
      await user.type(locationInput, "90210");

      // Wait for location to be replaced and displayed automatically
      await waitFor(() => {
        expect(fetchLocationFromZipMock).toHaveBeenCalledWith("90210");
      });

      // The collatedOptions should now include all three selections
      await waitFor(() => {
        expect(
          screen.getByTestId("collatedOptionsDisplay"),
        ).toBeInTheDocument();
      });
      display = screen.getByTestId("collatedOptionsDisplay");
      expect(display).toHaveTextContent("Employment & Job Training");
      expect(display).toHaveTextContent("goodwill");
      expect(display).toHaveTextContent("Beverly Hills, CA");
    });
  });
});
