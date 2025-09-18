import { pick } from "lodash";

import {
  NextIntlClientProvider,
  useMessages,
  useTranslations,
} from "next-intl";


type Props = {
  children: React.ReactNode;
  locale?: string;
};

const Layout = ({ children, locale }: Props) => {
  const t = useTranslations("components.Layout");
  const messages = useMessages();

  return (
    // Stick the footer to the bottom of the page
    <div className="">
      {/*<NextIntlClientProvider
        locale={locale}
        messages={pick(messages, "components.Header")}
      >
      </NextIntlClientProvider>*/}
      <main id="main-content" className="">
        <div >{children}</div>
      </main>
    </div>
  );
};

export default Layout;
