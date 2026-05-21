---
name: feedback_testing
description: Integration tests over mocks — prior incident where mock/prod divergence masked broken migration
metadata:
  type: feedback
---

Always write integration tests that hit a real database, not mocks.

**Why:** Team got burned last quarter when mocked tests passed but a prod migration failed. The mocks didn't reflect actual database constraints. This cost 2 days of incident response.

**How to apply:** When writing tests for anything that touches the database (queries, migrations, schema changes), use the test database instance. Only mock for pure business logic that has no DB interaction. Related: [[project_auth]] uses Drizzle migrations which MUST be tested against real Postgres.
