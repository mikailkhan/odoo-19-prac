# UniSphere Architecture Decision Records (ADRs)

## ADR 001: Native Odoo 19 Platform vs. Decoupled PERN Architecture
- **Status:** Accepted
- **Context:** The team evaluated building a separate React/Express/FastAPI app communicating via REST/GraphQL vs. developing a native Odoo 19 addon.
- **Decision:** Build UniSphere as an idiomatic Odoo 19 module using Python ORM, declarative XML backend views, and QWeb portal templates.
- **Consequences:** Eliminates duplicated database schemas, custom JWT authentication layers, and manual CRUD endpoints. Utilizes Odoo's mature access control lists and automated database migration mechanisms.

---

## ADR 002: Addon Placement and Directory Strategy
- **Status:** Accepted
- **Context:** Odoo container mounts `./addons` to `/mnt/extra-addons`.
- **Decision:** Place all custom university models, security, views, and web controllers inside `addons/unisphere_university`.
- **Consequences:** Clean encapsulation, easy distribution, and zero contamination of core Odoo server code.

---

## ADR 003: User Identity Management
- **Status:** Accepted
- **Context:** Students and Faculty require contact details, profiles, and authentication credentials.
- **Decision:** Relate `unisphere.student` and `unisphere.faculty` to Odoo's core `res.partner` (contacts) and `res.users` (credentials) via `Many2one` relationships.
- **Consequences:** Avoids duplicating name, email, avatar, and phone fields. Integrates seamlessly with Odoo's authentication, email messaging, and portal capabilities.

---

## ADR 004: Dedicated Demonstration Fee Ledger (Option A)
- **Status:** Accepted
- **Context:** The university needs to demonstrate fee generation, student dues tracking, and payment verification. Odoo's full `account` module requires extensive chart-of-accounts and fiscal configuration.
- **Decision:** Implement a dedicated, lightweight UniSphere Fee Ledger (`unisphere.fee`) with clear status states (`draft`, `pending`, `paid`, `overdue`) and challan tracking.
- **Consequences:** Keeps the local demonstration lightweight, self-contained, and easy to run without requiring enterprise accounting setups. Can still be bridged to `account.move` if required in future releases.

---

## ADR 005: Security Boundaries via Record Rules
- **Status:** Accepted
- **Context:** Students must never view peers' grades, and faculty should only modify grades for their assigned course sections.
- **Decision:** Enforce authorization at the server level using Odoo `ir.rule` record rules rather than frontend UI conditional hiding.
- **Consequences:** Robust security that prevents unauthorized access even if request parameters or URLs are manipulated.
