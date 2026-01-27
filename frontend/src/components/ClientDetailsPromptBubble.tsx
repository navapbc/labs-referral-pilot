interface ClientDetailsPromptBubbleProps {
  clientDescription: string;
}

const ClientDetailsPromptBubble = ({
  clientDescription,
}: ClientDetailsPromptBubbleProps) => {
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
      </div>
    </div>
  );
};

export default ClientDetailsPromptBubble;
