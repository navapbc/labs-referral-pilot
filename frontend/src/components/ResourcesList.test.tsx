import { axe } from "jest-axe";
import { render, screen } from "tests/react-utils";
import { Resource } from "@/types/resources";
import ResourcesList from "./ResourcesList";

const mockResource: Resource = {
  name: "Test Resource",
  description: "Test description",
  addresses: ["123 Test St"],
  phones: ["555-1234"],
  emails: ["test@example.com"],
  website: "https://example.com",
  referral_type: "goodwill",
};

describe("ResourcesList", () => {
  it("renders 'No resources found' when list is empty", () => {
    render(<ResourcesList resources={[]} />);

    expect(screen.getByText("No resources found.")).toBeInTheDocument();
  });

  it("renders single resource with all fields", () => {
    render(<ResourcesList resources={[mockResource]} />);

    expect(screen.getByText("Test Resource")).toBeInTheDocument();
    expect(screen.getByText("Test description")).toBeInTheDocument();
    expect(screen.getByText(/123 Test St/)).toBeInTheDocument();
    expect(screen.getByText(/555-1234/)).toBeInTheDocument();
    expect(screen.getByText(/test@example.com/)).toBeInTheDocument();
  });

  it("renders multiple resources", () => {
    const resources: Resource[] = [
      { name: "Resource 1", description: "First resource" },
      { name: "Resource 2", description: "Second resource" },
      { name: "Resource 3", description: "Third resource" },
    ];

    render(<ResourcesList resources={resources} />);

    expect(screen.getByText("Resource 1")).toBeInTheDocument();
    expect(screen.getByText("Resource 2")).toBeInTheDocument();
    expect(screen.getByText("Resource 3")).toBeInTheDocument();
  });

  it("displays goodwill referral type indicator", () => {
    const resource: Resource = {
      name: "Goodwill Center",
      referral_type: "goodwill",
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.getByTestId("goodwill_referral")).toBeInTheDocument();
  });

  it("displays government referral type indicator", () => {
    const resource: Resource = {
      name: "Government Service",
      referral_type: "government",
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.getByTestId("government_referral")).toBeInTheDocument();
  });

  it("displays external referral type indicator", () => {
    const resource: Resource = {
      name: "Community Center",
      referral_type: "external",
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.getByTestId("external_referral")).toBeInTheDocument();
  });

  it("does not display referral type indicator when undefined", () => {
    const resource: Resource = {
      name: "Generic Resource",
      description: "No type specified",
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.queryByText("Goodwill")).not.toBeInTheDocument();
    expect(screen.queryByText("Government")).not.toBeInTheDocument();
    expect(screen.queryByText("External")).not.toBeInTheDocument();
  });

  it("renders website link with proper attributes", () => {
    render(<ResourcesList resources={[mockResource]} />);

    const link = screen.getByRole("link", { name: /example.com/i });
    expect(link).toHaveAttribute("href", "https://example.com");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("normalizes website URLs without protocol", () => {
    const resource: Resource = {
      name: "Test Resource",
      website: "example.com",
    };

    render(<ResourcesList resources={[resource]} />);

    const link = screen.getByRole("link", { name: /example.com/i });
    expect(link).toHaveAttribute("href", "https://example.com");
  });

  it("handles multiple addresses separated by pipe", () => {
    const resource: Resource = {
      name: "Multi-Location Resource",
      addresses: ["123 Main St", "456 Oak Ave", "789 Pine Rd"],
    };

    render(<ResourcesList resources={[resource]} />);

    expect(
      screen.getByText(/123 Main St \| 456 Oak Ave \| 789 Pine Rd/),
    ).toBeInTheDocument();
  });

  it("handles multiple phone numbers separated by pipe", () => {
    const resource: Resource = {
      name: "Contact Resource",
      phones: ["555-1111", "555-2222"],
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.getByText(/555-1111 \| 555-2222/)).toBeInTheDocument();
  });

  it("displays resource index numbers correctly", () => {
    const resources: Resource[] = [
      { name: "First" },
      { name: "Second" },
      { name: "Third" },
    ];

    render(<ResourcesList resources={resources} />);

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("only renders fields that have values", () => {
    const resource: Resource = {
      name: "Minimal Resource",
    };

    render(<ResourcesList resources={[resource]} />);

    expect(screen.queryByText(/Address/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Phone/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Email/)).not.toBeInTheDocument();
  });

  it("passes accessibility scan with single resource", async () => {
    const { container } = render(<ResourcesList resources={[mockResource]} />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it("passes accessibility scan with empty list", async () => {
    const { container } = render(<ResourcesList resources={[]} />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it("passes accessibility scan with multiple resources", async () => {
    const resources: Resource[] = [
      { name: "Resource 1", description: "First" },
      { name: "Resource 2", description: "Second" },
    ];

    const { container } = render(<ResourcesList resources={resources} />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });
});
