# Rules.md

## 1. Purpose

This file defines the development rules and boundaries for the Razorpay AI Commerce project.

These rules apply to all implementation phases.

---

## 2. Source of Truth

The six project files are the source of truth:

1. PRD.md
2. Architecture.md
3. Rules.md
4. Phases.md
5. Design.md
6. Memory.md

No implementation decision should knowingly contradict these files.

If two files conflict, stop implementation and resolve the conflict before proceeding.

---

## 3. Development Rules

### 3.1 Build Only the Current Phase

Only implement functionality explicitly assigned to the current phase in Phases.md.

Do not implement future-phase features early.

### 3.2 Avoid Unnecessary Dependencies

Do not add a library merely because it is convenient.

Every dependency should have a clear purpose.

Prefer existing project dependencies where possible.

### 3.3 Keep Components Modular

Separate:

- UI
- API communication
- Business logic
- AI logic
- Database access
- Payment operations
- Validation
- Audit logging

Do not place the entire application logic inside one file.

---

## 4. Environment Variables

Secrets must never be hardcoded.

Sensitive configuration must use environment variables.

Examples:

DATABASE_URL
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
AI_API_KEY
JWT_SECRET

The `.env` file must never be committed to Git.

`.env.example` may contain variable names but must not contain real credentials.

---

## 5. AI Rules

The AI is an assistant and decision-making layer, not an unrestricted system administrator.

The AI may:

- Analyze permitted merchant data
- Search the merchant catalog
- Recommend products
- Generate explanations
- Identify revenue opportunities
- Suggest permitted actions

The AI must not:

- Invent products
- Invent prices
- Invent inventory
- Invent payment status
- Override merchant policies
- Access unauthorized data
- Expose secrets
- Directly bypass backend validation
- Perform unrestricted financial operations

---

## 6. Financial Operations

All financial operations must pass through backend validation.

Required flow:

AI decision
→ backend validation
→ permission check
→ merchant policy check
→ financial operation
→ verification
→ database update
→ audit record

The AI must never directly execute unrestricted payment operations.

---

## 7. Payment Rules

Razorpay must be used through the backend.

Payment credentials must remain server-side.

The frontend must never contain:

- Razorpay secret keys
- Database credentials
- AI provider secret keys
- JWT signing secrets

The application must verify payment status before marking an order as successfully paid.

Never assume a payment succeeded merely because a payment request was created.

---

## 8. Order Rules

Order totals must be calculated server-side.

The client cannot be trusted to provide:

- Final price
- Discount amount
- Product availability
- Payment status

Before creating an order:

1. Validate product
2. Validate availability
3. Calculate price
4. Apply permitted discounts
5. Calculate final total
6. Create order
7. Initiate payment

---

## 9. AI Guardrails

AI actions must respect merchant-defined limits.

Examples:

- Maximum discount
- Maximum discount percentage
- Allowed products
- Required approval for sensitive actions

If an action violates a policy:

The action must be blocked or sent for approval.

The AI must never modify its own restrictions.

---

## 10. Error Handling

Errors must be handled explicitly.

Do not silently ignore exceptions.

Errors should:

- Be logged appropriately
- Return safe user-facing messages
- Avoid exposing secrets
- Preserve application state where possible
- Avoid duplicate financial operations

Never expose stack traces, API keys, database credentials, or internal secrets to users.

---

## 11. Payment Failure

A failed payment must never be represented as a successful order.

Possible payment states include:

- PENDING
- SUCCESS
- FAILED
- CANCELLED

The UI must communicate the actual payment state.

---

## 12. Audit Trail

Important AI and financial actions must be traceable.

Audit records should contain relevant information such as:

- Timestamp
- Actor
- Action
- Entity
- Reason
- Previous state
- New state
- Applied policy
- Result

Do not store sensitive credentials in audit records.

---

## 13. Data Isolation

A merchant must only be able to access their own business data.

Customer data must not be exposed to unauthorized users.

AI tools must receive only the data necessary for their task.

---

## 14. API Rules

API endpoints should:

- Validate input
- Authenticate protected requests
- Authorize access
- Return predictable responses
- Handle expected errors
- Avoid exposing internal implementation details

Business logic should remain in the service layer rather than being duplicated inside route handlers.

---

## 15. Frontend Rules

The frontend should:

- Follow Design.md
- Use reusable components
- Display loading states
- Display error states
- Display empty states
- Never contain secret credentials
- Never independently determine financial truth

The backend remains the source of truth for business and payment state.

---

## 16. Naming Rules

Use clear and consistent names.

Python:

- snake_case for variables and functions
- PascalCase for classes

TypeScript / React:

- camelCase for variables and functions
- PascalCase for components and types

Names should describe their purpose.

Avoid unnecessary abbreviations.

---

## 17. Code Quality

Code should be:

- Readable
- Modular
- Testable
- Consistent
- Explicit

Avoid:

- Giant files
- Duplicate logic
- Hardcoded business rules
- Unused dependencies
- Dead code
- Unnecessary abstractions

---

## 18. Testing

Each implemented feature should be tested before moving to the next phase.

At minimum, test:

- Expected successful flow
- Invalid input
- Relevant failure case
- Permission or policy boundary where applicable

---

## 19. Phase Completion

A phase is complete only when:

1. All phase tasks are implemented.
2. The application runs.
3. The defined acceptance criteria pass.
4. Relevant errors have been handled.
5. Memory.md is updated.

Do not mark a phase complete merely because the code has been written.

---

## 20. When Requirements Are Ambiguous

If an implementation decision would materially affect:

- Architecture
- Security
- Payments
- AI behavior
- Database structure
- User experience
- Dependencies

Stop and ask for clarification rather than making a major assumption.

Small implementation details may follow established project conventions.