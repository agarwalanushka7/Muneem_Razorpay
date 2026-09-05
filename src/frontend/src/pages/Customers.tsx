import { useEffect, useState } from "react";
import "./Customers.css";

interface Product {
  id: number;
  name: string;
  price: number;
  purchased_at?: string | null;
}

interface MuneemSignal {
  opportunity_id: number;
  type: string;
  title: string;
  description: string;
  recommended_product?: {
    id: number;
    name: string;
    price: number;
  } | null;
  estimated_value: number;
  confidence: string;
  opportunity_status: string;
  action_status?: string | null;
  final_amount?: number | null;
  discount_percentage?: number;
}

interface Customer {
  id: number;
  name: string;
  email: string;
  phone?: string | null;
  orders: number;
  total_spent: number;
  recent_products: Product[];
  muneem_signals: MuneemSignal[];
}

interface CustomerResponse {
  summary: {
    total_customers: number;
    total_orders: number;
    total_customer_revenue: number;
    customers_with_muneem_signals: number;
  };
  customers: Customer[];
}

function Customers() {
  const [data, setData] =
    useState<CustomerResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadCustomers();
  }, []);

  async function loadCustomers() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/customers/intelligence"
      );

      if (!response.ok) {
        throw new Error(
          `Request failed: ${response.status}`
        );
      }

      const result =
        await response.json();

      setData(result);
    } catch (err) {
      console.error(
        "Customer intelligence error:",
        err
      );

      setError(
        "Unable to load customer intelligence."
      );
    } finally {
      setLoading(false);
    }
  }

  function money(
    value?: number | null
  ) {
    return `₹${Number(
      value || 0
    ).toLocaleString(
      "en-IN",
      {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }
    )}`;
  }

  function titleCase(
    value?: string
  ) {
    if (!value) {
      return "";
    }

    return value
      .replaceAll("_", " ")
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  }

  function statusLabel(
    status?: string | null
  ) {
    if (!status) {
      return "WATCHING";
    }

    const normalized =
      status.toLowerCase();

    if (
      normalized === "executed" ||
      normalized === "completed"
    ) {
      return "EXECUTED";
    }

    if (
      normalized === "pending_approval" ||
      normalized === "pending"
    ) {
      return "REVIEW";
    }

    if (
      normalized === "rejected"
    ) {
      return "REJECTED";
    }

    return titleCase(
      status
    ).toUpperCase();
  }

  if (loading) {
    return (
      <main className="customers-page">
        <div className="customers-loading">
          <span>04 / CUSTOMERS</span>
          <h1>
            Reading your
            <br />
            customer base.
          </h1>
          <p>
            MUNEEM is preparing customer intelligence.
          </p>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="customers-page">
        <div className="customers-loading">
          <span>04 / CUSTOMERS</span>

          <h1>
            Customer intelligence
            <br />
            unavailable.
          </h1>

          <p>
            {error ||
              "No customer data is available."}
          </p>

          <button
            className="customers-retry"
            onClick={loadCustomers}
          >
            TRY AGAIN →
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="customers-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <section className="customers-hero">

        <div className="customers-topline">
          <span>
            04 / CUSTOMER INTELLIGENCE
          </span>

          <button
            className="customers-refresh"
            onClick={loadCustomers}
          >
            REFRESH ↻
          </button>
        </div>

        <div className="customers-hero-grid">

          <div>

            <span className="customers-kicker">
              MUNEEM IS WATCHING
            </span>

            <h1>
              Know the
              <br />
              customer
              <br />
              <em>behind the order.</em>
            </h1>

            <p>
              MUNEEM connects customer
              history with purchasing
              patterns to identify
              opportunities worth acting on.
            </p>

          </div>

          <div className="customers-summary">

            <div>
              <span>
                CUSTOMERS
              </span>

              <strong>
                {data.summary.total_customers}
              </strong>
            </div>

            <div>
              <span>
                ORDERS
              </span>

              <strong>
                {data.summary.total_orders}
              </strong>
            </div>

            <div>
              <span>
                CUSTOMER REVENUE
              </span>

              <strong>
                {money(
                  data.summary
                    .total_customer_revenue
                )}
              </strong>
            </div>

            <div>
              <span>
                MUNEEM SIGNALS
              </span>

              <strong>
                {
                  data.summary
                    .customers_with_muneem_signals
                }
              </strong>
            </div>

          </div>

        </div>

      </section>

      {/* =================================================
          CUSTOMER LIST
      ================================================= */}

      <section className="customers-list-section">

        <div className="customers-section-heading">

          <div className="customers-section-number">
            01
          </div>

          <div>
            <span>
              CUSTOMER BASE
            </span>

            <h2>
              People your
              <br />
              business serves.
            </h2>
          </div>

        </div>

        <div className="customer-list">

          {data.customers.length === 0 ? (

            <div className="customers-empty">
              No customers have been recorded yet.
            </div>

          ) : (

            data.customers.map(
              (
                customer,
                index
              ) => {

                const signal =
                  customer
                    .muneem_signals
                    ?.length > 0
                    ? customer
                        .muneem_signals[0]
                    : null;

                const recentProduct =
                  customer
                    .recent_products
                    ?.length > 0
                    ? customer
                        .recent_products[0]
                    : null;

                return (
                  <article
                    className="customer-card"
                    key={customer.id}
                  >

                    {/* ---------------------------------
                        CUSTOMER IDENTITY
                    --------------------------------- */}

                    <div className="customer-number">
                      {String(
                        index + 1
                      ).padStart(
                        2,
                        "0"
                      )}
                    </div>

                    <div className="customer-identity">

                      <span className="customer-label">
                        CUSTOMER
                      </span>

                      <h3>
                        {customer.name}
                      </h3>

                      <p>
                        {customer.email}
                      </p>

                      {customer.phone && (
                        <small>
                          {customer.phone}
                        </small>
                      )}

                    </div>

                    {/* ---------------------------------
                        CUSTOMER METRICS
                    --------------------------------- */}

                    <div className="customer-metrics">

                      <div>
                        <span>
                          ORDERS
                        </span>

                        <strong>
                          {customer.orders}
                        </strong>
                      </div>

                      <div>
                        <span>
                          SPENT
                        </span>

                        <strong>
                          {money(
                            customer.total_spent
                          )}
                        </strong>
                      </div>

                    </div>

                    {/* ---------------------------------
                        PURCHASE HISTORY
                    --------------------------------- */}

                    <div className="customer-purchases">

                      <span className="customer-label">
                        RECENT PURCHASE
                      </span>

                      {recentProduct ? (
                        <>
                          <strong>
                            {recentProduct.name}
                          </strong>

                          <p>
                            {money(
                              recentProduct.price
                            )}
                          </p>
                        </>
                      ) : (
                        <p>
                          No purchase history
                          available.
                        </p>
                      )}

                    </div>

                    {/* ---------------------------------
                        MUNEEM SIGNAL
                    --------------------------------- */}

                    <div
                      className={`customer-signal ${
                        signal
                          ? "has-signal"
                          : "no-signal"
                      }`}
                    >

                      <span className="customer-label">
                        MUNEEM SIGNAL
                      </span>

                      {signal ? (

                        <>
                          <div className="signal-status">
                            <i />
                            {statusLabel(
                              signal.action_status
                            )}
                          </div>

                          <h4>
                            {signal.title}
                          </h4>

                          {signal.recommended_product && (
                            <p className="signal-product">
                              →
                              {" "}
                              {
                                signal
                                  .recommended_product
                                  .name
                              }
                            </p>
                          )}

                          <p className="signal-description">
                            {signal.description}
                          </p>

                          <div className="signal-value">

                            <div>
                              <span>
                                OPPORTUNITY
                              </span>

                              <strong>
                                {money(
                                  signal
                                    .final_amount ??
                                  signal
                                    .estimated_value
                                )}
                              </strong>
                            </div>

                            {Number(
                              signal
                                .discount_percentage ||
                              0
                            ) > 0 && (
                              <div>
                                <span>
                                  INCENTIVE
                                </span>

                                <strong>
                                  {signal.discount_percentage}%
                                </strong>
                              </div>
                            )}

                          </div>

                        </>

                      ) : (

                        <div className="signal-watching">

                          <div className="signal-status">
                            <i />
                            WATCHING
                          </div>

                          <h4>
                            No active opportunity
                          </h4>

                          <p>
                            MUNEEM continues
                            watching this
                            customer's
                            purchasing
                            patterns.
                          </p>

                        </div>

                      )}

                    </div>

                  </article>
                );
              }
            )

          )}

        </div>

      </section>

      {/* =================================================
          INTELLIGENCE EXPLANATION
      ================================================= */}

      <section className="customers-intelligence">

        <div className="customers-section-number">
          02
        </div>

        <div className="customers-intelligence-content">

          <span>
            HOW MUNEEM THINKS
          </span>

          <h2>
            Every customer
            <br />
            becomes a <em>signal.</em>
          </h2>

          <p>
            MUNEEM looks at actual purchase
            history, product relationships
            and previous agent decisions.
            When a meaningful pattern appears,
            it turns that signal into a
            bounded revenue action.
          </p>

        </div>

        <div className="customers-intelligence-flow">

          <div>
            <span>01</span>
            <strong>
              PURCHASE
            </strong>
            <p>
              Customer activity
            </p>
          </div>

          <div>→</div>

          <div>
            <span>02</span>
            <strong>
              PATTERN
            </strong>
            <p>
              MUNEEM finds intent
            </p>
          </div>

          <div>→</div>

          <div>
            <span>03</span>
            <strong>
              ACTION
            </strong>
            <p>
              Revenue opportunity
            </p>
          </div>

        </div>

      </section>

      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="customers-footer">

        <span>
          CUSTOMER DATA
        </span>

        <span>
          MUNEEM INTELLIGENCE
        </span>

        <span>
          REVENUE ACTION
        </span>

      </footer>

    </main>
  );
}

export default Customers;