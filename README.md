MUNEEM 💰

AI-Powered Revenue Intelligence for Merchants

MUNEEM helps merchants find missed revenue opportunities, recommend the right action, get merchant approval, execute through Razorpay, and track the actual payment outcome.

Detect → Recommend → Approve → Execute → Pay → Measure

✨ What MUNEEM Does

📊 Reads customer, product and order data

🤖 Detects potential revenue opportunities

💡 Recommends an action dynamically

👤 Keeps the merchant in control with approval

💳 Creates Razorpay payment links

🔄 Syncs actual payment status from Razorpay

📈 Tracks recovered revenue and execution history

🧾 Maintains an audit trail

The key idea

AI handles the intelligence.
The backend handles reliable execution.

🛠️ Tech Stack

Layer

Technology

Frontend

React + TypeScript + Vite

Backend

FastAPI + Python

Database

SQLite / SQLAlchemy

AI

LLM-based opportunity & recommendation flow

Payments

Razorpay

Styling

CSS

🚀 Run MUNEEM Locally

1. Download the project

Option A — Clone with Git

Open Command Prompt / Terminal and run:

git clone https://github.com/agarwalanushka7/Muneem_Razorpay.git
cd Muneem_Razorpay

Option B — Download ZIP

Open the GitHub repository.

Click Code → Download ZIP.

Extract the ZIP file.

Open the extracted Muneem_Razorpay folder in VS Code.

2. Backend Setup

Open a terminal inside the project folder:

cd src/backend

Create a virtual environment:

Windows

python -m venv venv
venv\Scripts\activate

macOS / Linux

python3 -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

3. Add Environment Variables

Create a .env file in the backend/project location expected by the application.

Add your Razorpay credentials:

RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

Never upload .env or your secret keys to GitHub.

4. Start the Backend

From the project root, run:

uvicorn src.backend.main:app --reload

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

5. Start the Frontend

Open a new terminal.

Go to the frontend:

cd src/frontend

Install packages:

npm install

Start the application:

npm run dev

Open the URL shown in the terminal, usually:

http://localhost:5173

📂 Project Structure

Muneem_Razorpay/
│
├── src/
│   ├── backend/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   │
│   └── frontend/
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   └── main.tsx
│       └── vite.config.ts
│
├── README.md
└── .gitignore

📥 Using Your Own Data

MUNEEM is designed to work with dynamic merchant data, rather than fixed customer or product examples.

A typical order dataset contains:

customer_name
customer_email
customer_phone
product_name
product_price
product_category
product_inventory
quantity
total_amount
order_date
order_status
payment_status

To use your own merchant data, provide the data in the format expected by the application's data/import flow.

After the data is loaded, MUNEEM can use the customer, product and order records to identify opportunities dynamically.

🔄 How the System Works

Customer / Order Data
        ↓
Opportunity Detection
        ↓
AI Recommendation
        ↓
Merchant Approval
        ↓
Razorpay Payment Link
        ↓
Customer Payment
        ↓
Payment Status Sync
        ↓
Recovered Revenue

Important

Approved/Executed does not automatically mean Paid.

MUNEEM keeps these states separate:

AgentAction.status → execution state

Payment.status → actual payment state

This prevents generated payment links from being incorrectly counted as recovered revenue.

💳 Payment Status Sync

MUNEEM can fetch the latest payment state from Razorpay through the payment synchronization endpoint:

POST /payments/sync

This updates the local payment record using the actual Razorpay payment-link status.

🔐 Security

Do not commit:

.env
.env.*
venv/
.venv/
node_modules/
__pycache__/

Never expose your Razorpay secret key or other API credentials.

🎯 Why MUNEEM?

Most systems stop at:

“Here is a revenue opportunity.”

MUNEEM goes one step further:

“Here is the opportunity → here is the recommended action → approve it → execute it → track the payment → measure the revenue.”

That closes the gap between revenue intelligence and revenue execution.

👩‍💻 Local Development Checklist

☐ Clone / download the repository
☐ Open the project in VS Code
☐ Create Python virtual environment
☐ Install backend requirements
☐ Add Razorpay credentials to .env
☐ Start FastAPI backend
☐ Install frontend dependencies
☐ Start React frontend
☐ Open localhost:5173

📌 Repository

MUNEEM — AI Revenue Intelligence for Merchants

Built for a Razorpay-focused buildathon.
