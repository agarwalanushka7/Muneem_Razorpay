import { useEffect, useState } from "react";
import PaymentButton from "../components/PaymentButton";
import "./Orders.css";

interface Order {
  id: number;
  customer_id: number;
  product_id: number;
  quantity: number;
  total_amount: number;
  status: string;
  payment_status: string;
  created_at: string;
}

function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchOrders();
  }, []);

  async function fetchOrders() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/orders/"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch orders");
      }

      const data = await response.json();

      setOrders(
        Array.isArray(data) ? data : []
      );
    } catch (err) {
      console.error("Orders error:", err);

      setError("Unable to load orders.");
    } finally {
      setLoading(false);
    }
  }

  function money(value: number) {
    return `₹${Number(value || 0).toLocaleString("en-IN")}`;
  }

  function formatDate(value: string) {
    if (!value) {
      return "Date unavailable";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Date unavailable";
    }

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function isPaid(paymentStatus: string) {
  const value = paymentStatus?.toLowerCase();

  return (
    value === "paid" ||
    value === "completed" ||
    value === "captured" ||
    value === "successful"
  );
}

  const totalValue = orders.reduce(
    (sum, order) =>
      sum + Number(order.total_amount || 0),
    0
  );

 const paidOrders = orders.filter((order) =>
  isPaid(order.payment_status)
).length;

  const pendingOrders =
    orders.length - paidOrders;

  return (
    <>
      {loading && (
        <div className="orders-state">
          <span>05 / MUNEEM</span>

          <h1>
            Reading
            <br />
            <em>orders.</em>
          </h1>
        </div>
      )}

      {!loading && error && (
        <div className="orders-state">
          <span>05 / MUNEEM</span>

          <h1>
            Orders
            <br />
            <em>unavailable.</em>
          </h1>

          <p>{error}</p>

          <button
            className="orders-retry"
            onClick={fetchOrders}
          >
            TRY AGAIN →
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className="orders-page">

          {/* =================================================
              HERO
              ================================================= */}

          <section className="orders-hero">

            <div className="orders-meta">
              <span>05 / MUNEEM</span>
              <span>ORDER MANAGEMENT</span>
            </div>

            <div className="orders-hero-grid">

              <div className="orders-title">

                <p>TRANSACTIONS IN MOTION</p>

                <h1>
                  Every sale
                  <br />
                  <em>counts.</em>
                </h1>

              </div>

              <div className="orders-description">

                <strong>ORDER ACTIVITY</strong>

                <p>
                  Track recorded purchases,
                  understand transaction value,
                  and recover revenue through
                  MUNEEM when payment is pending.
                </p>

              </div>

              <div className="orders-summary">

                <div>
                  <span>ORDERS</span>

                  <strong>
                    {orders.length}
                  </strong>
                </div>

                <div>
                  <span>VALUE</span>

                  <strong>
                    {totalValue >= 1000
                      ? `₹${Math.round(
                          totalValue / 1000
                        )}k`
                      : money(totalValue)}
                  </strong>
                </div>

              </div>

            </div>

          </section>


          {/* =================================================
              ORDER SNAPSHOT
              ================================================= */}

          <section className="orders-snapshot">

            <div className="orders-section-number">
              01
            </div>

            <div className="orders-section-heading">

              <span>ORDER SNAPSHOT</span>

              <h2>
                Where your
                <br />
                transactions{" "}
                <em>stand.</em>
              </h2>

              <p>
                A quick read of order volume,
                payment state, and transaction
                value.
              </p>

            </div>

            <div className="orders-metrics">

              <div className="order-metric">

                <span>
                  TOTAL ORDER VALUE
                </span>

                <strong>
                  {money(totalValue)}
                </strong>

                <p>
                  Combined value of recorded
                  orders.
                </p>

              </div>

              <div className="order-metric">

                <span>
                  PAYMENT STATUS
                </span>

                <div className="order-status-split">

                  <div>
                    <strong>
                      {paidOrders}
                    </strong>

                    <span>PAID</span>
                  </div>

                  <div>
                    <strong>
                      {pendingOrders}
                    </strong>

                    <span>PENDING</span>
                  </div>

                </div>

              </div>

            </div>

          </section>


          {/* =================================================
              ORDERS LIST
              ================================================= */}

          <section className="orders-list-section">

            <div className="orders-section-number">
              02
            </div>

            <div className="orders-section-heading">

              <span>TRANSACTION LEDGER</span>

              <h2>
                The orders
                <br />
                behind the{" "}
                <em>revenue.</em>
              </h2>

            </div>

            <div className="orders-table-wrapper">

              <div className="orders-table-top">

                <div>
                  <span>ORDER FLOW</span>

                  <strong>
                    {orders.length} RECORDED
                  </strong>
                </div>

                <button
                  className="orders-refresh"
                  onClick={fetchOrders}
                  disabled={loading}
                >
                  REFRESH DATA
                  <span>↻</span>
                </button>

              </div>

              <div className="orders-table">

                <div className="orders-table-header">

                  <span>NO.</span>

                  <span>ORDER</span>

                  <span>DETAILS</span>

                  <span>VALUE</span>

                  <span>STATUS</span>

                  <span>ACTION</span>

                </div>


                {orders.length === 0 ? (

                  <div className="orders-empty">

                    <span>
                      EMPTY LEDGER
                    </span>

                    <h3>
                      No orders yet.
                    </h3>

                    <p>
                      Recorded orders will
                      appear here once a
                      transaction is created.
                    </p>

                  </div>

                ) : (

                  orders.map(
                    (order, index) => {

                      const paid =
                        isPaid(order.payment_status);

                      return (
                        <article
                          className="order-row"
                          key={order.id}
                        >

                          {/* NUMBER */}

                          <div className="order-index">
                            {String(
                              index + 1
                            ).padStart(2, "0")}
                          </div>


                          {/* ORDER */}

                          <div className="order-identity">

                            <h3>
                              Order #{order.id}
                            </h3>

                            <p>
                              {formatDate(
                                order.created_at
                              )}
                            </p>

                          </div>


                          {/* DETAILS */}

                          <div className="order-details">

                            <div>
                              <span>
                                CUSTOMER
                              </span>

                              <strong>
                                #{order.customer_id}
                              </strong>
                            </div>

                            <div>
                              <span>
                                PRODUCT
                              </span>

                              <strong>
                                #{order.product_id}
                              </strong>
                            </div>

                            <div>
                              <span>
                                QTY
                              </span>

                              <strong>
                                {order.quantity}
                              </strong>
                            </div>

                          </div>


                          {/* VALUE */}

                          <div className="order-value">

                            <span>
                              AMOUNT
                            </span>

                            <strong>
                              {money(
                                order.total_amount
                              )}
                            </strong>

                          </div>


                          {/* STATUS */}

                          <div className="order-status">

                            <span
                              className={
                                paid
                                  ? "order-status-dot paid"
                                  : "order-status-dot"
                              }
                            />

                           <strong>
                             {order.payment_status ||
                                   "pending"}
                                  </strong>
                          </div>


                          {/* PAYMENT */}

                          <div className="order-payment">

                            <PaymentButton
                              orderId={order.id}
                              amount={
                                order.total_amount
                              }
                            />

                          </div>

                        </article>
                      );
                    }
                  )

                )}

              </div>

            </div>

          </section>


          {/* =================================================
              MUNEEM INSIGHT
              ================================================= */}

          <section className="orders-insight">

            <div className="orders-section-number">
              03
            </div>

            <div>

              <span className="orders-insight-label">
                MUNEEM PERSPECTIVE
              </span>

              <h2>
                A pending order
                <br />
                is still{" "}
                <em>revenue.</em>
              </h2>

            </div>

            <div className="orders-insight-copy">

              <p>
                MUNEEM treats every transaction
                as a potential revenue signal.
                Pending payments can be identified
                and acted on before the opportunity
                disappears.
              </p>

              <div className="orders-insight-stats">

                <div>

                  <strong>
                    {pendingOrders}
                  </strong>

                  <span>
                    PENDING ORDERS
                  </span>

                </div>

                <div>

                  <strong>
                    {money(totalValue)}
                  </strong>

                  <span>
                    RECORDED VALUE
                  </span>

                </div>

              </div>

            </div>

          </section>


          {/* =================================================
              FOOTER
              ================================================= */}

          <footer className="orders-footer">

            <div>ORDERS</div>

            <div>PAYMENTS</div>

            <div>REVENUE</div>

            <span>
              MUNEEM · MERCHANT CONSOLE · 2026
            </span>

          </footer>

        </div>
      )}
    </>
  );
}

export default Orders;