const ClientDetailsPromptBubble = ({
  clientDescription,
}: {
  clientDescription: string;
}) => {
  return (
    <div className="bg-gray-100 rounded-2xl p-4 border">
      <h2 className="text-lg font-medium text-gray-900 text-center mb-3">
        {clientDescription}
      </h2>
    </div>
  );
};
export default ClientDetailsPromptBubble;
