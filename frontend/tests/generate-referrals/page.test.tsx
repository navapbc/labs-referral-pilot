import { render, screen, waitFor } from "tests/react-utils";
import userEvent from "@testing-library/user-event";
import Page from "src/app/[locale]/generate-referrals/page";
import * as fetchResourcesModule from "src/util/fetchResources";
import { Resource } from "src/types/resources";

// Mock the fetchResources module
jest.mock("src/util/fetchResources");

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

  beforeEach(() => {
    jest.clearAllMocks();
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
      .mockResolvedValue(mockResources);

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

      const employmentButton = screen.getByText("Employment & Job Training");
      await user.click(employmentButton);

      // Button should have the selected styling
      expect(employmentButton).toHaveClass("bg-blue-600");
    });

    it("deselects a category when clicked twice", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const employmentButton = screen.getByText("Employment & Job Training");

      // Select
      await user.click(employmentButton);
      expect(employmentButton).toHaveClass("bg-blue-600");

      // Deselect
      await user.click(employmentButton);
      expect(employmentButton).not.toHaveClass("bg-blue-600");
    });

    it("allows multiple categories to be selected", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const employmentButton = screen.getByText("Employment & Job Training");
      const housingButton = screen.getByText("Housing & Shelter");

      await user.click(employmentButton);
      await user.click(housingButton);

      expect(employmentButton).toHaveClass("bg-blue-600");
      expect(housingButton).toHaveClass("bg-blue-600");
    });
  });

  describe("toggleResourceType", () => {
    it("selects a resource type when clicked", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByText("Goodwill Internal");
      await user.click(goodwillButton);

      expect(goodwillButton).toHaveClass("bg-blue-600");
    });

    it("deselects a resource type when clicked twice", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByText("Goodwill Internal");

      // Select
      await user.click(goodwillButton);
      expect(goodwillButton).toHaveClass("bg-blue-600");

      // Deselect
      await user.click(goodwillButton);
      expect(goodwillButton).not.toHaveClass("bg-blue-600");
    });

    it("allows multiple resource types to be selected", async () => {
      const user = userEvent.setup();
      render(<Page />);

      const goodwillButton = screen.getByText("Goodwill Internal");
      const governmentButton = screen.getByText("Government");

      await user.click(goodwillButton);
      await user.click(governmentButton);

      expect(goodwillButton).toHaveClass("bg-blue-600");
      expect(governmentButton).toHaveClass("bg-blue-600");
    });
  });

  describe("clearAllFilters", () => {
    it("clears all selected categories, resource types, and location when clear button is clicked", async () => {
      const user = userEvent.setup();
      render(<Page />);

      // Select categories
      const employmentButton = screen.getByText("Employment & Job Training");
      const housingButton = screen.getByText("Housing & Shelter");
      await user.click(employmentButton);
      await user.click(housingButton);

      // Select resource types
      const goodwillButton = screen.getByText("Goodwill Internal");
      const governmentButton = screen.getByText("Government");
      await user.click(goodwillButton);
      await user.click(governmentButton);

      // Enter location
      const locationInput = screen.getByPlaceholderText(
        "Enter location (city, area, zip code, etc.)",
      );
      await user.type(locationInput, "Austin, TX");

      // Verify filters are set
      expect(employmentButton).toHaveClass("bg-blue-600");
      expect(housingButton).toHaveClass("bg-blue-600");
      expect(goodwillButton).toHaveClass("bg-blue-600");
      expect(governmentButton).toHaveClass("bg-blue-600");
      expect(locationInput).toHaveValue("Austin, TX");

      // Click clear filters button
      const clearButton = screen.getByTestId("clearFiltersButton");
      await user.click(clearButton);

      // Verify all filters are cleared
      expect(employmentButton).not.toHaveClass("bg-blue-600");
      expect(housingButton).not.toHaveClass("bg-blue-600");
      expect(goodwillButton).not.toHaveClass("bg-blue-600");
      expect(governmentButton).not.toHaveClass("bg-blue-600");
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
      const employmentButton = screen.getByText("Employment & Job Training");
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
        .mockResolvedValue(mockResources);

      render(<Page />);

      // Enter client description
      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client needs help getting to work");

      // Select a category
      const employmentButton = screen.getByText("Employment & Job Training");
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
              setTimeout(() => resolve(mockResources), 100),
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
        .mockResolvedValue(mockResources);

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

  describe("getCollatedReferralOptions", () => {
    it("includes selected categories in the prompt", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockResources);

      render(<Page />);

      // Select categories
      const employmentButton = screen.getByText("Employment & Job Training");
      const housingButton = screen.getByText("Housing & Shelter");
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
        .mockResolvedValue(mockResources);

      render(<Page />);

      const goodwillButton = screen.getByText("Goodwill Internal");
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
        .mockResolvedValue(mockResources);

      render(<Page />);

      const locationInput = screen.getByPlaceholderText(
        "Enter location (city, area, zip code, etc.)",
      );
      await user.type(locationInput, "Portland, OR");

      const textarea = screen.getByTestId("clientDescriptionInput");
      await user.type(textarea, "Client description");

      const findButton = screen.getByTestId("findResourcesButton");
      await user.click(findButton);

      await waitFor(() => expect(fetchResourcesSpy).toHaveBeenCalledTimes(1));

      const [arg] = fetchResourcesSpy.mock.calls.at(-1)!;
      expect(arg).toContain(
        "Focus on resources close to the following location:",
      );
      expect(arg).toContain("Portland, OR");
    });

    it("does not include filter prefixes when no filters are selected", async () => {
      const user = userEvent.setup();
      const fetchResourcesSpy = jest
        .spyOn(fetchResourcesModule, "fetchResources")
        .mockResolvedValue(mockResources);

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
});
