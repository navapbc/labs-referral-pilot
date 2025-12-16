const ClientDetailsPromptBubble = ({
  clientDescription,
}: {
  clientDescription: string;
}) => {
  return (
    <div className="bg-gray-100 rounded-2xl p-4 border">
      <p className="text-lg font-semibold text-gray-900 text-center mb-3">
        {clientDescription.split("\n").map((line, index, array) => (
          <span key={index}>
            {line}
            {index < array.length - 1 && <br />}
          </span>
        ))}
      </p>
    </div>
  );
};
export default ClientDetailsPromptBubble;
