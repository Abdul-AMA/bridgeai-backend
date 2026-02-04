# General Architectural Rules
- Follow SOLID principles in every change.
- Maintain FastAPI best practices: routes → services → repositories → database.
- Do not change existing API behavior, payload formats, or URLs.
- Do not modify existing tests; all tests must pass after each milestone.
- All refactored code must be self-explanatory without excessive comments.
- Use clear, descriptive naming.
- Maintain backward compatibility for all imports during the refactor.

# Code Structure Rules
Use this directory layout:
app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    repositories/
    exceptions/
    validators/
    utils/

# Route Handler Rules
- Routes contain no business logic.
- Routes call services and return results.
- No database access allowed inside routes.

# Service Layer Rules
- Services encapsulate business logic and workflows.
- Services must not directly use db.session — rely on repositories.
- Services must be stateless and easy to unit-test.

# Repository Rules
- Repositories encapsulate all database queries.
- Repositories use SQLAlchemy models and sessions.
- Repositories expose clear, minimal methods.

# Validation Rules
- Inline validation must be moved to validators/.
- Inline Pydantic models must be moved to schemas/.

# Error Handling Rules
- Replace all raw HTTPException raises with domain exceptions.
- Domain exceptions live inside app/exceptions/.
- HTTPException translation happens in FastAPI exception handlers.

# Permission Rules
- Permission logic must only exist in permission_service.py.
- Remove all duplicated checks in routes and services.

# Notification Rules
- All notifications must be created using notification_service.py.
- Remove custom notification creation scattered across the API.

# Chat, CRS, and Teams Splitting Rules
Large modules must be split:
- CRS → crs_crud, crs_workflow, crs_versions, crs_export
- Teams → team_crud, team_members, team_dashboard
- Chats → chat_sessions, chat_websocket

# Testing Rules
After each milestone:
- Run only the tests related to the changed modules.
- Proceed to the next milestone only when all relevant tests pass.
