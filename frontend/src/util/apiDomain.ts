export function getApiDomain(): string {
  const environment = process.env.NEXT_PUBLIC_ENVIRONMENT;

  switch (environment) {
    case "local":
      return "http://0.0.0.0:3000/";
    case "dev":
      return "https://referral-pilot-dev.navateam.com/";
    case "prod":
      return "https://api.referrals.navateam.com/";
    default:
      return "http://localhost:3000/";
  }
}
