# UniSphere Future Enhancements & Deferred Scope

This document tracks features, optimizations, and integrations intentionally deferred to later phases or post-MVP development.

---

## 🔮 Roadmap & Deferred Features

### 1. Advanced Academic Scheduling & Room Conflict Engine
- **Current Scope:** Course Section defines classroom and schedule text strings.
- **Future Scope:** Implement a dedicated timetable conflict engine that detects double-booking of physical classrooms or instructors across intersecting timeslots using PostgreSQL range types or calendar intervals.

### 2. Multi-Campus / Multi-Company Support
- **Current Scope:** Single campus (Northstar University of Technology - Islamabad Main Campus).
- **Future Scope:** Leverage Odoo's native `res.company` multi-company features to support satellite campuses and branch colleges with distinct administrative oversight.

### 3. Integrated Online Fee Payment Gateways
- **Current Scope:** Demonstration fee ledger with challan reference and manual payment confirmation.
- **Future Scope:** Integrate with Odoo payment acquirers (Stripe, 1-Link, or bank wire reconciliation) for instantaneous student ledger clearance upon checkout.

### 4. Advanced Transcript PDF Generation
- **Current Scope:** On-screen gradebook and student portal grade table.
- **Future Scope:** QWeb PDF report engine generating official university transcripts with cryptographic QR code verification and registrar digital signatures.

### 5. Automated AI Academic Advisor (Phase 10)
- **Current Scope:** Deterministic mock assistant responding to rule-based queries regarding attendance, grades, and fee balances.
- **Future Scope:** LLM integration via OpenAI/Gemini API using strictly authorized server-side function calling, providing context-aware course advisement without data leakage.
