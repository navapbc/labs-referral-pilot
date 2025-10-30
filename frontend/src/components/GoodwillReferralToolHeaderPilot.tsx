export function GoodwillReferralToolHeaderPilot() {
  return (
    <div className="">
      <div className="flex items-center gap-4 m-3">
        <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-lg p-2">
          <img
            src="/img/Goodwill_Industries_Logo.svg"
            alt="Goodwill Central Texas"
            className="w-10 h-10"
          />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Find Resources </h2>
          <div className="flex items-center gap-2">
            <p className="text-blue-600 font-medium">GenAI Referral Tool</p>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
              PILOT
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
