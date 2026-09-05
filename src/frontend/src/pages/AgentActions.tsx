import { useEffect, useState } from "react";
import "./AgentActions.css";

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

interface Offer {
  original_amount: number | null;
  discount_percentage: number;
  discount_amount: number;
  final_amount: number;
}

interface EmailResult {
  success?: boolean;
  sent?: boolean;
  to?: string;
  subject?: string;
  message_id?: string;
  sent_at?: string;
  provider?: string;
  status?: string;
  payment_link?: string;
}

interface ExecutionResult {
  success?: boolean;
  provider?: string;
  type?: string;
  id?: string;
  short_url?: string;
  status?: string;
  amount?: number;
  currency?: string;
  reference_id?: string;
  payment_id?: number | string;
  email?: EmailResult;
  purchase_history?: any[];
}

interface AgentAction {
  id: number;
  opportunity_id: number;
  action_type: string;
  action_amount: number;
  approval_required: boolean | number;
  status: string;
  customer: Customer | null;
  product: Product | null;
  offer: Offer;
  customer_message: string | null;
  execution_result: string | null;
  created_at: string;
  updated_at: string;
}

function AgentActions() {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processingId, setProcessingId] =
    useState<number | null>(null);

  const [executionResults, setExecutionResults] =
    useState<Record<number, ExecutionResult>>({});

  const [copiedActionId, setCopiedActionId] =
    useState<number | null>(null);

  // =====================================================
  // LOAD ACTIONS
  // =====================================================

  useEffect(() => {
    loadActions();
  }, []);

  async function loadActions(): Promise<AgentAction[]> {
    let safeData: AgentAction[] = [];

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/agent-actions/"
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load MUNEEM actions."
        );
      }

      const data = await response.json();

      safeData =
        Array.isArray(data)
          ? data.map(normalizeAction)
          : [];

      setActions(safeData);

      const savedResults: Record<
        number,
        ExecutionResult
      > = {};

      safeData.forEach((action) => {
        const execution =
          parseExecutionResult(
            action.execution_result
          );

        if (execution) {
          savedResults[action.id] =
            execution;
        }
      });

      setExecutionResults(savedResults);
    } catch (err) {
      console.error(
        "MUNEEM actions error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load MUNEEM actions."
      );
    } finally {
      setLoading(false);
    }

    return safeData;
  }

  // =====================================================
  // NORMALIZE ACTION
  // =====================================================

  function normalizeAction(
    action: any
  ): AgentAction {

    const storedCustomer =
      getStoredCustomer(
        action?.execution_result
      );

    const storedProduct =
      getStoredProduct(
        action?.execution_result
      );

    const storedOffer =
      getStoredOffer(
        action?.execution_result
      );

    const customer =
      action?.customer ||
      storedCustomer ||
      null;

    const product =
      action?.product ||
      storedProduct ||
      null;

    const offer: Offer = {
      original_amount:
        action?.offer?.original_amount ??
        action?.original_amount ??
        storedOffer?.original_amount ??
        action?.action_amount ??
        0,

      discount_percentage:
        action?.offer?.discount_percentage ??
        action?.discount_percentage ??
        storedOffer?.discount_percentage ??
        0,

      discount_amount:
        action?.offer?.discount_amount ??
        action?.discount_amount ??
        storedOffer?.discount_amount ??
        0,

      final_amount:
        action?.offer?.final_amount ??
        action?.final_amount ??
        storedOffer?.final_amount ??
        action?.action_amount ??
        0,
    };

    return {
      id: Number(action?.id || 0),

      opportunity_id:
        Number(
          action?.opportunity_id || 0
        ),

      action_type:
        String(
          action?.action_type ||
          "revenue_action"
        ),

      action_amount:
        Number(
          action?.action_amount || 0
        ),

      approval_required:
        action?.approval_required ??
        false,

      status:
        String(
          action?.status ||
          "pending"
        ).toLowerCase(),

      customer,

      product,

      offer,

      customer_message:
        action?.customer_message ||
        getStoredCustomerMessage(
          action?.execution_result
        ) ||
        null,

      execution_result:
        action?.execution_result ||
        null,

      created_at:
        action?.created_at || "",

      updated_at:
        action?.updated_at || "",
    };
  }

  // =====================================================
  // EXECUTION RESULT
  // =====================================================

  function parseExecutionResult(
    value: string | null | undefined
  ): ExecutionResult | null {

    if (!value) {
      return null;
    }

    try {
      const parsed =
        JSON.parse(value);

      if (parsed?.razorpay) {
        return {
          ...parsed.razorpay,
          email: parsed.email,
          purchase_history:
            parsed.purchase_history || [],
        };
      }

      if (
        parsed?.short_url ||
        parsed?.provider ||
        parsed?.type
      ) {
        return parsed;
      }

      return null;
    } catch {
      return null;
    }
  }

  // =====================================================
  // EMAIL RESULT
  // =====================================================

  function parseEmailResult(
    value: string | null | undefined
  ): EmailResult | null {

    if (!value) {
      return null;
    }

    try {
      const parsed = JSON.parse(value);
      const email = parsed?.email;

      if (!email) {
        return null;
      }

      return {
        success: Boolean(email.success),
        sent: Boolean(email.sent ?? email.success),
        to: email.to || email.email || "",
        subject: email.subject || "",
        message_id:
          email.message_id ||
          email.id ||
          "",
        sent_at:
          email.sent_at ||
          email.created_at ||
          null,
        provider:
          email.provider ||
          "",
        status:
          email.status ||
          "",
        payment_link:
          email.payment_link ||
          "",
      };
    } catch {
      return null;
    }
  }

  // =====================================================
  // STORED CUSTOMER
  // =====================================================

  function getStoredCustomer(
    value: string | null | undefined
  ): Customer | null {

    if (!value) {
      return null;
    }

    try {
      const parsed =
        JSON.parse(value);

      if (
        parsed?.customer?.id &&
        parsed?.customer?.name
      ) {
        return {
          id: Number(
            parsed.customer.id
          ),
          name:
            parsed.customer.name,
          email:
            parsed.customer.email ||
            "",
        };
      }

      return null;
    } catch {
      return null;
    }
  }

  // =====================================================
  // STORED PRODUCT
  // =====================================================

  function getStoredProduct(
    value: string | null | undefined
  ): Product | null {

    if (!value) {
      return null;
    }

    try {
      const parsed =
        JSON.parse(value);

      if (
        parsed?.product?.id &&
        parsed?.product?.name
      ) {
        return {
          id: Number(
            parsed.product.id
          ),
          name:
            parsed.product.name,
          price:
            Number(
              parsed.product.price || 0
            ),
        };
      }

      return null;
    } catch {
      return null;
    }
  }

  // =====================================================
  // STORED OFFER
  // =====================================================

  function getStoredOffer(
    value: string | null | undefined
  ): Offer | null {

    if (!value) {
      return null;
    }

    try {
      const parsed =
        JSON.parse(value);

      if (!parsed?.offer) {
        return null;
      }

      return {
        original_amount:
          Number(
            parsed.offer.original_amount ||
            0
          ),

        discount_percentage:
          Number(
            parsed.offer.discount_percentage ||
            0
          ),

        discount_amount:
          Number(
            parsed.offer.discount_amount ||
            0
          ),

        final_amount:
          Number(
            parsed.offer.final_amount ||
            0
          ),
      };
    } catch {
      return null;
    }
  }

  // =====================================================
  // STORED MESSAGE
  // =====================================================

  function getStoredCustomerMessage(
    value: string | null | undefined
  ): string | null {

    if (!value) {
      return null;
    }

    try {
      const parsed =
        JSON.parse(value);

      return (
        parsed?.customer_message ||
        null
      );
    } catch {
      return null;
    }
  }

  // =====================================================
  // MAIL COMPOSER
  // =====================================================

  function getPurchaseHistoryFromAction(
    action: AgentAction
  ): Array<{
    product_name?: string;
    quantity?: number;
    amount?: number;
    created_at?: string;
  }> {
    if (!action.execution_result) {
      return [];
    }

    try {
      const parsed =
        JSON.parse(action.execution_result);

      const history =
        parsed?.purchase_history ||
        parsed?.execution?.purchase_history ||
        [];

      return Array.isArray(history)
        ? history
        : [];
    } catch {
      return [];
    }
  }

  function getPaymentLinkFromAction(
    action: AgentAction | null
  ): string {
    if (!action?.execution_result) {
      return "";
    }

    try {
      const parsed =
        JSON.parse(action.execution_result);

      return (
        parsed?.payment_link ||
        parsed?.razorpay?.short_url ||
        parsed?.execution?.payment_link ||
        parsed?.execution?.razorpay?.short_url ||
        ""
      );
    } catch {
      return "";
    }
  }

  function openPersonalizedMail(
    action: AgentAction,
    paymentLink: string
  ) {
    const customerEmail =
      action.customer?.email || "";

    if (!customerEmail) {
      setError(
        "Payment link was created, but this customer has no email address."
      );
      return;
    }

    const customerName =
      action.customer?.name ||
      "Customer";

    const productName =
      action.product?.name ||
      "Recommended product";

    const originalAmount =
      Number(
        action.offer?.original_amount ||
        action.action_amount ||
        0
      );

    const discountPercentage =
      Number(
        action.offer?.discount_percentage ||
        0
      );

    const discountAmount =
      Number(
        action.offer?.discount_amount ||
        0
      );

    const finalAmount =
      Number(
        action.offer?.final_amount ||
        action.action_amount ||
        0
      );

    const message =
      getPersonalizedCustomerMessage(action);

    const purchaseHistory =
      getPurchaseHistoryFromAction(action);

    const previousPurchasesText =
      purchaseHistory.length > 0
        ? purchaseHistory
            .map((purchase, index) => {
              const quantity =
                Number(purchase.quantity || 1);

              const amount =
                Number(purchase.amount || 0);

              const date =
                purchase.created_at
                  ? new Date(
                      purchase.created_at
                    ).toLocaleDateString(
                      "en-IN"
                    )
                  : "";

              return (
                `${index + 1}. ` +
                `${purchase.product_name || "Product"} ` +
                `× ${quantity}` +
                `${amount > 0 ? ` — ${money(amount)}` : ""}` +
                `${date ? ` — ${date}` : ""}`
              );
            })
            .join("\n")
        : "No previous purchases found.";

    const body =
      `${message}\n\n` +
      `YOUR PREVIOUS PURCHASES\n` +
      `${previousPurchasesText}\n\n` +
      `PAYMENT LINK\n` +
      `${paymentLink || "Payment link unavailable"}\n\n` +
      `Offer summary:\n` +
      `Original price: ${money(originalAmount)}\n` +
      `Discount: ${discountPercentage}% (${money(discountAmount)})\n` +
      `Personalized price: ${money(finalAmount)}\n`;

    const subject =
      `Personalized offer from MUNEEM — ${productName}`;

    const mailto =
      `mailto:${encodeURIComponent(customerEmail)}` +
      `?subject=${encodeURIComponent(subject)}` +
      `&body=${encodeURIComponent(body)}`;

    // This runs from the user's Approve click, so mailto opens
    // the configured desktop/browser mail application.
    window.location.href = mailto;
  }

  // =====================================================
  // APPROVE
  // =====================================================

  async function approveAction(
    actionId: number
  ) {
    try {
      setProcessingId(actionId);
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/agent-actions/${actionId}/approve`,
        {
          method: "POST",
        }
      );

      const data =
        await response.json();

      // The backend can return 400 when SMTP fails even though
      // Razorpay payment-link creation succeeded. Reload the
      // action and use the saved execution_result in that case.
      if (!response.ok) {
        const refreshedActions =
          await loadActions();

        const refreshedAction =
          refreshedActions.find(
            (item: AgentAction) =>
              item.id === actionId
          );

        const paymentLink =
          getPaymentLinkFromAction(
            refreshedAction || null
          );

        if (paymentLink && refreshedAction) {
          setError("");

          openPersonalizedMail(
            refreshedAction,
            paymentLink
          );

          return;
        }

        throw new Error(
          data.detail ||
            "Failed to approve action."
        );
      }

      // Keep the returned execution result visible immediately.
      if (data?.execution) {
        setExecutionResults(
          (previous) => ({
            ...previous,
            [actionId]:
              data.execution?.razorpay ||
              data.razorpay ||
              data.execution,
          })
        );
      }

      const refreshedActions =
        await loadActions();

      const refreshedAction =
        refreshedActions.find(
          (item: AgentAction) =>
            item.id === actionId
        );

      const paymentLink =
        data?.payment_link ||
        data?.execution?.payment_link ||
        data?.razorpay?.short_url ||
        data?.execution?.razorpay?.short_url ||
        getPaymentLinkFromAction(
          refreshedAction || null
        );

      if (refreshedAction && paymentLink) {
        openPersonalizedMail(
          refreshedAction,
          paymentLink
        );
      }

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to approve action."
      );
    } finally {
      setProcessingId(null);
    }
  }

  // =====================================================
  // REJECT
  // =====================================================

  async function rejectAction(
    actionId: number
  ) {
    try {
      setProcessingId(actionId);
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/agent-actions/${actionId}/reject`,
        {
          method: "POST",
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to reject action."
        );
      }

      await loadActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reject action."
      );
    } finally {
      setProcessingId(null);
    }
  }

  // =====================================================
  // EXECUTE
  // =====================================================

  async function executeAction(
    actionId: number
  ) {
    try {
      setProcessingId(actionId);
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/agent-actions/${actionId}/execute`,
        {
          method: "POST",
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to execute action."
        );
      }

      if (data?.razorpay) {
        setExecutionResults(
          (previous) => ({
            ...previous,
            [actionId]:
              data.razorpay,
          })
        );
      }

      await loadActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to execute action."
      );
    } finally {
      setProcessingId(null);
    }
  }

  // =====================================================
  // PERSONALIZED CUSTOMER MESSAGE
  // =====================================================

  function getPersonalizedCustomerMessage(
    action: AgentAction
  ) {
    const customerName =
      action.customer?.name ||
      "there";

    const productName =
      action.product?.name ||
      "this product";

    const finalAmount =
      Number(
        action.offer?.final_amount ||
        action.action_amount ||
        0
      );

    const actionType =
      normalizedStatus(
        action.action_type
      );

    const discountPercentage =
      Number(
        action.offer?.discount_percentage ||
        0
      );

    if (actionType === "cross_sell") {

      const originalAmount =
        Number(
          action.offer?.original_amount ||
          finalAmount ||
          0
        );

      const discountAmount =
        Number(
          action.offer?.discount_amount ||
          0
        );

      const offerLine =
        discountPercentage > 0
          ? `We've unlocked a special ${discountPercentage}% discount for you. Your personalized price is ${money(finalAmount)}, down from ${money(originalAmount)} — you save ${money(discountAmount)}.`
          : `We've selected a personalized price of ${money(finalAmount)} for you.`;

      return `Hi ${customerName},

We noticed your recent purchase activity and thought ${productName} would be a great addition to what you've already picked up.

It's a recommendation selected specifically for you based on your recent shopping activity.

${offerLine}

You can complete your purchase securely using the payment link below.

Best,
MUNEEM`;
    }

    if (actionType === "upsell") {

      return `Hi ${customerName},

You've already shown interest in our products, so we thought you might be ready for ${productName}.

MUNEEM selected this as a next-step recommendation based on your purchase activity.

Your personalized price is ${money(finalAmount)}.

You can complete your purchase securely using the payment link below.

Best,
MUNEEM`;
    }

    if (
      actionType === "repeat_purchase" ||
      actionType === "reorder"
    ) {

      return `Hi ${customerName},

It looks like you may be ready for your next purchase.

MUNEEM selected ${productName} for you based on your previous shopping activity.

Your personalized price is ${money(finalAmount)}.

You can complete your purchase securely using the payment link below.

Best,
MUNEEM`;
    }

    if (
      actionType === "reengage"
    ) {

      return `Hi ${customerName},

We haven't seen you in a while, and MUNEEM found something that may be worth a look.

We thought ${productName} could be a great reason to come back.

Your personalized price is ${money(finalAmount)}.

You can complete your purchase securely using the payment link below.

Best,
MUNEEM`;
    }

    return `Hi ${customerName},

We found something we think you'll like: ${productName}.

MUNEEM selected this recommendation based on your recent shopping activity.

Your personalized price is ${money(finalAmount)}.

You can complete your purchase securely using the payment link below.

Best,
MUNEEM`;
  }

  // =====================================================
  // COPY PAYMENT LINK
  // =====================================================

  async function copyPaymentLink(
    actionId: number,
    link: string
  ) {
    try {

      await navigator.clipboard.writeText(
        link
      );

      setCopiedActionId(
        actionId
      );

      window.setTimeout(() => {
        setCopiedActionId(
          (current) =>
            current === actionId
              ? null
              : current
        );
      }, 2000);

    } catch {

      setError(
        "Could not copy the payment link."
      );
    }
  }

  // =====================================================
  // HELPERS
  // =====================================================

  function money(
    value: number | null | undefined
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

  function formatActionType(
    value: string
  ) {
    return value
      .replace(
        /_/g,
        " "
      )
      .toLowerCase()
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  }

  function formatStatus(
    value: string
  ) {
    return value
      .replace(
        /_/g,
        " "
      )
      .toLowerCase()
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  }

  function normalizedStatus(
    value: string
  ) {
    return String(
      value || ""
    )
      .toLowerCase()
      .trim();
  }

  function isApprovalRequired(
    action: AgentAction
  ) {
    return (
      action.approval_required ===
        true ||
      Number(
        action.approval_required
      ) === 1
    );
  }

  function getCustomerName(
    action: AgentAction
  ) {
    return (
      action.customer?.name ||
      "Customer"
    );
  }

  function getProductName(
    action: AgentAction
  ) {
    return (
      action.product?.name ||
      "Recommended product"
    );
  }

  function getActionTitle(
    action: AgentAction
  ) {

    const customer =
      getCustomerName(action);

    const product =
      getProductName(action);

    const type =
      normalizedStatus(
        action.action_type
      );

    if (
      type === "reengage"
    ) {
      return `${customer} may be ready to return`;
    }

    return `${customer} may be ready for ${product}`;
  }

  function getActionDescription(
    action: AgentAction
  ) {

    const customer =
      getCustomerName(action);

    const product =
      getProductName(action);

    const type =
      normalizedStatus(
        action.action_type
      );

    if (
      type === "cross_sell"
    ) {
      return `${customer} recently purchased from your store. MUNEEM identified ${product} as a relevant next purchase.`;
    }

    if (
      type === "upsell"
    ) {
      return `MUNEEM identified a higher-value ${product} opportunity for ${customer}.`;
    }

    if (
      type === "reengage"
    ) {
      return `MUNEEM identified ${customer} as a customer worth bringing back.`;
    }

    return `MUNEEM identified a revenue opportunity for ${customer}.`;
  }

  // =====================================================
  // METRICS
  // =====================================================

  const pendingActions =
    actions.filter(
      (action) =>
        normalizedStatus(
          action.status
        ) ===
        "pending_approval"
    );

  const approvedActions =
    actions.filter(
      (action) =>
        normalizedStatus(
          action.status
        ) === "approved"
    );

  const executedActions =
    actions.filter(
      (action) =>
        normalizedStatus(
          action.status
        ) === "executed"
    );

  const opportunityValue =
    actions.reduce(
      (
        sum,
        action
      ) =>
        sum +
        Number(
          action.offer
            ?.final_amount ||
          action.action_amount ||
          0
        ),
      0
    );

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <div className="agent-state">

        <span>
          06 / MUNEEM
        </span>

        <h1>
          Reading
          <br />
          <em>
            the signals.
          </em>
        </h1>

      </div>
    );
  }

  // =====================================================
  // PAGE
  // =====================================================

  return (
    <div className="agent-page">

      {/* =================================================
          HERO
      ================================================= */}

      <section className="agent-hero">

        <div className="agent-meta">

          <span>
            06 / MUNEEM
          </span>

          <span>
            REVENUE OPERATIONS
          </span>

        </div>

        <div className="agent-hero-grid">

          <div className="agent-title">

            <p>
              DECISIONS WORTH MAKING
            </p>

            <h1>
              Revenue
              <br />
              <em>
                in motion.
              </em>
            </h1>

          </div>

          <div className="agent-description">

            <strong>
              MUNEEM IS WATCHING
            </strong>

            <p>
              MUNEEM finds revenue
              opportunities, recommends
              the right action and keeps
              the final decision with you
              whenever approval is required.
            </p>

          </div>

          <div className="agent-summary">

            <div>
              <span>
                OPEN
              </span>

              <strong>
                {pendingActions.length}
              </strong>
            </div>

            <div>
              <span>
                EXECUTED
              </span>

              <strong>
                {executedActions.length}
              </strong>
            </div>

          </div>

        </div>

      </section>

      {/* =================================================
          ERROR
      ================================================= */}

      {error && (
        <div className="agent-error">

          <span>
            !
          </span>

          <p>
            {error}
          </p>

        </div>
      )}

      {/* =================================================
          OVERVIEW
      ================================================= */}

      <section className="agent-overview">

        <div className="agent-section-number">
          01
        </div>

        <div className="agent-section-heading">

          <span>
            MUNEEM CONTROL
          </span>

          <h2>
            From signal
            <br />
            to <em>action.</em>
          </h2>

          <p>
            Every recommendation follows
            a clear path before it can affect
            your business.
          </p>

        </div>

        <div className="agent-metrics">

          <div className="agent-metric">

            <span>
              OPPORTUNITY VALUE
            </span>

            <strong>
              {money(
                opportunityValue
              )}
            </strong>

            <p>
              Potential value attached to
              the actions currently recorded.
            </p>

          </div>

          <div className="agent-metric">

            <span>
              ACTION PIPELINE
            </span>

            <div className="agent-pipeline">

              <div>
                <strong>
                  {pendingActions.length}
                </strong>

                <span>
                  REVIEW
                </span>
              </div>

              <div>
                <strong>
                  {approvedActions.length}
                </strong>

                <span>
                  APPROVED
                </span>
              </div>

              <div>
                <strong>
                  {executedActions.length}
                </strong>

                <span>
                  DONE
                </span>
              </div>

            </div>

          </div>

        </div>

      </section>

      {/* =================================================
          ACTION QUEUE
      ================================================= */}

      <section className="agent-queue">

        <div className="agent-section-number">
          02
        </div>

        <div className="agent-section-heading">

          <span>
            ACTION QUEUE
          </span>

          <h2>
            Revenue
            <br />
            opportunities
            <br />
            <em>
              worth acting on.
            </em>
          </h2>

        </div>

        <div className="agent-queue-content">

          <div className="agent-queue-top">

            <div>

              <span>
                LIVE QUEUE
              </span>

              <strong>
                {actions.length}{" "}
                {actions.length === 1
                  ? "OPPORTUNITY"
                  : "OPPORTUNITIES"}
              </strong>

            </div>

            <button
              className="agent-refresh"
              onClick={loadActions}
              disabled={
                processingId !== null
              }
            >
              REFRESH
              <span>
                ↻
              </span>
            </button>

          </div>

          {actions.length === 0 ? (

            <div className="agent-empty">

              <span>
                QUEUE CLEAR
              </span>

              <h3>
                Nothing needs your
                attention.
              </h3>

              <p>
                MUNEEM will surface a
                recommendation when a
                revenue opportunity appears.
              </p>

            </div>

          ) : (

            <div className="agent-list">

              {actions.map(
                (
                  action,
                  index
                ) => {

                  const status =
                    normalizedStatus(
                      action.status
                    );

                  const isPending =
                    status ===
                    "pending_approval";

                  const isApproved =
                    status ===
                    "approved";

                  const isExecuted =
                    status ===
                    "executed";

                  const isRejected =
                    status ===
                    "rejected";

                  const isBlocked =
                    status ===
                    "blocked";

                  const isProcessing =
                    processingId ===
                    action.id;

                  const execution =
                    executionResults[
                      action.id
                    ];

                  const customerName =
                    getCustomerName(
                      action
                    );

                  const productName =
                    getProductName(
                      action
                    );

                  const originalAmount =
                    Number(
                      action.offer
                        ?.original_amount ||
                      action.action_amount ||
                      0
                    );

                  const discountPercentage =
                    Number(
                      action.offer
                        ?.discount_percentage ||
                      0
                    );

                  const discountAmount =
                    Number(
                      action.offer
                        ?.discount_amount ||
                      0
                    );

                  const finalAmount =
                    Number(
                      action.offer
                        ?.final_amount ||
                      action.action_amount ||
                      0
                    );

                  return (
                    <article
                      className="agent-row"
                      key={
                        action.id
                      }
                    >

                      <div className="agent-row-index">
                        {String(
                          index + 1
                        ).padStart(
                          2,
                          "0"
                        )}
                      </div>

                      <div className="agent-row-main">

                        <div className="agent-row-label">

                          <span>
                            {formatActionType(
                              action.action_type
                            )}
                          </span>

                          <div
                            className={`agent-status status-${status}`}
                          >
                            <i />

                            {formatStatus(
                              status
                            )}
                          </div>

                        </div>

                        <h3>
                          {getActionTitle(
                            action
                          )}
                        </h3>

                        <p>
                          {getActionDescription(
                            action
                          )}
                        </p>

                        {action.customer && (
                          <small>
                            {customerName}
                            {" · "}
                            {action.customer.email}
                          </small>
                        )}

                      </div>

                      <div className="agent-row-value">

                        <span>
                          CUSTOMER PAYS
                        </span>

                        <strong>
                          {money(
                            finalAmount
                          )}
                        </strong>

                        {discountPercentage >
                          0 && (
                          <small>
                            {money(
                              originalAmount
                            )}
                            {" · "}
                            {discountPercentage}% off
                          </small>
                        )}

                      </div>

                      <div className="agent-row-approval">

                        <span>
                          CONTROL
                        </span>

                        <strong>
                          {isApprovalRequired(
                            action
                          )
                            ? "Merchant approval"
                            : "Auto-approved"}
                        </strong>

                      </div>

                      <div className="agent-row-actions">

                        {isPending && (
                          <>
                            <button
                              className="agent-reject"
                              disabled={
                                isProcessing
                              }
                              onClick={() =>
                                rejectAction(
                                  action.id
                                )
                              }
                            >
                              {isProcessing
                                ? "..."
                                : "REJECT"}
                            </button>

                            <button
                              className="agent-approve"
                              disabled={
                                isProcessing
                              }
                              onClick={() =>
                                approveAction(
                                  action.id
                                )
                              }
                            >
                              {isProcessing
                                ? "..."
                                : "APPROVE →"}
                            </button>
                          </>
                        )}
                        {isApproved && (
                          <span className="agent-approved agent-awaiting">
                            {isProcessing
                              ? "SENDING..."
                              : "APPROVED — EMAIL PENDING"}
                          </span>
                        )}

                        {isExecuted && (
                          <span className="agent-executed">
                            ✓ EXECUTED
                          </span>
                        )}

                        {isRejected && (
                          <span className="agent-executed">
                            REJECTED
                          </span>
                        )}

                        {isBlocked && (
                          <span className="agent-executed">
                            BLOCKED BY POLICY
                          </span>
                        )}

                        {!isPending &&
                          !isApproved &&
                          !isExecuted &&
                          !isRejected &&
                          !isBlocked && (
                            <span className="agent-executed">
                              {formatStatus(
                                status
                              )}
                            </span>
                          )}

                      </div>

                      {/* =================================================
                          PERSONALIZED OFFER
                      ================================================= */}

                      {(action.customer ||
                        action.product) && (
                        <div className="agent-execution">

                          <div>

                            <span>
                              PERSONALIZED OFFER
                            </span>

                            <strong>
                              {customerName}
                              {" · "}
                              {productName}
                            </strong>

                          </div>

                          <div>

                            <div>
                              <span>
                                ORIGINAL
                              </span>

                              <strong>
                                {money(
                                  originalAmount
                                )}
                              </strong>
                            </div>

                            <div>
                              <span>
                                SAVING
                              </span>

                              <strong>
                                {money(
                                  discountAmount
                                )}
                              </strong>
                            </div>

                            <div>
                              <span>
                                FINAL PRICE
                              </span>

                              <strong>
                                {money(
                                  finalAmount
                                )}
                              </strong>
                            </div>

                          </div>

                        </div>
                      )}

                      {/* =================================================
                          CUSTOMER MESSAGE
                      ================================================= */}

                      {action.customer_message && (
                        <div className="agent-execution">

                          <div className="agent-message-heading">

                            <span>
                              MESSAGE TO{" "}
                              {customerName.toUpperCase()}
                            </span>

                            {isExecuted ? (
                              <span className="agent-mail-sent-label">
                                ✓ EMAIL SENT
                              </span>
                            ) : (
                              <span className="agent-mail-sent-label agent-mail-muted">
                                SENDS AUTOMATICALLY ON APPROVAL
                              </span>
                            )}

                          </div>

                          <p>
                            {
                              getPersonalizedCustomerMessage(
                                action
                              )
                            }
                          </p>

                        </div>
                      )}

                      {/* =================================================
                          PAYMENT
                      ================================================= */}

                      {execution && (
                        <div className="agent-execution agent-payment">

                          <div>

                            <span>
                              PAYMENT LINK READY
                            </span>

                            <strong>
                              {money(
                                Number(
                                  execution.amount ||
                                  finalAmount
                                )
                              )}
                            </strong>

                          </div>

                          <div className="agent-payment-actions">

                            {execution.short_url && (
                              <a
                                href={
                                  execution.short_url
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                OPEN PAYMENT LINK →
                              </a>
                            )}

                            {execution.short_url && (
                              <button
                                className="agent-copy-link"
                                onClick={() =>
                                  copyPaymentLink(
                                    action.id,
                                    execution.short_url ||
                                      ""
                                  )
                                }
                              >
                                {copiedActionId ===
                                action.id
                                  ? "LINK COPIED"
                                  : "COPY LINK"}
                              </button>
                            )}

                            {copiedActionId ===
                              action.id && (
                              <span className="agent-copy-toast">
                                Link copied
                              </span>
                            )}

                          </div>

                        </div>
                      )}

                    </article>
                  );
                }
              )}

            </div>

          )}

        </div>

      </section>

      {/* =================================================
          SEND HISTORY
      ================================================= */}

      <section className="agent-send-history">

        <div className="agent-section-number">
          03
        </div>

        <div className="agent-section-heading">
          <span>SEND HISTORY</span>

          <h2>
            Offers
            <br />
            <em>already sent.</em>
          </h2>

          <p>
            A persistent record of every customer offer
            MUNEEM has successfully sent.
          </p>
        </div>

        <div className="agent-history-content">

          <div className="agent-history-top">
            <div>
              <span>OUTBOUND ACTIVITY</span>
              <strong>
                {actions.filter(
                  (action) =>
                    normalizedStatus(action.status) ===
                    "executed"
                ).length}{" "}
                SENT
              </strong>
            </div>

            <span className="agent-history-live">
              LIVE FROM MUNEEM
            </span>
          </div>

          {actions.filter(
            (action) =>
              normalizedStatus(action.status) ===
              "executed"
          ).length === 0 ? (

            <div className="agent-history-empty">
              <span>NO SENT OFFERS</span>
              <h3>
                Your outbound history is clear.
              </h3>
              <p>
                Approved offers will appear here once
                MUNEEM successfully sends them.
              </p>
            </div>

          ) : (

            <div className="agent-history-list">

              {actions
                .filter(
                  (action) =>
                    normalizedStatus(action.status) ===
                    "executed"
                )
                .map((action) => {

                  const email =
                    parseEmailResult(
                      action.execution_result
                    );

                  const sentAt =
                    email?.sent_at ||
                    action.updated_at ||
                    action.created_at;

                  return (
                    <article
                      className="agent-history-card"
                      key={`sent-${action.id}`}
                    >

                      <div className="agent-history-icon">
                        ✓
                      </div>

                      <div className="agent-history-main">

                        <div className="agent-history-title">
                          <strong>
                            {getCustomerName(action)}
                          </strong>

                          <span>
                            OFFER SENT
                          </span>
                        </div>

                        <p>
                          {getProductName(action)}
                          {" · "}
                          {money(
                            Number(
                              action.offer?.final_amount ||
                              action.action_amount ||
                              0
                            )
                          )}
                        </p>

                        <small>
                          {email?.to ||
                            action.customer?.email ||
                            "Customer email unavailable"}
                        </small>

                      </div>

                      <div className="agent-history-meta">

                        <span>
                          {email?.provider
                            ? `${email.provider.toUpperCase()} · `
                            : ""}
                          {sentAt
                            ? new Date(sentAt).toLocaleString(
                                "en-IN",
                                {
                                  day: "2-digit",
                                  month: "short",
                                  year: "numeric",
                                  hour: "2-digit",
                                  minute: "2-digit",
                                }
                              )
                            : "Recently"}

                        </span>

                        <strong>
                          ACTION #{action.id}
                        </strong>

                      </div>

                    </article>
                  );
                })}

            </div>
          )}

        </div>

      </section>

      {/* =================================================
          MUNEEM LOOP
      ================================================= */}

      <section className="agent-insight">

        <div className="agent-section-number">
          04
        </div>

        <div>

          <span className="agent-insight-label">
            THE MUNEEM LOOP
          </span>

          <h2>
            See it.
            <br />
            Decide it.
            <br />
            <em>
              Recover it.
            </em>
          </h2>

        </div>

        <div className="agent-insight-copy">

          <p>
            MUNEEM follows one simple
            loop: identify a revenue
            signal, recommend an action,
            apply merchant controls,
            execute when permitted,
            then track the outcome.
          </p>

          <div className="agent-loop">

            <div>
              <strong>
                01
              </strong>

              <span>
                IDENTIFY
              </span>
            </div>

            <div>
              <strong>
                02
              </strong>

              <span>
                APPROVE
              </span>
            </div>

            <div>
              <strong>
                03
              </strong>

              <span>
                EXECUTE
              </span>
            </div>

            <div>
              <strong>
                04
              </strong>

              <span>
                RECOVER
              </span>
            </div>

          </div>

        </div>

      </section>

      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="agent-footer">

        <div>
          DETECT
        </div>

        <div>
          DECIDE
        </div>

        <div>
          SEND
        </div>

        <div>
          RECOVER
        </div>

        <span>
          MUNEEM · MERCHANT CONSOLE · 2026
        </span>

      </footer>

    </div>
  );
}

export default AgentActions;