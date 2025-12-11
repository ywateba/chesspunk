# chesspunk
Chess community

# Chess Community Manager - API POC

This project is the backend API for a Chess Community Application. It is designed to manage amateur chess groups, allowing for player management, tournament creation, automatic matchmaking, and leaderboard tracking.

## 📋 Project Scope

The goal of this POC (Proof of Concept) is to provide a RESTful API that handles:
1.  **Player Management:** Registration and profile tracking.
2.  **Competition Management:** creating tournaments and handling inscriptions.
3.  **Matchmaking:** Generating pairings (Swiss System or Round Robin).
4.  **Game Reporting:** submitting results and game blueprints (PGN).
5.  **Standings:** Automatic calculation of points and classifications.

---

## 🛠️ API Endpoints

### 1. Authentication & Players
*Management of user identities and profiles.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Create a new player account (Username, Email, Password, Initial ELO). |
| `POST` | `/api/auth/login` | Authenticate and receive a JWT token. |
| `GET` | `/api/players/{id}` | Retrieve a player's profile, stats, and match history. |
| `GET` | `/api/players` | List all players (with optional search/filter). |

### 2. Competitions (Tournaments)
*Creation and management of tournament events.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/competitions` | Create a new competition (Name, Start Date, Format: *Swiss/Robin/Knockout*). |
| `GET` | `/api/competitions` | List all active or upcoming competitions. |
| `GET` | `/api/competitions/{id}` | Get details for a specific competition. |
| `PATCH` | `/api/competitions/{id}/status`| Update status (e.g., `Open` → `In Progress` → `Completed`). |

### 3. Inscriptions (Participation)
*Managing the link between players and competitions.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/competitions/{id}/join` | Register the authenticated user for a competition. |
| `DELETE`| `/api/competitions/{id}/leave` | Remove a player from the competition (before start). |
| `GET` | `/api/competitions/{id}/players` | List all participants currently registered. |

### 4. Matches & Pairing Logic
*Core logic for generating games and viewing brackets.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/competitions/{id}/rounds` | **Trigger:** Generates matches for the next round based on current standings. |
| `GET` | `/api/competitions/{id}/rounds` | List all rounds created for a tournament. |
| `GET` | `/api/matches/{id}` | Get specific details of a match (White vs. Black). |

### 5. Results & Blueprints
*Handling game outcomes and saving moves.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/matches/{id}/result` | Submit match result (e.g., `1-0`, `0-1`, `0.5-0.5`). |
| `PUT` | `/api/matches/{id}/pgn` | Upload the **Blueprint** (PGN string) of the match moves. |

### 6. Classification (Standings)
*Read-only endpoints for leaderboards.*

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/competitions/{id}/standings`| Get the ranked leaderboard. Calculates points and tie-breakers. |

---

## 🗄️ Data Model (Entities)

The database schema is built around these core relationships:

* **Player:** `id`, `username`, `email`, `rating`
* **Competition:** `id`, `name`, `status`, `format`
* **Participant:** Links `Player` to `Competition` with `current_score`.
* **Match:** `id`, `round_number`, `white_player_id`, `black_player_id`, `result`, `pgn_content`.

---

## 🧩 Matchmaking Logic

For this POC, the system supports two main formats:

1.  **Round Robin:**
    * Upon starting the competition, the system generates all $N \times (N-1) / 2$ matches immediately.
2.  **Swiss System (Simplified):**
    * Matches are generated one round at a time.
    * Players are paired based on equal scores.
    * Colors (White/Black) are balanced where possible.

---

## 🚀 Getting Started (Dev)

*Instructions to run the API locally.*

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    # Command to install (e.g., npm install, pip install, go mod download)
    ```
3.  Configure Environment Variables:
    * `DB_CONNECTION_STRING`
    * `JWT_SECRET`
4.  Run the server:
    ```bash
    # Command to start server
    ```
