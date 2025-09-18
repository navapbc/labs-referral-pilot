"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

const primaryLinks = [
  {
    i18nKey: "nav_link_home",
    href: "/",
  },
  {
    i18nKey: "nav_link_health",
    href: "/health",
  },
  {
    i18nKey: "nav_link_generate_referrals",
    href: "/generate-referrals",
  },
] as const;

const Header = () => {
  const t = useTranslations("components.Header");

  const [isMobileNavExpanded, setIsMobileNavExpanded] = useState(false);
  const handleMobileNavToggle = () => {
    setIsMobileNavExpanded(!isMobileNavExpanded);
  };

  const navItems = primaryLinks.map((link) => (
    <a href={link.href} key={link.href}>
      {t(link.i18nKey)}
    </a>
  ));

  return (
    <>
      <div
        className={`usa-overlay ${isMobileNavExpanded ? "is-visible" : ""}`}
      />
      <header>
        <div className="usa-nav-container">
          <div className="usa-navbar">
            <span className="desktop:margin-top-2">
              <div className="display-flex flex-align-center">
                <span className="margin-right-1">
                  <img
                    className="width-3 desktop:width-5 text-bottom margin-right-05"
                    src={`${
                      process.env.NEXT_PUBLIC_BASE_PATH ?? ""
                    }/img/logo.svg`}
                    alt="Site logo"
                  />
                </span>
                <span className="font-sans-lg flex-fill">{t("title")}</span>
              </div>
            </span>
            <button
              onClick={handleMobileNavToggle}
            >t("nav_menu_toggle")</button>
          </div>
          {/*} <PrimaryNav
            items={navItems}
            mobileExpanded={isMobileNavExpanded}
            onToggleMobileNav={handleMobileNavToggle}
          ></PrimaryNav>*/}
        </div>
      </header>
    </>
  );
};

export default Header;
