import { useEffect, useState } from "react";
import "./Audit.css";

interface AuditLog {
  id: number;
  action: string;
  actor: string;
  entity_id: number | null;
  entity_type: string;
  details: string;
  status: string;
  created_at: string;
}

interface Customer {
  id: number;
  name: string;
  email: string;
}

interface Product {
  id: number;
  name: string;
  price: number;
}

interface Opportunity {
  id: number;
  title: string;
  opportunity_type: string;
  description: string;
  estimated_value: number;
  confidence: string;
}

interface AgentAction {
  id: number;
  opportunity_id: number;
  action_type: string;
  status: string;
  customer?: Customer | null;
  product?: Product | null;
  final_amount?: number | null;
  action_amount?: number | null;
  discount_percentage?: number | null;
  execution_result?: string | null;
  payment_status?: string | null;
  payment_id?: string | null;
}

function Audit() {
  const [logs, setLogs] =
    useState<AuditLog[]>([]);

  const [customers, setCustomers] =
    useState<Customer[]>([]);

  const [products, setProducts] =
    useState<Product[]>([]);

  const [opportunities, setOpportunities] =
    useState<Opportunity[]>([]);

  const [actions, setActions] =
    useState<AgentAction[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

useEffect(() => {
  loadAuditLogs();
}, []);

  async function loadAuditLogs() {
  try {
    setLoading(true);
    setError("");

    await fetch(
      "http://127.0.0.1:8000/payments/sync",
      {
        method: "POST",
      }
    );

    const [
      auditResponse,
      customerResponse,
      productResponse,
      opportunityResponse,
      actionResponse,
    ] = await Promise.all([
      fetch("http://127.0.0.1:8000/audit/"),
      fetch("http://127.0.0.1:8000/customers/"),
      fetch("http://127.0.0.1:8000/products/"),
      fetch("http://127.0.0.1:8000/opportunities/"),
      fetch("http://127.0.0.1:8000/agent-actions/"),
    ]);

      if (!auditResponse.ok) {
        throw new Error(
          "Failed to load audit logs."
        );
      }

      const auditData =
        await auditResponse.json();

      setLogs(
        Array.isArray(auditData)
          ? auditData
          : []
      );

      if (customerResponse.ok) {
        const data =
          await customerResponse.json();

        setCustomers(
          Array.isArray(data)
            ? data
            : []
        );
      }

      if (productResponse.ok) {
        const data =
          await productResponse.json();

        setProducts(
          Array.isArray(data)
            ? data
            : []
        );
      }

      if (opportunityResponse.ok) {
        const data =
          await opportunityResponse.json();

        setOpportunities(
          Array.isArray(data)
            ? data
            : []
        );
      }

      if (actionResponse.ok) {
        const data =
          await actionResponse.json();

        setActions(
          Array.isArray(data)
            ? data
            : []
        );
      }

    } catch (err) {
      console.error(
        "Audit error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load audit logs."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(
    value: string
  ) {
    if (!value) {
      return "Unknown time";
    }

    /*
     * Backend timestamps are stored as UTC.
     * Some older records arrive without the trailing Z.
     * JavaScript treats those as local time, which shifts the
     * displayed time. Explicitly mark naive ISO timestamps as UTC.
     */
    const raw = String(value).trim();

    const hasTimezone =
      /(?:Z|[+-]\\d{2}:?\\d{2})$/i.test(
        raw
      );

    const utcValue =
      hasTimezone
        ? raw
        : `${raw}Z`;

    const date =
      new Date(utcValue);

    if (Number.isNaN(date.getTime())) {
      return "Unknown time";
    }

    return date.toLocaleString(
      "en-IN",
      {
        timeZone:
          "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }
    );
  }

  function formatText(
    value?: string | null
  ) {
    if (!value) {
      return "";
    }

    return value
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(
        /\b\w/g,
        (char) =>
          char.toUpperCase()
      );
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

  /*
   * Payment state is deliberately separate from the agent-action state.
   *
   * "approved" means the merchant approved the action.
   * It does NOT mean the customer paid.
   *
   * Razorpay payment links normally begin in a created/issued state.
   * Only an explicit paid/captured/authorized payment state is treated
   * as successful here.
   */
  function parseExecutionResult(
    action?: AgentAction | null
  ): any | null {
    if (!action?.execution_result) {
      return null;
    }

    try {
      return JSON.parse(
        action.execution_result
      );
    } catch {
      return null;
    }
  }

  function collectPaymentStates(
    value: any,
    states: string[] = []
  ): string[] {
    if (
      value === null ||
      value === undefined
    ) {
      return states;
    }

    if (
      typeof value === "string"
    ) {
      states.push(
        value.toLowerCase().trim()
      );
      return states;
    }

    if (
      Array.isArray(value)
    ) {
      value.forEach(
        (item) =>
          collectPaymentStates(
            item,
            states
          )
      );
      return states;
    }

    if (
      typeof value === "object"
    ) {
      Object.entries(value).forEach(
        ([key, item]) => {
          const normalizedKey =
            key
              .toLowerCase()
              .replace(
                /[^a-z0-9]/g,
                "_"
              );

          /*
           * Only inspect fields that can actually describe a payment.
           * This prevents email success, action execution success,
           * etc. from being mistaken for a successful payment.
           */
          if (
            normalizedKey.includes(
              "payment_status"
            ) ||
            normalizedKey === "paymentstate" ||
            normalizedKey === "payment_state" ||
            normalizedKey === "paymentstatus"
          ) {
            if (
              typeof item ===
              "string"
            ) {
              states.push(
                item
                  .toLowerCase()
                  .trim()
              );
            }
          }

          if (
            normalizedKey ===
              "payment" ||
            normalizedKey ===
              "payments" ||
            normalizedKey ===
              "razorpay_payment" ||
            normalizedKey ===
              "razorpay_payments"
          ) {
            collectPaymentStates(
              item,
              states
            );
          }
        }
      );
    }

    return states;
  }

  function isPaymentSuccessful(
    action?: AgentAction | null
  ) {
    if (!action) {
      return false;
    }

    const explicitStatus =
      String(
        action.payment_status ||
          ""
      )
        .toLowerCase()
        .trim();

    const result =
      parseExecutionResult(
        action
      );

    const states =
      collectPaymentStates(
        result
      );

    if (explicitStatus) {
      states.push(
        explicitStatus
      );
    }

    return states.some(
      (state) =>
        [
          "paid",
          "captured",
          "authorized",
          "success",
          "successful",
          "completed",
        ].includes(state)
    );
  }

  function getPaymentDisplayStatus(
    log: AuditLog
  ) {
    const action =
      getAction(
        log.entity_id
      );

    const entityType =
      String(
        log.entity_type || ""
      ).toLowerCase();

    const auditAction =
      String(
        log.action || ""
      ).toLowerCase();

    /*
     * A direct payment audit record is successful only when its own
     * status says paid/captured/successful. "created" is pending.
     */
    if (
      entityType === "payment" ||
      auditAction.includes("payment")
    ) {
      const value =
        String(
          log.status || ""
        ).toLowerCase();

      if (
        [
          "paid",
          "captured",
          "authorized",
          "success",
          "successful",
          "completed",
        ].includes(value)
      ) {
        return {
          label:
            "Payment Successful",
          className:
            "audit-status success",
        };
      }

      if (
        [
          "failed",
          "error",
          "cancelled",
          "canceled",
          "refunded",
        ].includes(value)
      ) {
        return {
          label:
            formatText(
              value
            ),
          className:
            "audit-status failed",
        };
      }

      return {
        label:
          "Payment Pending",
        className:
          "audit-status pending",
      };
    }

    /*
     * Approval/execution records tied to an agent action:
     * approved != paid.
     */
    if (
      action &&
      (
        entityType ===
          "agent_action" ||
        auditAction.includes(
          "approve"
        ) ||
        auditAction.includes(
          "execute"
        )
      )
    ) {
      if (
        isPaymentSuccessful(
          action
        )
      ) {
        return {
          label:
            "Payment Successful",
          className:
            "audit-status success",
        };
      }

      return {
        label:
          "Payment Pending",
        className:
          "audit-status pending",
      };
    }

    return null;
  }

  function getDisplayStatus(
    log: AuditLog
  ) {
    return (
      getPaymentDisplayStatus(
        log
      ) || {
        label:
          formatText(
            log.status
          ),
        className:
          getStatusClass(
            log.status
          ),
      }
    );
  }

  function getStatusClass(
    status: string
  ) {
    const value =
      String(
        status || ""
      ).toLowerCase();

    if (
      [
        "approved",
        "executed",
        "success",
        "completed",
        "auto_execute",
      ].includes(value)
    ) {
      return "audit-status success";
    }

    if (
      [
        "failed",
        "error",
        "rejected",
      ].includes(value)
    ) {
      return "audit-status failed";
    }

    if (
      [
        "pending",
        "pending_approval",
      ].includes(value)
    ) {
      return "audit-status pending";
    }

    return "audit-status";
  }

  function getCustomer(
    id: number | null
  ) {
    if (id === null) {
      return null;
    }

    return customers.find(
      (customer) =>
        customer.id === id
    );
  }

  function getProduct(
    id: number | null
  ) {
    if (id === null) {
      return null;
    }

    return products.find(
      (product) =>
        product.id === id
    );
  }

  function getOpportunity(
    id: number | null
  ) {
    if (id === null) {
      return null;
    }

    return opportunities.find(
      (opportunity) =>
        opportunity.id === id
    );
  }

  function getAction(
    id: number | null
  ) {
    if (id === null) {
      return null;
    }

    return actions.find(
      (action) =>
        action.id === id
    );
  }

  function getEntityLabel(
    log: AuditLog
  ) {
    const entityType =
      String(
        log.entity_type || ""
      ).toLowerCase();

    if (
      entityType ===
      "customer"
    ) {
      const customer =
        getCustomer(
          log.entity_id
        );

      return customer
        ? customer.name
        : "Customer activity";
    }

    if (
      entityType ===
      "product"
    ) {
      const product =
        getProduct(
          log.entity_id
        );

      return product
        ? product.name
        : "Product activity";
    }

    if (
      entityType ===
      "opportunity"
    ) {
      const opportunity =
        getOpportunity(
          log.entity_id
        );

      return opportunity
        ? opportunity.title
        : "Revenue opportunity";
    }

    if (
      entityType ===
      "agent_action"
    ) {
      const action =
        getAction(
          log.entity_id
        );

      if (action?.customer) {
        return `${action.customer.name}'s revenue action`;
      }

      return "Revenue action";
    }

    if (
      entityType ===
      "payment"
    ) {
      return "Razorpay payment";
    }

    if (
      entityType ===
      "transaction"
    ) {
      return "Payment transaction";
    }

    return (
      formatText(
        log.entity_type
      ) ||
      "Business activity"
    );
  }

  function getEventTitle(
    log: AuditLog
  ) {
    const action =
      String(
        log.action || ""
      ).toLowerCase();

    if (
      action.includes(
        "create_agent_action"
      )
    ) {
      return "MUNEEM created a revenue action";
    }

    if (
      action.includes(
        "approve"
      )
    ) {
      return "Merchant approved a revenue action";
    }

    if (
      action.includes(
        "reject"
      )
    ) {
      return "Revenue action rejected";
    }

    if (
      action.includes(
        "execute"
      )
    ) {
      return "MUNEEM executed a revenue action";
    }

    if (
      action.includes(
        "payment"
      )
    ) {
      return "Payment activity recorded";
    }

    if (
      action.includes(
        "opportunity"
      )
    ) {
      return "Revenue opportunity identified";
    }

    return formatText(
      log.action
    );
  }

  function getReadableDetails(
    log: AuditLog
  ) {
    let details =
      log.details ||
      "No additional details recorded.";

    /*
     * Replace common internal identifiers
     * with business-facing information.
     */

    const action =
      getAction(
        log.entity_id
      );

    if (action?.customer) {
      details = details.replace(
        new RegExp(
          `Customer\\s*#?${action.customer.id}`,
          "gi"
        ),
        action.customer.name
      );
    }

    if (action?.product) {
      details = details.replace(
        new RegExp(
          `Product\\s*#?${action.product.id}`,
          "gi"
        ),
        action.product.name
      );
    }

    const opportunity =
      getOpportunity(
        log.entity_id
      );

    if (opportunity) {
      details = details.replace(
        new RegExp(
          `Opportunity\\s*#?${opportunity.id}`,
          "gi"
        ),
        opportunity.title
      );
    }

    return details;
  }

  const totalEvents =
    logs.length;

  const displayStatuses =
    logs.map(
      (log) =>
        getDisplayStatus(
          log
        )
    );

  const successfulEvents =
    displayStatuses.filter(
      (status) =>
        status?.className ===
        "audit-status success"
    ).length;

  const pendingEvents =
    displayStatuses.filter(
      (status) =>
        status?.className ===
        "audit-status pending"
    ).length;

  const failedEvents =
    displayStatuses.filter(
      (status) =>
        status?.className ===
        "audit-status failed"
    ).length;

  const successRate =
    totalEvents > 0
      ? Math.round(
          (successfulEvents /
            totalEvents) *
            100
        )
      : 0;
const executedActions =
  actions.filter((action) => {
    const status = String(
      action.status || ""
    ).toLowerCase();

    return (
      status === "executed" ||
      status === "paid"
    );
  });

  const executedValue =
    executedActions.reduce(
      (sum, action) =>
        sum +
        Number(
          action.final_amount ??
          action.action_amount ??
          0
        ),
      0
    );

  if (loading) {
    return (
      <div className="audit-state">

        <span>
          07 / MUNEEM
        </span>

        <h1>
          Reading
          <br />
          <em>the trail.</em>
        </h1>

        <p>
          Loading decisions,
          actions and outcomes.
        </p>

      </div>
    );
  }

  if (error) {
    return (
      <div className="audit-state">

        <span>
          07 / MUNEEM
        </span>

        <h1>
          Audit
          <br />
          <em>unavailable.</em>
        </h1>

        <p>
          {error}
        </p>

        <button
          className="audit-retry"
          onClick={loadAuditLogs}
        >
          TRY AGAIN →
        </button>

      </div>
    );
  }

  return (
    <div className="audit-page">

      {/* =====================================================
          HERO
      ===================================================== */}

      <section className="audit-hero">

        <div className="audit-meta">

          <span>
            07 / MUNEEM
          </span>

          <span>
            ACCOUNTABILITY & CONTROL
          </span>

        </div>

        <div className="audit-hero-grid">

          <div className="audit-title">

            <p>
              EVERY DECISION LEAVES A TRACE
            </p>

            <h1>
              Nothing
              <br />
              <em>gets lost.</em>
            </h1>

          </div>

          <div className="audit-description">

            <strong>
              THE ACTIVITY TRAIL
            </strong>

            <p>
              Follow every meaningful
              MUNEEM decision from
              recommendation to approval,
              execution and payment outcome.
            </p>

          </div>

          <div className="audit-summary">

            <div>
              <span>
                EVENTS
              </span>

              <strong>
                {totalEvents}
              </strong>
            </div>

            <div>
              <span>
                SUCCESS
              </span>

              <strong>
                {successRate}%
              </strong>
            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          OVERVIEW
      ===================================================== */}

      <section className="audit-overview">

        <div className="audit-section-number">
          01
        </div>

        <div className="audit-section-heading">

          <span>
            ACTIVITY OVERVIEW
          </span>

          <h2>
            Know what
            <br />
            <em>happened.</em>
          </h2>

          <p>
            A transparent record of the
            decisions and actions moving
            through your revenue agent.
          </p>

        </div>

        <div className="audit-metrics">

          <div className="audit-metric">

            <span>
              TOTAL EVENTS
            </span>

            <strong>
              {totalEvents}
            </strong>

            <p>
              Decisions and actions
              recorded by MUNEEM.
            </p>

          </div>

          <div className="audit-metric">

            <span>
              SUCCESSFUL
            </span>

            <strong>
              {successfulEvents}
            </strong>

            <p>
              Events with a confirmed
              successful payment.
            </p>

          </div>

          <div className="audit-metric">

            <span>
              AWAITING REVIEW
            </span>

            <strong>
              {pendingEvents}
            </strong>

            <p>
              Actions whose customer
              payment is still pending.
            </p>

          </div>

          <div className="audit-metric">

            <span>
              FAILED / REJECTED
            </span>

            <strong>
              {failedEvents}
            </strong>

            <p>
              Events that did not
              complete successfully.
            </p>

          </div>

        </div>

      </section>


      {/* =====================================================
          BUSINESS IMPACT
      ===================================================== */}

      <section className="audit-overview">

        <div className="audit-section-number">
          02
        </div>

        <div className="audit-section-heading">

          <span>
            REVENUE IMPACT
          </span>

          <h2>
            Actions that
            <br />
            <em>moved.</em>
          </h2>

          <p>
            The audit trail connects
            agent decisions to the
            revenue actions they produced.
          </p>

        </div>

        <div className="audit-metrics">

          <div className="audit-metric">

            <span>
              EXECUTED ACTIONS
            </span>

            <strong>
              {executedActions.length}
            </strong>

            <p>
              Revenue actions completed
              by the agent, not customer
              payment confirmations.
            </p>

          </div>

          <div className="audit-metric">

            <span>
              EXECUTED VALUE
            </span>

            <strong>
              {money(
                executedValue
              )}
            </strong>

            <p>
              Value attached to
              completed actions.
            </p>

          </div>

        </div>

      </section>


      {/* =====================================================
          ACTIVITY LEDGER
      ===================================================== */}

      <section className="audit-log-section">

        <div className="audit-section-number">
          03
        </div>

        <div className="audit-section-heading">

          <span>
            ACTIVITY LEDGER
          </span>

          <h2>
            Follow the
            <br />
            <em>trail.</em>
          </h2>

        </div>

        <div className="audit-log-wrapper">

          <div className="audit-log-top">

            <div>

              <span>
                RECORDED ACTIVITY
              </span>

              <strong>
                {logs.length} EVENTS
              </strong>

            </div>

            <button
              className="audit-refresh"
              onClick={loadAuditLogs}
            >
              REFRESH
              <span>↻</span>
            </button>

          </div>

          {logs.length === 0 ? (

            <div className="audit-empty">

              <span>
                NO ACTIVITY
              </span>

              <h3>
                The trail is clear.
              </h3>

              <p>
                MUNEEM activity will appear
                here as decisions and actions
                are recorded.
              </p>

            </div>

          ) : (

            <div className="audit-table">

              <div className="audit-table-header">

                <span>
                  NO.
                </span>

                <span>
                  DECISION / EVENT
                </span>

                <span>
                  ACTOR
                </span>

                <span>
                  BUSINESS CONTEXT
                </span>

                <span>
                  STATUS
                </span>

                <span>
                  TIME
                </span>

              </div>

              {logs.map(
                (log, index) => {

                  const action =
                    getAction(
                      log.entity_id
                    );

                  return (
                    <article
                      className="audit-row"
                      key={log.id}
                    >

                      <div className="audit-index">
                        {String(
                          index + 1
                        ).padStart(
                          2,
                          "0"
                        )}
                      </div>


                      <div className="audit-event">

                        <h3>
                          {getEventTitle(
                            log
                          )}
                        </h3>

                        <p>
                          {getReadableDetails(
                            log
                          )}
                        </p>

                      </div>


                      <div className="audit-actor">

                        <span>
                          ACTOR
                        </span>

                        <strong>
                          {log.actor ===
                          "AI_AGENT"
                            ? "MUNEEM"
                            : formatText(
                                log.actor
                              )}
                        </strong>

                      </div>


                      <div className="audit-entity">

                        <span>
                          CONTEXT
                        </span>

                        <strong>
                          {getEntityLabel(
                            log
                          )}
                        </strong>

                        {action?.customer && (
                          <small
                            style={{
                              display:
                                "block",
                              marginTop:
                                "5px",
                              color:
                                "#888884",
                              fontSize:
                                "9px",
                            }}
                          >
                            {action.customer.name}
                            {" · "}
                            {action.customer.email}
                          </small>
                        )}

                        {action?.product && (
                          <small
                            style={{
                              display:
                                "block",
                              marginTop:
                                "5px",
                              color:
                                "#888884",
                              fontSize:
                                "9px",
                            }}
                          >
                            {action.product.name}
                            {" · "}
                            {money(
                              action.final_amount ??
                              action.action_amount
                            )}
                          </small>
                        )}

                      </div>


                      <div>

                        {(() => {
                          const displayStatus =
                            getDisplayStatus(
                              log
                            );

                          return (
                            <span
                              className={
                                displayStatus.className
                              }
                            >
                              <i />

                              {displayStatus.label}
                            </span>
                          );
                        })()}

                      </div>


                      <div className="audit-date">
                        {formatDate(
                          log.created_at
                        )}
                      </div>

                    </article>
                  );
                }
              )}

            </div>

          )}

        </div>

      </section>


      {/* =====================================================
          TRUST SECTION
      ===================================================== */}

      <section className="audit-insight">

        <div className="audit-section-number">
          04
        </div>

        <div>

          <span className="audit-insight-label">
            TRUST BY DESIGN
          </span>

          <h2>
            Every action
            <br />
            has a <em>history.</em>
          </h2>

        </div>

        <div className="audit-insight-copy">

          <p>
            MUNEEM does not hide the work
            happening behind the scenes.
            Recommendations, policy checks,
            approvals, executions and failures
            remain visible so the merchant
            always knows what happened.
          </p>

          <div className="audit-principles">

            <div>
              <strong>
                01
              </strong>

              <span>
                EXPLAIN
              </span>
            </div>

            <div>
              <strong>
                02
              </strong>

              <span>
                CONTROL
              </span>
            </div>

            <div>
              <strong>
                03
              </strong>

              <span>
                RECORD
              </span>
            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="audit-footer">

        <div>
          DETECT
        </div>

        <div>
          DECIDE
        </div>

        <div>
          EXECUTE
        </div>

        <span>
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>

      </footer>

    </div>
  );
}

export default Audit;