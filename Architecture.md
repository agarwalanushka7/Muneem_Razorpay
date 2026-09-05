# Architecture.md

## 1. Architecture Overview

The application is a merchant-focused AI commerce platform.

The system has two primary experiences:

1. Merchant Console
2. Customer AI Commerce Experience

The Merchant Console is the primary application surface.

The Customer AI Commerce Experience allows customers to discover products, receive recommendations, build an order, and complete payment.

The architecture should keep business logic, AI logic, payment logic, data access, and UI concerns separated.

---

## 2. High-Level Application Flow

```text
Merchant
   ↓
Merchant Console
   ↓
Authentication
   ↓
Dashboard
   ↓
Products / Customers / AI Opportunities
   ↓
AI Revenue Agent
   ↓
Recommendation / Action
   ↓
Customer Commerce Experience
   ↓
Cart / Order
   ↓
Razorpay Test Payment
   ↓
Payment Result
   ↓
Transaction
   ↓
Audit Trail