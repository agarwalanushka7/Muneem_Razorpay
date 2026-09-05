import { useEffect, useState } from "react";
import "./Dashboard.css";

interface Summary {
  total_revenue?: number;
  total_orders?: number;
  recovered_revenue?: number;
  pending_revenue?: number;
  total_opportunity_value?: number;
  recovery_rate?: number;
}

interface Opportunity {
  id?: number;

  // Current backend fields
  opportunity_type?: string;
  title?: string;
  description?: string;
  product_id?: number;
  related_product_id?: number;
  customer_count?: number;
  estimated_value?: number;
  confidence?: string | number;
  status?: string;

  // Backward-compatible fields
  type?: string;
  potential_value?: number;
  product_name?: string;
}

interface Customer {
  id?: number;
  name?: string;
  email?: string;
  total_orders?: number;
  total_spent?: number;
}

interface AgentAction {
  id?: number;
  opportunity_id?: number;
  action_type?: string;
  action?: string;
  status?: string;
  created_at?: string;

  customer?: {
    id?: number;
    name?: string;
    email?: string;
  } | null;

  product?: {
    id?: number;
    name?: string;
    price?: number;
  } | null;

  offer?: {
    original_amount?: number;
    discount_percentage?: number;
    discount_amount?: number;
    final_amount?: number;
  };

  customer_message?: string | null;
}

interface Platform {
  id?: number;
  name?: string;
  platform_name?: string;
  status?: string;
  connection_type?: string;
  last_synced_at?: string;
}

function Dashboard() {
  const [summary, setSummary] =
    useState<Summary | null>(null);

  const [opportunities, setOpportunities] =
    useState<Opportunity[]>([]);

  const [actions, setActions] =
    useState<AgentAction[]>([]);

  const [platforms, setPlatforms] =
    useState<Platform[]>([]);

  const [customers, setCustomers] =
    useState<Customer[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  // =====================================================
  // LOAD DASHBOARD DATA
  // =====================================================

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const [
        summaryResponse,
        opportunitiesResponse,
        platformsResponse,
        actionsResponse,
        customersResponse,
      ] = await Promise.all([
        fetch(
          "http://127.0.0.1:8000/dashboard/summary"
        ),

        fetch(
          "http://127.0.0.1:8000/opportunities/"
        ),

        fetch(
          "http://127.0.0.1:8000/platforms/"
        ),

        fetch(
          "http://127.0.0.1:8000/agent-actions/"
        ),

        fetch(
          "http://127.0.0.1:8000/customers/"
        ),
      ]);

      // -------------------------------------------------
      // SUMMARY
      // -------------------------------------------------

      if (summaryResponse.ok) {
        const data =
          await summaryResponse.json();

        setSummary(
          data || null
        );
      }

      // -------------------------------------------------
      // OPPORTUNITIES
      // -------------------------------------------------

      if (opportunitiesResponse.ok) {
        const data =
          await opportunitiesResponse.json();

        setOpportunities(
          Array.isArray(data)
            ? data
            : []
        );
      }

      // -------------------------------------------------
      // PLATFORMS
      // -------------------------------------------------

      if (platformsResponse.ok) {
        const data =
          await platformsResponse.json();

        setPlatforms(
          Array.isArray(data)
            ? data
            : []
        );
      }

      // -------------------------------------------------
      // AGENT ACTIONS
      // -------------------------------------------------

      if (actionsResponse.ok) {
        const data =
          await actionsResponse.json();

        setActions(
          Array.isArray(data)
            ? data
            : []
        );
      }

      // -------------------------------------------------
      // CUSTOMERS
      // -------------------------------------------------

      if (customersResponse.ok) {
        const data =
          await customersResponse.json();

        setCustomers(
          Array.isArray(data)
            ? data
            : []
        );
      }

    } catch (err) {
      console.error(
        "Dashboard loading error:",
        err
      );

      setError(
        "Unable to load the merchant dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  // =====================================================
  // FORMATTERS
  // =====================================================

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

  function percent(
    value?: number | string | null
  ) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "—";
    }

    if (
      typeof value === "string"
    ) {
      const normalized =
        value.toLowerCase();

      if (
        normalized === "high"
      ) {
        return "High";
      }

      if (
        normalized === "medium"
      ) {
        return "Medium";
      }

      if (
        normalized === "low"
      ) {
        return "Low";
      }
    }

    return `${Number(
      value
    ).toFixed(0)}%`;
  }

  function formatText(
    value?: string
  ) {
    if (!value) {
      return "";
    }

    return value
      .replaceAll(
        "_",
        " "
      )
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  }

  // =====================================================
  // OPPORTUNITY HELPERS
  // =====================================================

  function opportunityType(
    opportunity: Opportunity
  ) {
    return (
      opportunity.opportunity_type ||
      opportunity.type ||
      "opportunity"
    );
  }

  function opportunityValue(
    opportunity: Opportunity
  ) {
    return Number(
      opportunity.estimated_value ??
      opportunity.potential_value ??
      0
    );
  }

  function opportunityTitle(
    opportunity: Opportunity
  ) {
    return (
      opportunity.title ||
      opportunity.product_name ||
      "Revenue opportunity"
    );
  }

  function opportunityDescription(
    opportunity: Opportunity
  ) {
    return (
      opportunity.description ||
      "MUNEEM identified a potential revenue opportunity."
    );
  }

  function confidenceLabel(
    opportunity: Opportunity
  ) {
    return percent(
      opportunity.confidence
    );
  }

  // =====================================================
  // ACTION HELPERS
  // =====================================================

  function actionName(
    action: AgentAction
  ) {
    return formatText(
      action.action_type ||
      action.action ||
      "Revenue action"
    );
  }

  function actionCustomer(
    action: AgentAction
  ) {
    return (
      action.customer?.name ||
      null
    );
  }

  function actionProduct(
    action: AgentAction
  ) {
    return (
      action.product?.name ||
      null
    );
  }

  function actionValue(
    action: AgentAction
  ) {
    return Number(
      action.offer?.final_amount ||
      action.offer?.original_amount ||
      0
    );
  }

  function actionDescription(
    action: AgentAction
  ) {
    const customer =
      actionCustomer(action);

    const product =
      actionProduct(action);

    if (
      customer &&
      product
    ) {
      return `${customer} → ${product}`;
    }

    if (customer) {
      return customer;
    }

    if (product) {
      return product;
    }

    return "MUNEEM revenue action";
  }

  // =====================================================
  // BUSINESS METRICS
  // =====================================================

  const revenue =
    Number(
      summary?.total_revenue || 0
    );

  const recovered =
    Number(
      summary?.recovered_revenue || 0
    );

  const pending =
    Number(
      summary?.pending_revenue || 0
    );

  const opportunityValueTotal =
    Number(
      summary?.total_opportunity_value ||
      opportunities.reduce(
        (
          total,
          opportunity
        ) =>
          total +
          opportunityValue(
            opportunity
          ),
        0
      )
    );

  const orders =
    Number(
      summary?.total_orders || 0
    );

  const recoveryRate =
    summary?.recovery_rate ??
    (
      opportunityValueTotal > 0
        ? (
            recovered /
            opportunityValueTotal
          ) * 100
        : 0
    );

  const averageOrderValue =
    orders > 0
      ? revenue / orders
      : 0;

  const activeActions =
    actions.filter(
      (action) => {
        const status =
          String(
            action.status ||
            ""
          ).toLowerCase();

        return (
          status !== "executed" &&
          status !== "completed" &&
          status !== "recovered" &&
          status !== "rejected"
        );
      }
    );

  const executedActions =
    actions.filter(
      (action) =>
        String(
          action.status ||
          ""
        ).toLowerCase() ===
        "executed"
    );

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <div className="dashboard-state">

        <span>
          01 / MUNEEM
        </span>

        <h1>
          Loading your
          <br />
          revenue
        </h1>

        <p>
          Preparing your merchant overview
        </p>

      </div>
    );
  }

  // =====================================================
  // ERROR
  // =====================================================

  if (error) {
    return (
      <div className="dashboard-state">

        <span>
          01 / MUNEEM
        </span>

        <h1>
          Something went
          <br />
          wrong
        </h1>

        <p>
          {error}
        </p>

        <button
          onClick={
            loadDashboard
          }
          className="dashboard-retry"
        >
          TRY AGAIN →
        </button>

      </div>
    );
  }

  // =====================================================
  // PAGE
  // =====================================================

  return (
    <div className="dashboard-page">

      {/* =================================================
          INTRO
      ================================================= */}

      <section className="dashboard-intro">

        <div className="dashboard-meta">

          <span>
            01 / MUNEEM
          </span>

          <span>
            MERCHANT OVERVIEW
          </span>

        </div>

        <div className="dashboard-intro-grid">

          <div>

            <p className="dashboard-kicker">
              REVENUE INTELLIGENCE
            </p>

            <h1>
              Make every
              <br />
              rupee <em>count</em>
            </h1>

            <p className="dashboard-description">
              MUNEEM watches your commerce
              activity, finds revenue
              opportunities, and turns
              useful signals into actions
              worth taking.
            </p>

          </div>

          <div className="dashboard-primary-card">

            <div className="dashboard-card-top">

              <span>
                REVENUE OPPORTUNITY
              </span>

              <span className="dashboard-live">
                <i />
                LIVE
              </span>

            </div>

            <strong>
              {money(
                opportunityValueTotal
              )}
            </strong>

            <p>
              Potential revenue identified
              across your business.
            </p>

            <div className="dashboard-card-line" />

            <div className="dashboard-card-stats">

              <div>

                <span>
                  RECOVERED
                </span>

                <strong>
                  {money(
                    recovered
                  )}
                </strong>

              </div>

              <div>

                <span>
                  RATE
                </span>

                <strong>
                  {percent(
                    recoveryRate
                  )}
                </strong>

              </div>

            </div>

          </div>

        </div>

      </section>

      {/* =================================================
          BUSINESS SNAPSHOT
      ================================================= */}

      <section className="dashboard-overview">

        <div className="dashboard-section-heading">

          <div className="dashboard-section-number">
            01
          </div>

          <div>

            <span>
              BUSINESS SNAPSHOT
            </span>

            <h2>
              Where your revenue
              <br />
              stands
            </h2>

          </div>

        </div>

        <div className="dashboard-metrics">

          <article className="dashboard-metric featured">

            <span>
              TOTAL REVENUE
            </span>

            <strong>
              {money(
                revenue
              )}
            </strong>

            <p>
              Revenue recorded across
              your connected commerce.
            </p>

          </article>

          <article className="dashboard-metric">

            <span>
              RECOVERED
            </span>

            <strong>
              {money(
                recovered
              )}
            </strong>

            <p>
              Revenue already recovered
              through MUNEEM.
            </p>

          </article>

          <article className="dashboard-metric">

            <span>
              PENDING
            </span>

            <strong>
              {money(
                pending
              )}
            </strong>

            <p>
              Revenue still available
              for action.
            </p>

          </article>

          <article className="dashboard-metric">

            <span>
              AVERAGE ORDER
            </span>

            <strong>
              {money(
                averageOrderValue
              )}
            </strong>

            <p>
              Average value across
              recorded orders.
            </p>

          </article>

        </div>

      </section>

      {/* =================================================
          MUNEEM OPPORTUNITIES
      ================================================= */}

      <section className="dashboard-opportunities">

        <div className="dashboard-section-heading">

          <div className="dashboard-section-number">
            02
          </div>

          <div>

            <span>
              MUNEEM SIGNALS
            </span>

            <h2>
              Revenue
              <br />
              opportunities
            </h2>

            <p>
              {opportunities.length}{" "}
              {opportunities.length === 1
                ? "opportunity"
                : "opportunities"}{" "}
              identified with{" "}
              {money(
                opportunityValueTotal
              )}{" "}
              in potential value.
            </p>

          </div>

        </div>

        <div className="opportunity-list">

          {opportunities.length === 0 ? (

            <div className="dashboard-empty">

              No revenue opportunities
              found right now.

            </div>

          ) : (

            opportunities
              .slice(
                0,
                6
              )
              .map(
                (
                  opportunity,
                  index
                ) => (

                  <article
                    className="opportunity-row"
                    key={
                      opportunity.id ??
                      index
                    }
                  >

                    <div className="opportunity-number">
                      {String(
                        index + 1
                      ).padStart(
                        2,
                        "0"
                      )}
                    </div>

                    <div className="opportunity-content">

                      <span>
                        {formatText(
                          opportunityType(
                            opportunity
                          )
                        ).toUpperCase()}
                      </span>

                      <h3>
                        {opportunityTitle(
                          opportunity
                        )}
                      </h3>

                      <p>
                        {opportunityDescription(
                          opportunity
                        )}
                      </p>

                      {opportunity.customer_count !==
                        undefined && (
                        <small>
                          {
                            opportunity.customer_count
                          }{" "}
                          {opportunity.customer_count ===
                          1
                            ? "customer"
                            : "customers"}{" "}
                          identified
                        </small>
                      )}

                    </div>

                    <div className="opportunity-data">

                      <div>

                        <span>
                          POTENTIAL
                        </span>

                        <strong>
                          {money(
                            opportunityValue(
                              opportunity
                            )
                          )}
                        </strong>

                      </div>

                      <div>

                        <span>
                          CONFIDENCE
                        </span>

                        <strong>
                          {confidenceLabel(
                            opportunity
                          )}
                        </strong>

                      </div>

                    </div>

                    <span className="opportunity-arrow">
                      →
                    </span>

                  </article>

                )
              )

          )}

        </div>

      </section>

      {/* =================================================
          AGENT PIPELINE
      ================================================= */}

      <section className="dashboard-flow">

        <div className="dashboard-section-heading">

          <div className="dashboard-section-number">
            03
          </div>

          <div>

            <span>
              AGENT PIPELINE
            </span>

            <h2>
              From opportunity
              <br />
              to <em>outcome</em>
            </h2>

          </div>

        </div>

        <div className="recovery-flow">

          <div className="flow-step">

            <span>
              01
            </span>

            <strong>
              {opportunities.length}
            </strong>

            <p>
              Opportunities
              detected
            </p>

          </div>

          <div className="flow-arrow">
            →
          </div>

          <div className="flow-step">

            <span>
              02
            </span>

            <strong>
              {activeActions.length}
            </strong>

            <p>
              Actions
              active
            </p>

          </div>

          <div className="flow-arrow">
            →
          </div>

          <div className="flow-step dark">

            <span>
              03
            </span>

            <strong>
              {executedActions.length}
            </strong>

            <p>
              Actions
              executed
            </p>

          </div>

        </div>

      </section>

      {/* =================================================
          AGENT ACTIVITY
      ================================================= */}

      <section className="dashboard-activity">

        <div className="dashboard-section-heading">

          <div className="dashboard-section-number">
            04
          </div>

          <div>

            <span>
              MUNEEM ACTIVITY
            </span>

            <h2>
              What the agent
              <br />
              is doing
            </h2>

          </div>

        </div>

        <div className="activity-list">

          {actions.length === 0 ? (

            <div className="dashboard-empty">
              No MUNEEM activity yet.
            </div>

          ) : (

            actions
              .slice(
                0,
                8
              )
              .map(
                (
                  action,
                  index
                ) => (

                  <div
                    className="activity-row"
                    key={
                      action.id ??
                      index
                    }
                  >

                    <span className="activity-index">
                      {String(
                        index + 1
                      ).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    <div>

                      <strong>
                        {actionName(
                          action
                        )}
                      </strong>

                      <p>
                        {actionDescription(
                          action
                        )}
                      </p>

                    </div>

                    <span
                      className={`activity-status ${
                        action.status ||
                        "pending"
                      }`}
                    >
                      {formatText(
                        action.status ||
                        "pending"
                      ).toUpperCase()}
                    </span>

                    <span className="activity-date">

                      {action.created_at
                        ? new Date(
                            action.created_at
                          ).toLocaleDateString(
                            "en-IN",
                            {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            }
                          )
                        : "—"}

                    </span>

                  </div>

                )
              )

          )}

        </div>

      </section>

      {/* =================================================
          CONNECTED BUSINESS
      ================================================= */}

      <section className="dashboard-connected">

        <div>

          <span className="dashboard-label">
            CONNECTED BUSINESS
          </span>

          <h2>
            Everything
            <br />
            <em>connected</em>
          </h2>

        </div>

        <div className="connected-stats">

          <div>

            <span>
              PLATFORMS
            </span>

            <strong>
              {platforms.length}
            </strong>

          </div>

          <div>

            <span>
              CUSTOMERS
            </span>

            <strong>
              {customers.length.toLocaleString(
                "en-IN"
              )}
            </strong>

          </div>

          <div>

            <span>
              ORDERS
            </span>

            <strong>
              {orders.toLocaleString(
                "en-IN"
              )}
            </strong>

          </div>

        </div>

      </section>

      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="dashboard-footer">

        <div>
          DETECT
        </div>

        <div>
          DECIDE
        </div>

        <div>
          ACT
        </div>

        <span>
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>

      </footer>

    </div>
  );
}

export default Dashboard;