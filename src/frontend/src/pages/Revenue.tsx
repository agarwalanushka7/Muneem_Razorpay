import { useEffect, useState } from "react";
import "./Revenue.css";

interface Summary {
  total_revenue: number;
  total_orders: number;
  average_order_value?: number;
  recovered_revenue?: number;
  pending_revenue?: number;
  total_opportunity_value?: number;
}

interface Opportunity {
  id: number;
  title: string;
  product_id?: number | null;
  related_product_id?: number | null;
  opportunity_type: string;
  customer_count: number;
  confidence: string;
  created_at: string;
  description: string;
  estimated_value: number;
  status: string;
}

interface AgentAction {
  id: number;
  opportunity_id: number;
  action_type: string;
  status: string;
  approval_required: boolean | number;

  action_amount?: number;
  original_amount?: number | null;
  discount_percentage?: number | null;
  discount_amount?: number | null;
  final_amount?: number | null;

  customer?: {
    id: number;
    name: string;
    email: string;
  } | null;

  product?: {
    id: number;
    name: string;
    price: number;
  } | null;

  offer?: {
    original_amount: number;
    discount_percentage: number;
    discount_amount: number;
    final_amount: number;
  } | null;
}

function Revenue() {
  const [summary, setSummary] =
    useState<Summary | null>(null);

  const [opportunities, setOpportunities] =
    useState<Opportunity[]>([]);

  const [actions, setActions] =
    useState<AgentAction[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadRevenue();
  }, []);

  async function loadRevenue() {
    try {
      setLoading(true);
      setError("");

      const summaryResponse = await fetch(
        "http://127.0.0.1:8000/dashboard/summary"
      );

      if (!summaryResponse.ok) {
        throw new Error(
          "Failed to load revenue summary."
        );
      }

      const summaryData =
        await summaryResponse.json();

      setSummary(summaryData);

      /*
       * Opportunities and actions are secondary
       * intelligence sources. If one is temporarily
       * unavailable, the financial summary can still
       * render.
       */

      const [opportunityResult, actionResult] =
        await Promise.allSettled([
          fetch(
            "http://127.0.0.1:8000/opportunities/"
          ),
          fetch(
            "http://127.0.0.1:8000/agent-actions/"
          ),
        ]);

      if (
        opportunityResult.status ===
        "fulfilled" &&
        opportunityResult.value.ok
      ) {
        const opportunityData =
          await opportunityResult.value.json();

        setOpportunities(
          Array.isArray(opportunityData)
            ? opportunityData
            : []
        );
      }

      if (
        actionResult.status ===
        "fulfilled" &&
        actionResult.value.ok
      ) {
        const actionData =
          await actionResult.value.json();

        setActions(
          Array.isArray(actionData)
            ? actionData
            : []
        );
      }
    } catch (err) {
      console.error(
        "Revenue error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load revenue."
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

  function getActionStatus(
    action: AgentAction
  ) {
    const status =
      String(
        action.status || ""
      ).toLowerCase();

    if (
      status === "executed" ||
      status === "completed"
    ) {
      return "EXECUTED";
    }

    if (
      status === "pending_approval" ||
      status === "pending"
    ) {
      return "REVIEW";
    }

    if (
      status === "rejected"
    ) {
      return "REJECTED";
    }

    if (
      status === "auto_execute"
    ) {
      return "READY";
    }

    return titleCase(
      action.status
    ).toUpperCase();
  }

  function getOpportunityAction(
    opportunityId: number
  ) {
    return actions.find(
      (action) =>
        action.opportunity_id ===
        opportunityId
    );
  }

  /*
   * We intentionally derive these numbers
   * from the actual agent actions.
   */

  const executedActions =
    actions.filter(
      (action) =>
        String(
          action.status
        ).toLowerCase() ===
          "executed" ||
        String(
          action.status
        ).toLowerCase() ===
          "completed"
    );

  const pendingActions =
    actions.filter(
      (action) =>
        String(
          action.status
        ).toLowerCase() ===
          "pending" ||
        String(
          action.status
        ).toLowerCase() ===
          "pending_approval"
    );

  const executedValue =
    executedActions.reduce(
      (total, action) =>
        total +
        Number(
          action.final_amount ??
          action.action_amount ??
          0
        ),
      0
    );

  const pendingValue =
    pendingActions.reduce(
      (total, action) =>
        total +
        Number(
          action.final_amount ??
          action.action_amount ??
          0
        ),
      0
    );

  const opportunityValue =
    opportunities.reduce(
      (total, opportunity) =>
        total +
        Number(
          opportunity.estimated_value ||
          0
        ),
      0
    );

  const totalOpportunityValue =
    opportunityValue ||
    Number(
      summary?.total_opportunity_value ||
      0
    );

  const averageOrderValue =
    summary?.average_order_value ??
    (
      summary?.total_orders
        ? summary.total_revenue /
          summary.total_orders
        : 0
    );

  const executionRate =
    totalOpportunityValue > 0
      ? Math.round(
          (executedValue /
            totalOpportunityValue) *
            100
        )
      : 0;

  if (loading) {
    return (
      <div className="revenue-state">

        <div className="revenue-spinner" />

        <p>
          Reading revenue signals...
        </p>

      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="revenue-state">

        <div className="revenue-state-icon">
          !
        </div>

        <h2>
          Revenue unavailable
        </h2>

        <p>
          {error ||
            "No revenue data is available."}
        </p>

        <button
          className="muneem-button muneem-button-primary"
          onClick={loadRevenue}
        >
          Try again
        </button>

      </div>
    );
  }

  return (
    <div className="revenue-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="revenue-header">

        <div>

          <p className="revenue-eyebrow">
            MUNEEM / REVENUE INTELLIGENCE
          </p>

          <h1>
            Revenue
          </h1>

          <p className="revenue-subtitle">
            See what your business has earned,
            what MUNEEM has identified and which
            opportunities are ready to become
            revenue.
          </p>

        </div>

        <div className="revenue-header-status">

          <span className="revenue-status-dot" />

          <span>
            Live intelligence
          </span>

          <button
            className="customers-refresh"
            onClick={loadRevenue}
          >
            REFRESH ↻
          </button>

        </div>

      </header>


      {/* =================================================
          CORE NUMBERS
      ================================================= */}

      <section className="revenue-primary">

        <div className="revenue-primary-main">

          <span>
            TOTAL REVENUE
          </span>

          <strong>
            {money(
              summary.total_revenue
            )}
          </strong>

          <p>
            Generated from recorded orders
          </p>

        </div>

        <div className="revenue-primary-side">

          <span>
            MUNEEM OPPORTUNITY
          </span>

          <strong>
            {money(
              totalOpportunityValue
            )}
          </strong>

          <p>
            Potential value identified
          </p>

        </div>

        <div className="revenue-primary-side">

          <span>
            AVERAGE ORDER
          </span>

          <strong>
            {money(
              averageOrderValue
            )}
          </strong>

          <p>
            Revenue per recorded order
          </p>

        </div>

      </section>


      {/* =================================================
          MUNEEM PIPELINE
      ================================================= */}

      <section className="revenue-section">

        <div className="revenue-section-header">

          <div>

            <p className="revenue-kicker">
              MUNEEM PIPELINE
            </p>

            <h2>
              From signal to revenue.
            </h2>

          </div>

          <p>
            Every opportunity passes through
            MUNEEM's bounded action flow before
            it can affect your business.
          </p>

        </div>


        <div className="revenue-signals">

          <article className="revenue-signal">

            <span className="signal-number">
              01
            </span>

            <div>

              <span className="signal-label">
                OPPORTUNITIES
              </span>

              <strong>
                {opportunities.length}
              </strong>

              <p>
                Revenue patterns identified
                from your commerce data.
              </p>

            </div>

          </article>


          <article className="revenue-signal">

            <span className="signal-number">
              02
            </span>

            <div>

              <span className="signal-label">
                READY / REVIEW
              </span>

              <strong>
                {pendingActions.length}
              </strong>

              <p>
                Actions waiting for the next
                permitted step.
              </p>

            </div>

          </article>


          <article className="revenue-signal">

            <span className="signal-number">
              03
            </span>

            <div>

              <span className="signal-label">
                EXECUTED VALUE
              </span>

              <strong>
                {money(
                  executedValue
                )}
              </strong>

              <p>
                Revenue value attached to
                completed MUNEEM actions.
              </p>

            </div>

          </article>

        </div>


        <div className="recovery-progress">

          <div className="recovery-progress-label">

            <span>
              Opportunity execution
            </span>

            <strong>
              {Math.min(
                executionRate,
                100
              )}
              %
            </strong>

          </div>

          <div className="recovery-progress-track">

            <div
              className="recovery-progress-fill"
              style={{
                width: `${Math.min(
                  executionRate,
                  100
                )}%`,
              }}
            />

          </div>

          <p>
            {executedValue > 0
              ? `${money(
                  executedValue
                )} in completed MUNEEM actions.`
              : "No MUNEEM action has generated an executed outcome yet."}
          </p>

        </div>

      </section>


      {/* =================================================
          LIVE OPPORTUNITIES
      ================================================= */}

      <section className="revenue-section">

        <div className="revenue-section-header">

          <div>

            <p className="revenue-kicker">
              LIVE OPPORTUNITIES
            </p>

            <h2>
              Where MUNEEM sees growth.
            </h2>

          </div>

          <p>
            These recommendations come directly
            from the opportunity engine and
            customer purchase patterns.
          </p>

        </div>


        <div className="revenue-signals">

          {opportunities.length === 0 ? (

            <article className="revenue-signal">

              <span className="signal-number">
                —
              </span>

              <div>

                <span className="signal-label">
                  WATCHING
                </span>

                <strong>
                  No active opportunities
                </strong>

                <p>
                  MUNEEM continues watching
                  your commerce activity for
                  meaningful revenue patterns.
                </p>

              </div>

            </article>

          ) : (

            opportunities
              .slice(0, 6)
              .map(
                (
                  opportunity,
                  index
                ) => {

                  const action =
                    getOpportunityAction(
                      opportunity.id
                    );

                  const recommendedProduct =
                    action?.product?.name;

                  return (
                    <article
                      className="revenue-signal"
                      key={
                        opportunity.id
                      }
                    >

                      <span className="signal-number">
                        {String(
                          index + 1
                        ).padStart(
                          2,
                          "0"
                        )}
                      </span>

                      <div>

                        <span className="signal-label">
                          {titleCase(
                            opportunity.opportunity_type
                          )}
                        </span>

                        <strong>
                          {opportunity.title}
                        </strong>

                        <p>
                          {opportunity.description}
                        </p>

                        <p>
                          <strong>
                            {money(
                              opportunity.estimated_value
                            )}
                          </strong>
                          {" "}
                          potential value
                          {" · "}
                          {opportunity.customer_count}
                          {" "}
                          customer
                          {opportunity.customer_count !==
                          1
                            ? "s"
                            : ""}
                          {" · "}
                          {titleCase(
                            opportunity.confidence
                          )}
                          {" confidence"}
                        </p>

                        {recommendedProduct && (
                          <p>
                            Recommended:
                            {" "}
                            <strong>
                              {
                                recommendedProduct
                              }
                            </strong>
                          </p>
                        )}

                        {action && (
                          <p>
                            MUNEEM action:
                            {" "}
                            <strong>
                              {getActionStatus(
                                action
                              )}
                            </strong>
                          </p>
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
          MONEY CURRENTLY IN MOTION
      ================================================= */}

      <section className="revenue-section">

        <div className="revenue-section-header">

          <div>

            <p className="revenue-kicker">
              MONEY IN MOTION
            </p>

            <h2>
              Revenue actions, not just reports.
            </h2>

          </div>

        </div>


        <div className="revenue-primary">

          <div className="revenue-primary-main">

            <span>
              EXECUTED
            </span>

            <strong>
              {money(
                executedValue
              )}
            </strong>

            <p>
              Value attached to executed
              revenue actions.
            </p>

          </div>

          <div className="revenue-primary-side">

            <span>
              AWAITING ACTION
            </span>

            <strong>
              {money(
                pendingValue
              )}
            </strong>

            <p>
              Opportunity currently waiting
              for execution or approval.
            </p>

          </div>

          <div className="revenue-primary-side">

            <span>
              ACTIONS COMPLETED
            </span>

            <strong>
              {executedActions.length}
            </strong>

            <p>
              Revenue actions successfully
              completed.
            </p>

          </div>

        </div>

      </section>


      {/* =================================================
          MUNEEM EXPLANATION
      ================================================= */}

      <section className="revenue-insight">

        <div className="revenue-insight-mark">
          M
        </div>

        <div className="revenue-insight-content">

          <span>
            MUNEEM
          </span>

          <h2>
            Revenue intelligence
            <br />
            that can actually <em>act.</em>
          </h2>

          <p>
            MUNEEM observes commerce activity,
            identifies a revenue opportunity,
            recommends an action, checks the
            merchant's policy and records the
            outcome. Money only moves through
            a bounded action path.
          </p>

        </div>

      </section>


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="revenue-footer">

        <div>

          <span>
            TOTAL REVENUE
          </span>

          <strong>
            {money(
              summary.total_revenue
            )}
          </strong>

        </div>

        <div>

          <span>
            OPPORTUNITY
          </span>

          <strong>
            {money(
              totalOpportunityValue
            )}
          </strong>

        </div>

        <div>

          <span>
            EXECUTED
          </span>

          <strong>
            {money(
              executedValue
            )}
          </strong>

        </div>

        <div>

          <span>
            ORDERS
          </span>

          <strong>
            {summary.total_orders}
          </strong>

        </div>

      </footer>

    </div>
  );
}

export default Revenue;