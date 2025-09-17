import { pick } from "lodash";
import "../app/globals.css";


import {
  NextIntlClientProvider,
  useMessages,
  useTranslations,
} from "next-intl";

import Header from "./Header";

type Props = {
  children: React.ReactNode;
  locale?: string;
};

const Layout = ({ children, locale }: Props) => {
  const t = useTranslations("components.Layout");
  const messages = useMessages();

  return (
    // Stick the footer to the bottom of the page
    <div className="display-flex flex-column minh-viewport">
      {/* <a className="" href="#main-content">
        {t("skip_to_main")}
      </a>
      <NextIntlClientProvider
        locale={locale}
        messages={pick(messages, "components.Header")}
      >
        <Header />
      </NextIntlClientProvider>*/}
      <main id="main-content" className="grid-col-fill">
        <div>
          <div >
            <div >{children}</div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
