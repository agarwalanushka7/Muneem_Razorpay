import { useState } from "react";
import "./Login.css";

function Login() {
  const [isSignup, setIsSignup] = useState(false);

  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const resetMessages = () => {
    setError("");
    setSuccess("");
  };

  const switchMode = () => {
    setIsSignup(!isSignup);
    setBusinessName("");
    setEmail("");
    setPassword("");
    resetMessages();
  };

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    const cleanEmail = email.trim();
    const cleanBusinessName = businessName.trim();

    if (isSignup && !cleanBusinessName) {
      setError("Enter your business name.");
      return;
    }

    if (!cleanEmail || !password.trim()) {
      setError("Enter your email and password.");
      return;
    }

    if (password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      const endpoint = isSignup
        ? "http://127.0.0.1:8000/auth/signup"
        : "http://127.0.0.1:8000/auth/login";

      const body = isSignup
        ? {
            business_name: cleanBusinessName,
            email: cleanEmail,
            password,
          }
        : {
            email: cleanEmail,
            password,
          };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      let data: any = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            (isSignup
              ? "Unable to create account."
              : "Invalid email or password.")
        );
      }

      /*
       * SIGNUP
       *
       * The backend creates the merchant account.
       * We do not authenticate automatically.
       * The merchant is taken back to the login state.
       */
      if (isSignup) {
        setSuccess(
          "Account created successfully. You can now sign in."
        );

        setIsSignup(false);
        setBusinessName("");
        setPassword("");

        return;
      }

      /*
       * LOGIN
       *
       * Store only the identity of the merchant
       * who actually logged in.
       *
       * Nothing is hardcoded here.
       */
      localStorage.setItem(
        "muneem_authenticated",
        "true"
      );

      localStorage.setItem(
        "muneem_merchant_email",
        cleanEmail
      );

      /*
       * Business name is not currently returned by
       * the login API, so only store it if it exists
       * from a previous signup flow.
       */
      const storedBusinessName =
        localStorage.getItem("muneem_business_name");

      if (!storedBusinessName && cleanBusinessName) {
        localStorage.setItem(
          "muneem_business_name",
          cleanBusinessName
        );
      }

      window.location.href = "/dashboard";
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="muneem-login">

      {/* TOP NAV */}

      <header className="login-nav">

        <div className="login-logo">

          <div className="login-logo-box">
            M
          </div>

          <span>MUNEEM</span>

        </div>

        <div className="login-nav-right">

          <span>MERCHANT CONSOLE</span>

          <span className="login-nav-dot" />

        </div>

      </header>


      {/* MAIN */}

      <main className="login-hero">

        {/* LEFT */}

        <section className="login-intro">

          <div className="login-intro-top">

            <span className="login-index">
              01 / MUNEEM
            </span>

            <span className="login-location">
              INDIA · 2026
            </span>

          </div>


          <div className="login-headline">

            <p>
              REVENUE
            </p>

            <h1>
              SHOULD
            </h1>

            <h1 className="login-outline">
              WORK
            </h1>

            <h1>
              HARDER
            </h1>

          </div>


          <div className="login-intro-bottom">

            <p>
              MUNEEM watches your commerce
              activity, finds revenue opportunities,
              and helps you act on them.
            </p>

          </div>

        </section>


        {/* RIGHT PANEL */}

        <section className="login-panel">

          <div className="login-panel-inner">

            <div className="login-panel-header">

              <span className="login-small-label">
                MERCHANT PORTAL
              </span>

              <div className="login-live">

                <span />

                SECURE ACCESS

              </div>

            </div>


            <div className="login-card-heading">

              <h2>
                {isSignup ? (
                  <>
                    Create
                    <br />
                    account
                  </>
                ) : (
                  <>
                    Welcome
                    <br />
                    back
                  </>
                )}
              </h2>

              <p>
                {isSignup
                  ? "Set up your merchant workspace."
                  : "Sign in to continue to your merchant workspace."}
              </p>

            </div>


            <form
              className="muneem-login-form"
              onSubmit={handleSubmit}
            >

              {/* BUSINESS NAME */}

              {isSignup && (
                <div className="login-field">

                  <label htmlFor="businessName">
                    BUSINESS NAME
                  </label>

                  <input
                    id="businessName"
                    type="text"
                    value={businessName}
                    onChange={(event) =>
                      setBusinessName(event.target.value)
                    }
                    placeholder="Enter your business name"
                    autoComplete="organization"
                  />

                </div>
              )}


              {/* EMAIL */}

              <div className="login-field">

                <label htmlFor="email">
                  EMAIL
                </label>

                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="Enter your email"
                  autoComplete="email"
                />

              </div>


              {/* PASSWORD */}

              <div className="login-field">

                <label htmlFor="password">
                  PASSWORD
                </label>

                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete={
                    isSignup
                      ? "new-password"
                      : "current-password"
                  }
                />

              </div>


              {/* ERROR */}

              {error && (
                <div className="login-error">

                  <span>!</span>

                  {error}

                </div>
              )}


              {/* SUCCESS */}

              {success && (
                <div className="login-success">

                  <span>✓</span>

                  {success}

                </div>
              )}


              {/* SUBMIT */}

              <button
                type="submit"
                disabled={loading}
                className="login-submit"
              >

                <span>
                  {loading
                    ? isSignup
                      ? "CREATING ACCOUNT..."
                      : "SIGNING IN..."
                    : isSignup
                    ? "CREATE ACCOUNT"
                    : "SIGN IN"}
                </span>

                <span className="login-arrow">
                  →
                </span>

              </button>

            </form>


            {/* MODE SWITCH */}

            <div className="login-mode-switch">

              <span>
                {isSignup
                  ? "Already have an account?"
                  : "New to MUNEEM?"}
              </span>

              <button
                type="button"
                onClick={switchMode}
              >
                {isSignup
                  ? "SIGN IN"
                  : "CREATE ACCOUNT"}
                {" →"}
              </button>

            </div>


            <div className="login-panel-footer">

              <span>
                MUNEEM
              </span>

              <span>
                REVENUE INTELLIGENCE
              </span>

            </div>

          </div>

        </section>

      </main>


      {/* BOTTOM BAR */}

      <footer className="login-bottom">

        <div>
          DETECT
        </div>

        <div>
          DECIDE
        </div>

        <div>
          ACT
        </div>

        <span className="login-bottom-copy">
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>

      </footer>

    </div>
  );
}

export default Login;