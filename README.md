MUNEEM --- Agentic AI Revenue Intelligence

MUNEEM is an agentic AI revenue intelligence system for merchants.

It connects commerce data with an approval-controlled action workflow:

Revenue signal → Opportunity → Recommendation → Merchant approval →
Execution → Payment → Measurable revenue

What problem does MUNEEM solve?

Merchants already have customer, product, order, inventory, and
transaction data, but potential revenue opportunities often remain
hidden in that data.

MUNEEM turns that into a controlled workflow. It identifies revenue
opportunities, recommends an appropriate action, keeps the merchant in
control, executes approved actions through Razorpay, and tracks the
resulting payment outcome.

Instead of only saying:

"There is a revenue opportunity."

MUNEEM helps move the opportunity toward:

"Here is the opportunity, here is the recommended action, approve it,
and MUNEEM will execute the permitted action and measure the result."

Why is MUNEEM agentic AI?

MUNEEM operates across a multi-step workflow rather than only generating
text.

Perceive: understand customer, product, order, inventory, and
transaction context.

Reason: identify a revenue opportunity and an appropriate
action.

Recommend: present the action to the merchant.

Act: execute only after merchant approval.

Observe: obtain the current payment state from Razorpay.

Measure: record the outcome and calculate recovered revenue.

Core principle:

AI handles intelligence and recommendation; deterministic backend
services handle execution and payment operations.

Core workflow

Commerce Data
     |
     v
Opportunity Intelligence
     |
     v
Agent Recommendation
     |
     v
Merchant Approval
     |
     v
Action Executor
     |
     v
Razorpay Payment Link
     |
     v
Customer Payment
     |
     v
Payment Synchronization
     |
     v
Revenue + Audit + Dashboard

Key features

Commerce data

Customer records

Product records

Inventory context

Order history

Transaction values

Payment state

Revenue intelligence

Opportunity detection

Estimated opportunity value

Recommended revenue actions

Customer/product context

Agent action workflow

Pending approval

Merchant approval

Controlled execution

Execution result tracking

Payments

Razorpay Payment Links

Dynamic payment amounts

Payment status synchronization

Paid/pending state separation

Recovered revenue based on successful payments

Auditability

Opportunity/action history

Merchant approvals

Execution events

Payment outcomes

Business context attached to events

Architecture

                    +----------------------+
                    |    React Frontend    |
                    | Dashboard / Revenue  |
                    | Customers / Products |
                    | Orders / Actions     |
                    | Audit                |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |     FastAPI API       |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
       Opportunity       Agent Action       Payment
         Services          Services          Services
              |                |                |
              +----------------+----------------+
                               |
                               v
                       +---------------+
                       |   Database    |
                       +---------------+
                               |
                               v
                       +---------------+
                       |   Razorpay    |
                       +---------------+

Important state model

MUNEEM separates action state from payment state.

AgentAction

pending_approval
       ↓
approved
       ↓
executed

Payment

created / pending
       ↓
paid

These are different states.

An action can be:

AgentAction = executed
Payment     = pending

because MUNEEM successfully performed the permitted operation but the
customer has not paid yet.

After payment:

AgentAction = executed
Payment     = paid

Revenue definition

MUNEEM separates existing merchant revenue from revenue recovered
through MUNEEM actions.

Total revenue: value of recorded commerce orders.

Opportunity value: potential value identified by MUNEEM.

Recovered revenue: money associated with successfully paid
MUNEEM payment records.

A generated payment link or approved action is not treated as
recovered revenue.

Technology

Frontend

React

TypeScript

Vite

CSS

Backend

Python

FastAPI

SQLAlchemy

SQLite/database layer

Service/repository architecture

Payments

Razorpay Payment Links

Data

CSV-based commerce data ingestion

Database-backed customer/product/order/action/payment records

Main application areas

Dashboard --- merchant-level overview and MUNEEM pipeline

Revenue --- revenue, opportunity value, recovered revenue, and
action pipeline

Agent Actions --- review, approve, and execute recommended
actions

Customers --- customer commerce records

Products --- product and inventory records

Orders --- transaction ledger

Audit Log --- action, approval, execution, and payment history

Running the project

Backend

From the project root:

uvicorn src.backend.main:app --reload

API:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Frontend

From the frontend directory:

npm install
npm run dev

Application:

http://localhost:5173

Payment synchronization

MUNEEM uses:

POST /payments/sync

The synchronization process:

Finds MUNEEM actions containing payment information.

Gets the current payment-link state from Razorpay.

Updates the corresponding Payment record.

Stores current payment metadata in the execution result.

Keeps AgentAction.status separate from payment status.

Payment synchronization does not execute an agent action again.

Dynamic data

The application is database/API-driven.

The production flow should not depend on hardcoded: - customer names -
customer IDs - product IDs - prices - action IDs - payment amounts -
recommendations

Seed/demo data can be used for demonstration, but the application
operates on the records available through the backend.

Security and control model

MUNEEM is designed around bounded agency:

AI recommendation
       ↓
Merchant approval
       ↓
Deterministic execution
       ↓
External payment provider

The AI recommendation layer does not directly perform an external
payment operation.

Future improvements

Razorpay webhooks for event-driven payment synchronization

Stronger idempotency guarantees for external actions

More sophisticated opportunity scoring

Conversion feedback loops

More commerce platform integrations

Background job processing

Role-based merchant permissions

Production database and deployment infrastructure

Demo narrative

The strongest demonstration is:

Customer / Product / Order data
            ↓
Revenue opportunity
            ↓
Recommended action
            ↓
Merchant approval
            ↓
Razorpay payment link
            ↓
Customer payment
            ↓
Payment synchronization
            ↓
Recovered revenue
            ↓
Audit trail

MUNEEM turns revenue signals into controlled, measurable actions.