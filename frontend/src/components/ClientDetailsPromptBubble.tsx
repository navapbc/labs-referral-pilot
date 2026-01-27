import { resourceCategories } from "./ClientDetailsInput";

interface ClientDetailsPromptBubbleProps {
  clientDescription: string;
  selectedCategories?: string[];
  locationText?: string;
}

const ClientDetailsPromptBubble = ({
  clientDescription,
  selectedCategories = [],
  locationText = "",
}: ClientDetailsPromptBubbleProps) => {
  // Get category labels from IDs
  const categoryLabels = selectedCategories
    .map((id) => resourceCategories.find((c) => c.id === id)?.label)
    .filter(Boolean);

  // Build metadata string
  const metadataParts: string[] = [];
  if (categoryLabels.length > 0) {
    metadataParts.push(`Categories: ${categoryLabels.join(", ")}`);
  }
  if (locationText) {
    metadataParts.push(`Location: ${locationText}`);
  }

  return (
    <div data-testid="yourSearchSection">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Your Search</h2>
      <div className="bg-gray-100 rounded-2xl p-4 border">
        <p
          className="text-lg font-semibold text-gray-900 text-center"
          data-testid="searchQueryDisplay"
        >
          {clientDescription}
        </p>
        {metadataParts.length > 0 && (
          <p
            className="text-sm text-gray-600 text-center mt-2"
            data-testid="searchMetadataDisplay"
          >
            {metadataParts.join(" | ")}
          </p>
        )}
      </div>
    </div>
  );
};

export default ClientDetailsPromptBubble;
