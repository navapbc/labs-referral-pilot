import { render, screen } from "tests/react-utils";
import userEvent from "@testing-library/user-event";
import { EmailOptionsDialog } from "src/components/EmailOptionsDialog";

describe("EmailOptionsDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    onSelectMode: jest.fn(),
    hasActionPlan: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders dialog with title and description", () => {
    render(<EmailOptionsDialog {...defaultProps} />);

    expect(
      screen.getByText("What would you like to email?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Choose what to include in your email."),
    ).toBeInTheDocument();
  });

  it("shows both options when hasActionPlan is true", () => {
    render(<EmailOptionsDialog {...defaultProps} />);

    expect(screen.getByText("Action Plan Only")).toBeInTheDocument();
    expect(
      screen.getByText("Action Plan + Full Referrals"),
    ).toBeInTheDocument();
  });

  it("shows only Full Referrals option when hasActionPlan is false", () => {
    render(<EmailOptionsDialog {...defaultProps} hasActionPlan={false} />);

    expect(screen.queryByText("Action Plan Only")).not.toBeInTheDocument();
    expect(screen.getByText("Full Referrals")).toBeInTheDocument();
  });

  it("calls onSelectMode with 'action-plan-only' when Action Plan Only is clicked", async () => {
    const user = userEvent.setup();
    render(<EmailOptionsDialog {...defaultProps} />);

    const actionPlanButton = screen.getByTestId("email-action-plan-only");
    await user.click(actionPlanButton);

    expect(defaultProps.onSelectMode).toHaveBeenCalledWith("action-plan-only");
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls onSelectMode with 'full-referrals' when Full Referrals is clicked", async () => {
    const user = userEvent.setup();
    render(<EmailOptionsDialog {...defaultProps} />);

    const fullReferralsButton = screen.getByTestId("email-full-referrals");
    await user.click(fullReferralsButton);

    expect(defaultProps.onSelectMode).toHaveBeenCalledWith("full-referrals");
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it("does not render content when open is false", () => {
    render(<EmailOptionsDialog {...defaultProps} open={false} />);

    expect(
      screen.queryByText("What would you like to email?"),
    ).not.toBeInTheDocument();
  });

  it("displays description for Action Plan Only option", () => {
    render(<EmailOptionsDialog {...defaultProps} />);

    expect(
      screen.getByText(
        "Includes contact info for selected resources (no descriptions)",
      ),
    ).toBeInTheDocument();
  });

  it("displays description for Full Referrals option", () => {
    render(<EmailOptionsDialog {...defaultProps} />);

    expect(
      screen.getByText("Includes complete resource details with descriptions"),
    ).toBeInTheDocument();
  });

  it("has proper accessibility attributes", () => {
    render(<EmailOptionsDialog {...defaultProps} />);

    const optionsGroup = screen.getByRole("group", { name: "Email options" });
    expect(optionsGroup).toBeInTheDocument();
  });
});
