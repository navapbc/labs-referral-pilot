import { getRequestConfig } from "next-intl/server";
import { formats, timeZone } from "./config";
import { getMessagesWithFallbacks } from "./getMessagesWithFallbacks";
import { routing } from "./routing";

/**
 * Make locale messages available to all server components.
 * This method is used behind the scenes by `next-intl/plugin`, which is setup in next.config.js.
 * @see https://next-intl-docs.vercel.app/docs/usage/configuration#nextconfigjs
 */
export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  // Ensure that the incoming locale is valid
  if (!locale || !routing.locales.includes(locale as "en-US")) {
    locale = routing.defaultLocale;
  }
  return {
    formats,
    locale,
    messages: await getMessagesWithFallbacks(locale),
    timeZone,
  };
});
