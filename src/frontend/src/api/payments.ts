const API_URL = "http://127.0.0.1:8000";

export async function createPayment(orderId: number) {
  const response = await fetch(
    `${API_URL}/payments/create/${orderId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();

    throw new Error(
      error.detail || "Failed to create payment"
    );
  }

  return response.json();
}


export async function verifyPayment(data: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  transaction_id: number;
}) {
  const params = new URLSearchParams({
    razorpay_order_id: data.razorpay_order_id,
    razorpay_payment_id: data.razorpay_payment_id,
    razorpay_signature: data.razorpay_signature,
    transaction_id: String(data.transaction_id),
  });

  const response = await fetch(
    `${API_URL}/payments/verify?${params.toString()}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const error = await response.json();

    throw new Error(
      error.detail || "Payment verification failed"
    );
  }

  return response.json();
}