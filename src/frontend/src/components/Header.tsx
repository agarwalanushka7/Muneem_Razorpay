import { useEffect, useState } from "react";

function Header() {
  const [merchantEmail, setMerchantEmail] = useState("Merchant account");

  useEffect(() => {
    const email = localStorage.getItem("muneem_merchant_email");

    if (email) {
      setMerchantEmail(email);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("muneem_authenticated");
    localStorage.removeItem("muneem_merchant_email");
    localStorage.removeItem("muneem_business_name");

    window.location.href = "/";
  };

  return (
    <header className="muneem-header">

      <div className="muneem-header-brand">

        <div className="muneem-header-logo">
          M
        </div>

        <div className="muneem-header-brand-copy">

          <div className="muneem-header-name">
            MUNEEM
          </div>

          <div className="muneem-header-subtitle">
            Revenue Intelligence
          </div>

        </div>

      </div>


      <div className="muneem-header-right">

        <div className="muneem-account">

          <span className="muneem-account-dot" />

          <div className="muneem-account-copy">

            <div className="muneem-account-email">
              {merchantEmail}
            </div>

            <div className="muneem-account-label">
              Merchant account
            </div>

          </div>

        </div>


        <div className="muneem-header-divider" />


        <button
          type="button"
          onClick={handleLogout}
          className="muneem-logout"
        >
          <span>LOG OUT</span>
          <span className="muneem-logout-arrow">↗</span>
        </button>

      </div>

    </header>
  );
}

export default Header;