import { NextIntlClientProvider } from "next-intl";

type Props = {
  children: React.ReactNode;
  locale?: string;
};

const Layout = ({ children, locale }: Props) => {
  return (
    // Stick the footer to the bottom of the page
    <div className="">
      <NextIntlClientProvider locale={locale}>
        {children}
      </NextIntlClientProvider>
      <main id="main-content" className="">
        <div>{children}</div>
      </main>
    </div>
  );
};

export default Layout;
