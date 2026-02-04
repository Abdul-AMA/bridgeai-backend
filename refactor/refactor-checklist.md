# Refactor Checklist (Strict Order)

---------------------------------------------------
Milestone 1 — Permission Service Extraction
---------------------------------------------------
1. Create app/services/permission_service.py.
2. Move all permission checks from:
   - auth.py
   - projects.py
   - chats.py
   - crs.py
   - teams.py
3. Replace inline checks with service calls.
4. Run all authorization-related tests.
5. Stop and wait for next instruction.

---------------------------------------------------
Milestone 2 — Repository Layer
---------------------------------------------------
1. Create app/repositories/ with:
   - ProjectRepository
   - TeamRepository
   - CRSRepository
   - UserRepository
2. Move all direct db.query() calls from routes and services.
3. Make services depend on repositories.
4. Run all tests related to modules modified.
5. Stop and wait for next instruction.

---------------------------------------------------
Milestone 3 — Split Oversized API Modules
---------------------------------------------------
1. Split crs.py into 4 modules.
2. Split teams.py into 3 modules.
3. Split chats.py into 2 modules.
4. Expose router objects via __init__.py for backward compatibility.
5. Run routing tests + relevant functional tests.
6. Stop and wait for next instruction.

---------------------------------------------------
Milestone 4 — Service Layer Expansion
---------------------------------------------------
1. Create missing services:
   - project_service.py
   - team_service.py
   - auth_service.py
   - file_storage_service.py
2. Move all business logic out of routes.
3. Routes call services only.
4. Run relevant tests.
5. Stop and wait for next instruction.

---------------------------------------------------
Milestone 5 — Notification Standardization
---------------------------------------------------
1. Replace all ad-hoc notification logic with notification_service usage.
2. Normalize DB commit behavior.
3. Run notification tests.
4. Stop and wait for next instruction.

---------------------------------------------------
Milestone 6 — Exception + Validation Review
---------------------------------------------------
1. Add domain exceptions in app/exceptions/.
2. Move validation logic into validators/.
3. Move inline schemas into schemas/.
4. Run tests.
5. Stop and wait for next instruction.

---------------------------------------------------
Milestone 7 — CRS/Comment Services Review
---------------------------------------------------
1. Decide whether to adapt existing CRS and Comment services to repositories.
2. Refactor if beneficial.
3. Run CRS/comment tests.
4. Stop and wait for next instruction.

---------------------------------------------------
Milestone 8 — Final Test Pass
---------------------------------------------------
1. Run all tests.
2. Confirm zero regressions.
3. Produce final summary and cleaned folder structure.
