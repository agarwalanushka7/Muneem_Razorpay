Phase 1 — Project Foundation & Merchant Entry
Objective

Create the basic working application foundation and establish the merchant entry point.

Requirements
Application starts successfully.
Frontend loads.
Backend starts.
Frontend and backend communicate.
Merchant has a working login page.
Login follows Design.md.
Basic authentication structure exists.
Configuration is loaded through environment variables.
Frontend and backend remain cleanly separated.
Phase 1 does NOT implement
AI Revenue Agent
Product catalog management
Customer management
AI recommendations
Upselling
Cross-selling
Conversational commerce
Razorpay payment processing
Campaigns
Audit dashboard
Advanced analytics
Phase 1.1 — Backend Foundation
Tasks

Create the backend application entry point.

Requirements
FastAPI application
Basic application configuration
Environment variable loading
Health-check endpoint
CORS configuration for local frontend development
Basic error-handling structure
Expected endpoint
GET /health
Acceptance Criteria
[ ] FastAPI starts successfully
[ ] /health returns 200
[ ] Environment variables load correctly
[ ] CORS allows local frontend
[ ] Basic errors return structured responses
Phase 1.2 — Frontend Foundation
Tasks

Create the frontend application foundation.

Requirements
React application
Vite development environment
Design system integration
Basic routing structure
Frontend environment configuration
Backend API communication
Acceptance Criteria
[ ] Frontend starts successfully
[ ] Login page loads
[ ] Frontend can call backend
[ ] Backend response is received
[ ] No hardcoded backend architecture
Phase 1.3 — Merchant Authentication
Tasks

Create the merchant entry flow.

Requirements
Merchant login page
Email field
Password field
Sign-in button
Login validation
Backend authentication endpoint
Invalid credential handling
Loading state
Authentication error state
Expected endpoint
POST /auth/login
Acceptance Criteria
[ ] Valid merchant credentials are accepted
[ ] Invalid credentials are rejected
[ ] Appropriate error message appears
[ ] Loading state works
[ ] Frontend communicates with backend
Phase 1.4 — Phase 1 Validation

Before moving forward:

Test
Backend startup
Frontend startup
Health endpoint
Frontend → Backend communication
Login success
Login failure
Environment configuration
CORS
Completion condition

Phase 1 is complete only when all acceptance criteria pass.

Phase 2 — Merchant Dashboard Foundation
Objective

After successful authentication, establish the main merchant workspace.

The merchant should have a clear overview of their business and access to the core AI Revenue Agent functionality.

Tasks

Create:

Merchant dashboard
Navigation structure
Sidebar/navigation menu
Header
Merchant profile area
Dashboard content structure
Logout functionality
Dashboard sections

The dashboard should provide the foundation for:

Overview
Revenue
Customers
Products
AI Revenue Agent
Recommendations
Campaigns
Analytics
Settings

Only sections belonging to the current implementation phase should be functional.

Later functionality should remain clearly marked as unavailable or be excluded from the interface according to Design.md.

Acceptance Criteria
[ ] Merchant can reach dashboard after login
[ ] Dashboard layout follows Design.md
[ ] Navigation works
[ ] Logout works
[ ] Merchant session state is handled
[ ] Dashboard is responsive
Phase 3 — Merchant Business Data Foundation
Objective

Give the system the merchant data required for intelligent revenue analysis.

Product Management

Create the basic merchant product system.

Product information

Depending on PRD.md:

Product name
Description
Price
Category
Inventory information
Product status
Relevant metadata
Customer Data

Create the basic customer data structure.

Customer information
Customer identifier
Basic customer information
Purchase history
Order information
Relevant behavioral data
Backend

Create:

Product APIs
Customer APIs
Order/data structures
Database models
Repositories
Services
Acceptance Criteria
[ ] Merchant products can be represented
[ ] Customer data can be represented
[ ] Product data can be retrieved
[ ] Customer data can be retrieved
[ ] Backend structure follows Architecture.md
Phase 4 — Revenue Intelligence Foundation
Objective

Introduce the intelligence layer that analyzes merchant business data.

The system should begin turning raw business information into useful revenue insights.

Core functionality

Analyze:

Sales
Revenue
Products
Customers
Purchase behavior
Product performance
Trends
Revenue insights

Examples of insights the system may generate according to the PRD:

Revenue trends
Top-performing products
Underperforming products
Customer purchasing patterns
Potential revenue opportunities
Important boundary

The AI must not invent business data.

AI outputs must be based on available merchant data.

If required data is unavailable, the system must clearly communicate that limitation.

Acceptance Criteria
[ ] Merchant data can be analyzed
[ ] Revenue insights can be generated
[ ] Insights reference available data
[ ] Missing data is handled safely
[ ] AI does not fabricate metrics
Phase 5 — AI Revenue Agent
Objective

Introduce the core AI Revenue Agent.

The agent becomes the merchant's intelligent assistant for identifying and acting on revenue opportunities.

Core capabilities

The AI Revenue Agent should be able to:

Understand merchant questions
Analyze available business data
Identify revenue opportunities
Explain recommendations
Provide actionable suggestions
Reference the underlying data
Handle unsupported questions safely
Example interactions
Which products are performing best?

Which products are losing sales?

What should I promote this week?

Which customers are most likely to buy again?

Where am I losing revenue?

What can I do to increase revenue?
AI boundaries

The agent must:

Avoid fabricated data
Avoid unsupported claims
Clearly distinguish facts from recommendations
Explain uncertainty
Use available merchant data
Respect Rules.md
Acceptance Criteria
[ ] Merchant can communicate with AI agent
[ ] Agent understands merchant context
[ ] Agent uses available business data
[ ] Agent produces actionable insights
[ ] Unsupported requests are handled safely
Phase 6 — Recommendations, Upselling & Cross-Selling
Objective

Use merchant and customer data to identify opportunities for increasing revenue.

Recommendation Engine

The system should identify relevant:

Product recommendations
Upselling opportunities
Cross-selling opportunities
Customer-product relationships
Examples
Customer bought:
Laptop

Potential cross-sell:
Laptop bag
Wireless mouse
Keyboard

Or:

Customer is viewing:
Premium plan

Potential upsell:
Enterprise plan

Recommendations must be based on available data rather than arbitrary AI guesses.

Acceptance Criteria
[ ] Recommendations are generated
[ ] Recommendations use available data
[ ] Upsell opportunities are identifiable
[ ] Cross-sell opportunities are identifiable
[ ] Merchant can understand why recommendation was made
Phase 7 — Conversational Commerce
Objective

Extend the intelligence layer toward customer-facing conversational commerce.

Features

Depending on the PRD:

Customer conversational interface
Product discovery
Product questions
Personalized recommendations
Guided purchasing
Context-aware conversations
Example
Customer:
I need a laptop for programming.

AI:
What is your approximate budget?

Customer:
Around ₹80,000.

AI:
Here are products matching your requirements...
Boundaries

The AI must not:

Invent products
Invent prices
Claim unavailable inventory
Misrepresent merchant policies
Complete actions without required confirmation
Phase 8 — Razorpay Payment Integration
Objective

Integrate payment functionality only after the commerce and merchant systems are stable.

Features

Depending on PRD:

Payment initiation
Payment status
Payment confirmation
Transaction records
Payment error handling
Razorpay integration
Security

Sensitive credentials must come from environment variables.

Never expose:

API secrets
Private keys
Payment credentials

to the frontend.

Acceptance Criteria
[ ] Payment flow works
[ ] Payment status is handled
[ ] Failed payments are handled
[ ] Secrets remain server-side
[ ] Transactions are recorded correctly
Phase 9 — Campaigns & Revenue Actions
Objective

Allow merchants to act on AI-generated revenue opportunities.

Features

Potential capabilities:

Create campaigns
Select target customers
Select products
Generate campaign suggestions
Campaign previews
Campaign status
Campaign history

AI can assist with:

Campaign idea
Target audience
Product selection
Messaging suggestions
Timing suggestions

The merchant remains in control of final actions.

Phase 10 — Analytics & Audit Dashboard
Objective

Provide merchants with deeper visibility into business performance and AI activity.

Analytics

Potential metrics:

Revenue
Orders
Conversion
Customer activity
Product performance
Campaign performance
AI recommendation performance
AI Audit

Track:

AI recommendations
Reason for recommendation
Data used
Merchant action
Outcome where measurable

The system should make AI behavior understandable rather than treating it as a black box.

Phase 11 — Production Hardening
Objective

Prepare the application for production-level reliability.

Tasks
Security
Authentication hardening
Secure secrets
Input validation
API security
Authorization
Rate limiting where required
Reliability
Error handling
Logging
Monitoring
Retry handling
API failure handling
Performance
Database optimization
API optimization
AI response optimization
Caching where justified
Testing
Unit tests
Integration tests
API tests
Frontend tests
AI behavior tests
Edge-case tests
Phase 12 — Final Buildathon Polish
Objective

Prepare the complete application for demonstration and judging.

Tasks
Final UI polish
Responsive design
Loading states
Empty states
Error states
Demo data
Demo workflow
Performance check
Final bug fixing
README
Deployment
Buildathon presentation
Final Demo Flow

The ideal demonstration should show:

Merchant Login
      ↓
Merchant Dashboard
      ↓
Business Overview
      ↓
AI Revenue Agent
      ↓
Revenue Opportunity
      ↓
Recommendation
      ↓
Upsell / Cross-sell
      ↓
Merchant Action
      ↓
Result / Analytics
Development Rules for All Phases
1. Sequential development

Never implement Phase N+1 while Phase N is incomplete.

2. Source of truth

Always check:

PRD.md
Architecture.md
Rules.md
Phases.md
Design.md
Memory.md

before making architectural changes.

3. No unnecessary features

Do not add features simply because they are technically interesting.

Build what the product requires.

4. No premature AI

AI should only be introduced when the required underlying merchant data and business logic exist.

5. No fabricated business data

The AI must not invent:

Revenue
Customers
Products
Inventory
Orders
Recommendations
Analytics
6. Merchant control

AI can recommend.

The merchant makes the final business decision.

7. Security

Secrets belong in environment variables.

Never place API keys or credentials in frontend code.

8. Error handling

Every major feature must have:

Loading state
Success state
Empty state
Error state

where applicable.

9. Maintainability

Keep:

API
Schema
Service
Repository
Model
UI

responsibilities separated according to Architecture.md.