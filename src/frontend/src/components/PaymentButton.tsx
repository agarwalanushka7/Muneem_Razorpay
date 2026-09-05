import { useState } from "react";

interface PaymentButtonProps {
  orderId: number;
  amount: number;
}

interface RazorpayResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

interface PaymentData {
  success: boolean;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  order_id: number;
  transaction_id: number;
}

declare global {
  interface Window {
    Razorpay: any;
  }

  interface ImportMetaEnv {
    readonly VITE_RAZORPAY_KEY_ID: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const existingScript = document.querySelector(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
    );

    if (existingScript) {
      existingScript.addEventListener("load", () =>
        resolve(true)
      );

      existingScript.addEventListener("error", () =>
        resolve(false)
      );

      return;
    }

    const script = document.createElement("script");

    script.src =
      "https://checkout.razorpay.com/v1/checkout.js";

    script.async = true;

    script.onload = () => {
      resolve(true);
    };

    script.onerror = () => {
      resolve(false);
    };

    document.body.appendChild(script);
  });
}

export default function PaymentButton({
  orderId,
  amount,
}: PaymentButtonProps) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handlePayment = async () => {
    try {
      setLoading(true);
      setMessage("");

      // --------------------------------------------------
      // LOAD RAZORPAY CHECKOUT
      // --------------------------------------------------

      const razorpayLoaded =
        await loadRazorpayScript();

      if (!razorpayLoaded) {
        throw new Error(
          "Unable to load Razorpay Checkout."
        );
      }

      // --------------------------------------------------
      // CREATE PAYMENT ORDER
      // --------------------------------------------------

      const response = await fetch(
        `http://127.0.0.1:8000/payments/create/${orderId}`,
        {
          method: "POST",
        }
      );

      const data: PaymentData =
        await response.json();

      if (!response.ok) {
        throw new Error(
          (data as any).detail ||
            "Failed to create payment."
        );
      }

      // --------------------------------------------------
      // RAZORPAY CHECKOUT
      // --------------------------------------------------

      const options = {
        key:
          import.meta.env
            .VITE_RAZORPAY_KEY_ID,

        amount: data.amount,

        currency: data.currency,

        name: "Merchant Console",

        description:
          `Payment for Order #${orderId}`,

        order_id:
          data.razorpay_order_id,

        prefill: {
          name: "Customer",
          email: "customer@example.com",
        },

        theme: {
          color: "#111827",
        },

        handler: async (
          paymentResponse: RazorpayResponse
        ) => {
          try {
            setMessage(
              "Verifying payment..."
            );

            // ------------------------------------------------
            // VERIFY PAYMENT
            // ------------------------------------------------

            const verifyResponse =
              await fetch(
                "http://127.0.0.1:8000/payments/verify",
                {
                  method: "POST",

                  headers: {
                    "Content-Type":
                      "application/json",
                  },

                  body: JSON.stringify({
                    razorpay_order_id:
                      paymentResponse.razorpay_order_id,

                    razorpay_payment_id:
                      paymentResponse.razorpay_payment_id,

                    razorpay_signature:
                      paymentResponse.razorpay_signature,

                    transaction_id:
                      data.transaction_id,
                  }),
                }
              );

            const verifyData =
              await verifyResponse.json();

            if (!verifyResponse.ok) {
              throw new Error(
                verifyData.detail ||
                  "Payment verification failed."
              );
            }

            setMessage(
              "Payment successful and verified!"
            );
          } catch (error) {
            console.error(
              "Payment verification error:",
              error
            );

            setMessage(
              error instanceof Error
                ? error.message
                : "Payment verification failed."
            );
          }
        },

        modal: {
          ondismiss: () => {
            setMessage(
              "Payment cancelled."
            );
          },
        },
      };

      const razorpay =
        new window.Razorpay(options);

      razorpay.open();
    } catch (error) {
      console.error(
        "Payment error:",
        error
      );

      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to start payment."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        type="button"
        onClick={handlePayment}
        disabled={loading}
      >
        {loading
          ? "Processing..."
          : `Pay ₹${amount.toLocaleString(
              "en-IN"
            )}`}
      </button>

      {message && (
        <p>{message}</p>
      )}
    </div>
  );
}