import createNextIntlPlugin from "next-intl/plugin";

// Space-separated list of origins that are allowed to embed your app in an <iframe>
const ALLOWED_FRAME_ANCESTORS = "*"; // TODO change to only allowing predetermined hosts e.g. "https://train.caseworthy.com/Goodwill_CentralTexas_Train.caseworthy"
// Comma-separated list of extra connect-src origins/protocols
const ALLOWED_CONNECT_SOURCES = "*"; // TODO backend, localhost

const withNextIntl = createNextIntlPlugin("./src/i18n/server.ts");

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
const isProd = process.env.NODE_ENV === "production";

const FRAME_ANCESTORS = ALLOWED_FRAME_ANCESTORS.trim() || "'self'";

const CONNECT_EXTRA = (ALLOWED_CONNECT_SOURCES || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean)
  .join(" ");

const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' blob: data:",
  "font-src 'self'",
  `connect-src 'self' ${CONNECT_EXTRA} ${isProd ? "" : "ws:"}`.trim(),
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  `frame-ancestors ${FRAME_ANCESTORS}`,
].join("; ");

const nextConfig = {
  basePath,
  reactStrictMode: true,
  output: "standalone",
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // IMPORTANT: Ensure no other layer injects X-Frame-Options (remove it at the proxy/CDN).
          { key: "Content-Security-Policy", value: csp },
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
