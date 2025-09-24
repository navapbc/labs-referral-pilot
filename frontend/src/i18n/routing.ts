import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en-US"], //TODO Update
  defaultLocale: "en-US",
  localePrefix: {
    mode: "always",
    prefixes: {
      "en-US": "/us",
    },
  },
  pathnames: {
    "/": "/",
    "/organization": {
      "en-US": "/organization",
    },
  },
});
