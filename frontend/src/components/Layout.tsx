import {
  NextIntlClientProvider,
} from "next-intl";


type Props = {
  children: React.ReactNode;
  locale?: string;
};

const Layout = ({ children, locale }: Props) => {

  return (
    <div>
      <NextIntlClientProvider
        locale={locale}
        children={children}
      >
      </NextIntlClientProvider>
      <main id="main-content" className="">
        <div >{children}</div>
      </main>
    </div>
  );
};

export default Layout;
