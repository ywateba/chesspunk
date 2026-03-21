Here is a detailed, prompt-ready roadmap designed specifically for "vibe coding" with an AI like Gemini 3.

You can copy-paste each "Sprint" block directly into your AI chat window to guide the development process step-by-step.

***

# Project Roadmap: Chess Community API
**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy (Async/Sync), Pydantic, SQLite (Dev) / PostgreSQL (Prod), Pytest.

---

## Sprint 1: Foundation, Database & Authentication
**Goal:** Establish the project structure, database connection, and secure user management system.

### Phase 1.1: Environment & Database Setup
* **Task:** Initialize a new Python project structure with `app/main.py`, `app/core/config.py`, and `app/db/session.py`.
* **Task:** Configure `SQLAlchemy` with a `Base` class and a dependency `get_db` to yield database sessions.
* **Task:** Install `alembic` and configure it to handle database migrations.
* **Task:** Create the `User` model in `app/models/user.py` with fields: `id`, `email` (unique), `username` (unique), `hashed_password`, `is_active`, `created_at`.
* **Test:** Create a test file `tests/test_db.py` to verify the database connection and table creation.

### Phase 1.2: Authentication System
* **Task:** Implement password hashing using `passlib[bcrypt]`. Add utility functions `verify_password` and `get_password_hash`.
* **Task:** Implement JWT token generation using `python-jose`. Create a configuration class to hold `SECRET_KEY` and `ALGORITHM`.
* **Task:** Create a Pydantic schema `UserCreate` (email, username, password) and `Token` (access_token, token_type).
* **Task:** Implement API endpoints:
    * `POST /auth/signup`: Registers a new user.
    * `POST /auth/login`: Validates credentials and returns a JWT.
* **Task:** Create a `get_current_user` dependency function that decodes the JWT and retrieves the user from the DB.
* **Test:** Write `tests/test_auth.py`:
    * Test successful registration.
    * Test login with correct/incorrect password.
    * Test accessing a protected route without a token (should return 401).

---

## Sprint 2: Competitions & Inscriptions
**Goal:** Allow users to create tournaments and manage participants.

### Phase 2.1: Competition Core
* **Task:** Create `Competition` model with fields: `id`, `name`, `description`, `start_date`, `status` (enum: PLANNED, ACTIVE, FINISHED), `format` (enum: ROUND_ROBIN, SWISS).
* **Task:** Create a many-to-many association table `competition_participants` linking `User` and `Competition`.
* **Task:** Implement CRUD endpoints for Competitions:
    * `POST /competitions/`: Create new (Admin/User).
    * `GET /competitions/`: List all.
    * `GET /competitions/{id}`: Get details.
* **Test:** Write `tests/test_competitions.py` to verify creation and retrieval.

### Phase 2.2: Player Management
* **Task:** Implement the "Join" logic.
    * Endpoint: `POST /competitions/{id}/join`.
    * Validation: Ensure user isn't already joined. Ensure competition status is `PLANNED`.
* **Task:** Implement `GET /competitions/{id}/participants` to list all players in a tournament.
* **Task:** Implement `DELETE /competitions/{id}/leave` for users to withdraw before start.
* **Test:** Write `tests/test_inscriptions.py`:
    * Test user joining a competition.
    * Test error when joining the same competition twice.
    * Test error when joining a closed/active competition.

---

## Sprint 3: Match Engine & Results
**Goal:** Generate match-ups and handle game outcomes.

### Phase 3.1: Match Model & Generation (Round Robin)
* **Task:** Create `Match` model with fields: `id`, `competition_id`, `white_player_id`, `black_player_id`, `round_number`, `result` (enum: 1-0, 0-1, 1/2-1/2, PENDING), `pgn_content`.
* **Task:** Implement a Service method `generate_round_robin_pairings(competition_id)`.
    * Logic: Use the "Circle Method" or simple iteration to create `Match` records for all players.
* **Task:** Endpoint: `POST /competitions/{id}/start`.
    * Action: Sets status to `ACTIVE` and triggers pairing generation.
* **Test:** Write `tests/test_matchmaking.py`:
    * Create a competition with 4 players. Trigger start. Verify 6 matches are created (mathematically correct for Single Round Robin).

### Phase 3.2: Results & Standings Logic
* **Task:** Endpoint: `POST /matches/{id}/result`.
    * Input: `ResultEnum`.
    * Validation: Only the players involved or an admin can set the result.
* **Task:** Implement `StandingsService`.
    * Logic: Query all matches for a competition.
    * Loop through players: +1 point for Win, +0.5 for Draw.
    * Return sorted list by Points (descending).
* **Task:** Endpoint: `GET /competitions/{id}/standings`.
* **Test:** Write `tests/test_results.py`:
    * Simulate a few match results.
    * Call the standings endpoint and verify the points are calculated correctly.

---

## Sprint 4: Polish, Validation & Advanced Features
**Goal:** Make the app robust, handle data validation, and prepare for frontend.

### Phase 4.1: PGN & Data Integrity
* **Task:** Add `pgn_content` validation.
    * Use `python-chess` library (optional) or regex to validate the move string in `PUT /matches/{id}/pgn`.
* **Task:** Refactor Routers. Move code from `main.py` into `app/api/v1/endpoints/` (e.g., `auth.py`, `competitions.py`, `matches.py`) to clean up the codebase.
* **Task:** Add CORS Middleware to `main.py` to allow requests from `localhost:3000` (React/Vue) or `localhost:5173` (Vite).

### Phase 4.2: Final Integration & Docker
* **Task:** Create a comprehensive "Tournament Lifecycle" test in `tests/test_integration.py`.
    * Scenario: Create User A & B -> Create Comp -> Join -> Start -> Play Match -> Submit Result -> Check Standings.
* **Task:** Create `Dockerfile` and `docker-compose.yml`.
    * Service 1: `web` (FastAPI).
    * Service 2: `db` (Postgres).
* **Task:** Generate final `requirements.txt` with frozen versions.

---

### How to use this with Gemini 3:
Start by pasting the **Project Context** and **Sprint 1** header. Ask Gemini to generate the code for Phase 1.1. Once that code is working and tested, paste Phase 1.2, and so on. This keeps the context window clean and the code high-quality.
