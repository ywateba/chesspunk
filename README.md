# Chesspunk - Chess Community Manager API

A production-ready RESTful API for managing chess communities, tournaments, and player ratings. Built with modern async Python architecture supporting multi-database backends (SQL/NoSQL).

## 📋 Project Overview

**Chesspunk** is a comprehensive backend system for amateur chess groups that enables:

- **Player Management:** User registration, authentication, and ELO rating tracking
- **Tournament Management:** Create and manage chess competitions in multiple formats
- **Automatic Matchmaking:** Intelligent pairing using Swiss System, Round Robin, or Knockout formats
- **Game Tracking:** Submit match results with PGN (Portable Game Notation) validation
- **Leaderboards:** Real-time standings with FIDE scoring rules and Buchholz tiebreaker calculations
- **Communities:** Group management with member roles and discussion features

### Key Highlights
- ✅ **Clean Architecture:** Layered design with dependency injection and repository pattern
- ✅ **Database Agnostic:** Transparent switching between PostgreSQL and MongoDB without code changes
- ✅ **Async-First:** Non-blocking I/O with asyncpg, aiosqlite, and Motor for high concurrency
- ✅ **Production-Ready:** Rate limiting, security headers, structured logging, and metrics
- ✅ **Type-Safe:** Full Pydantic validation and SQLAlchemy type hints
- ✅ **Well-Tested:** Comprehensive test suite with pytest and integration tests

## 🛠️ Technology Stack

### Core Framework
- **FastAPI** - Modern async Python web framework with automatic OpenAPI docs
- **Uvicorn** - ASGI server for high-performance request handling
- **Pydantic** - Runtime data validation and serialization

### Database & ORM
- **SQLAlchemy 2.0** - Async-capable ORM with full type support
- **Alembic** - Database schema migrations
- **PostgreSQL** (production) / **SQLite** (development) - SQL databases
- **MongoDB** + **Beanie** - NoSQL support via Motor async driver
- **asyncpg** / **aiosqlite** - Async database drivers

### Security & Authentication
- **python-jose + PyJWT** - JWT token generation and validation
- **Passlib + bcrypt** - Secure password hashing
- **python-multipart** - Secure file upload handling

### Chess Logic
- **python-chess** - Move validation, PGN parsing, and game state management

### Infrastructure & Monitoring
- **slowapi** - Rate limiting middleware (5 req/min signup, 10 req/min login)
- **prometheus-fastapi-instrumentator** - Prometheus metrics collection
- **structlog** - Structured JSON logging for observability
- **python-dotenv** - Environment configuration

### Testing & Quality
- **pytest** + **pytest-asyncio** - Async test framework
- **httpx** - Async HTTP client for API testing
- **mongomock-motor** - MongoDB mocking for unit tests
- **tox** - Test automation across environments
- **Docker & Docker Compose** - Containerization and orchestration

---

## 🏗️ Architecture

### Layered Design
```
┌─────────────────────────────────────────────────────┐
│  API Routers (routers/)                             │
│  → /auth, /users, /competitions, /matches,          │
│    /communities                                      │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  Service Layer (services/)                          │
│  → auth_service, user_service, competition_service, │
│    match_service, elo_service, chess_service       │
│  (Business logic and tournament rules)              │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  Repository Pattern (repositories/)                 │
│  → Abstract interfaces w/ SQL & NoSQL implementations│
│  • sql/: PostgreSQL/SQLite implementations          │
│  • nosql/: MongoDB implementations                  │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  Database & ORM (db/)                               │
│  → SQLAlchemy models, Beanie document models        │
└─────────────────────────────────────────────────────┘
```

### Design Patterns

**1. Dependency Injection**
- `dependencies.py` provides repository instances based on configuration
- Services receive repositories via FastAPI `Depends()` mechanism
- Enables database-agnostic business logic

**2. Repository Pattern**
- Abstract `BaseRepository` defines interface
- `SQLUserRepository` and `MongoUserRepository` implement interchangeably
- Switch between backends at dependency layer—zero changes to business logic

**3. Async/Await Throughout**
- Non-blocking database I/O with asyncpg and Motor
- Async middleware for rate limiting and metrics
- Full asyncio integration with pytest-asyncio

**4. Pydantic Schemas**
- Separate schemas for Create, Update, and Response operations
- Runtime validation of all API inputs and outputs
- Clear separation from database models

---

## 🗄️ Data Model

### Core Entities

**User**
- `id`, `username`, `email`, `hashed_password`, `role`, `elo_rating`
- Relationships: can join multiple competitions, participate in matches

**Competition**
- `id`, `name`, `format` (Swiss/RoundRobin/Knockout), `status`, `community_id`
- Relationships: contains many matches, belongs to community

**Match**
- `id`, `white_player_id`, `black_player_id`, `result` (1-0/0-1/0.5-0.5), `pgn_blueprint`, `round_number`
- Relationships: linked to competition, references users

**Community**
- `id`, `name`, `owner_id`, `description`
- Relationships: contains many members and competitions

**CommunityMember**
- Links users to communities with roles (owner/moderator/member) and ranks

**Social Features**
- **Post**: Community discussions
- **Comment**: Threaded discussions on posts and matches

## 🛠️ API Endpoints

### Authentication (`/auth`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/signup` | Register new user with username, email, password |
| `POST` | `/auth/login` | Authenticate and receive JWT token |

### Users (`/users`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/users/me` | Get authenticated user's profile and stats |
| `GET` | `/users` | List all users (paginated, searchable) |
| `GET` | `/users/{id}` | Get specific user profile with match history |

### Competitions (`/competitions`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/competitions` | Create new tournament (name, format, start_date) |
| `GET` | `/competitions` | List all competitions (filtered by status) |
| `GET` | `/competitions/{id}` | Get competition details and metadata |
| `PATCH` | `/competitions/{id}` | Update competition status (Open → InProgress → Completed) |
| `GET` | `/competitions/{id}/standings` | Get leaderboard with FIDE scoring and Buchholz tiebreaker |
| `GET` | `/competitions/{id}/players` | List all registered participants |

### Matches (`/matches`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/matches/{id}` | Get match details (white/black, status, PGN) |
| `POST` | `/matches/{id}/result` | Submit match result (1-0, 0-1, or 0.5-0.5 draw) |
| `PUT` | `/matches/{id}/pgn` | Upload PGN string with game moves |

### Communities (`/communities`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/communities` | Create new community group |
| `GET` | `/communities` | List all communities |
| `GET` | `/communities/{id}` | Get community details and metadata |
| `GET` | `/communities/{id}/members` | List community members with roles |
| `POST` | `/communities/{id}/join` | Join community as member |
| `DELETE` | `/communities/{id}/leave` | Leave community |

### Documentation
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

## 🎯 Tournament Formats & Scoring

### Supported Tournament Formats

**1. Swiss System**
- Players are paired by score after each round
- Color (White/Black) assignments balanced across tournament
- Perfect for variable participation clubs
- Implemented in `competition_service.py`

**2. Round Robin**
- Every player plays every other player exactly once
- Total matches: $N \times (N-1) / 2$ for $N$ players
- Determines complete ranking with no byes

**3. Knockout (Single Elimination)**
- Bracket-style tournament
- Losers are eliminated; winners advance
- Fastest format for quick tournaments

### Scoring Rules

**FIDE Scoring System:**
- Win: 1 point
- Draw: 0.5 points  
- Loss: 0 points

**Tiebreaker (Buchholz System):**
- When players have equal points, compare sum of opponent scores
- Implemented in `elo_service.py` for accurate standings calculation
- Used across all tournament formats

### ELO Rating Updates
- Player ratings updated after each match result
- `elo_service.py` implements rating calculation
- Configurable K-factor for rating volatility

## 🚀 Getting Started

### Prerequisites
- **Docker & Docker Compose** (recommended) OR
- **Python 3.9+**, **PostgreSQL 14+** or **SQLite3**
- **pip** or **conda** package manager

### ⚡ Quickstart with Docker (Recommended)

```bash
# Clone and navigate to project
git clone <repository-url>
cd chesspunk

# Start the full stack (API + PostgreSQL)
docker compose up -d --build

# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

The Docker setup includes:
- FastAPI application on port 8000 with hot-reload
- PostgreSQL 14 on port 5432 with persistent volume
- Automatic schema migrations via Alembic on startup
- Shared volumes for live code development

### 🐍 Local Development Setup

#### 1. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

#### 2. Configure Environment
Create `.env` in `app/` directory:
```env
# Database (development uses SQLite)
DATABASE_URL=sqlite:///./test.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/chesspunk

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Backend Selection
USE_MONGO=false  # Set true to use MongoDB instead of SQL

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

#### 3. Run Database Migrations
```bash
cd app
alembic upgrade head
```

#### 4. Start Development Server
```bash
cd app/main/python
uvicorn routers.main:app --reload
```

Server runs with auto-reload on `http://localhost:8000`

### 🔧 Configuration Options

The application uses `core/config.py` for configuration management:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./test.db` | Database connection string |
| `USE_MONGO` | `false` | Switch between SQL and MongoDB backends |
| `SECRET_KEY` | Generated | JWT signing key |
| `DEBUG` | `false` | Enable debug mode and verbose logging |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed cross-origin domains |
| `RATE_LIMIT` | `5/minute` | Rate limit for signup/login endpoints |

### 📊 Database Selection

**SQL Mode (Default)**
- Uses SQLAlchemy with PostrgeSQL or SQLite
- Alembic manages schema migrations
- Production-ready with full ACID support

**NoSQL Mode**
- Switch via `USE_MONGO=true` in configuration
- Uses MongoDB with Beanie ODM
- Identical business logic, different persistence layer
- Useful for horizontal scaling scenarios

---

## 🧪 Testing

The project includes comprehensive test coverage using **pytest** with async support.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/python/test_auth.py

# Run with coverage report
pytest --cov=main --cov-report=html

# Run in isolated tox environment
cd app
tox
```

### Test Files Overview

| File | Purpose |
| --- | --- |
| `test_auth.py` | Authentication endpoints (signup, login, JWT validation) |
| `test_integration.py` | Full tournament lifecycle workflows |
| `test_matchmaking.py` | Swiss/Round Robin pairing logic |
| `test_service.py` | Business logic and scoring calculations |
| `test_chess_engine.py` | PGN parsing and move validation |
| `test_nosql_repo.py` | MongoDB repository implementations |
| `test_crud.py` | CRUD operations across all entities |

### Key Test Utilities

- **pytest-asyncio**: Async test function support
- **httpx**: Async HTTP client for endpoint testing
- **mongomock-motor**: MongoDB in-memory mocking
- **conftest.py**: Shared fixtures for test setup/teardown

---

## 📁 Project Structure

```
chesspunk/
├── docker-compose.yml              # Local dev environment
├── README.md                        # This file
├── Roadmap.md                       # Development roadmap
│
├── app/                             # Main application
│   ├── alembic/                     # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                # Migration scripts
│   │
│   ├── main/python/
│   │   ├── core/                    # Core application logic
│   │   │   ├── config.py            # Configuration management
│   │   │   ├── dependencies.py      # Dependency injection
│   │   │   ├── logger.py            # Structured logging
│   │   │   ├── middleware.py        # CORS, security middleware
│   │   │   ├── rate_limit.py        # Rate limiting setup
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── utils.py         # JWT token utilities
│   │   │   │   └── constants.py
│   │   │   │
│   │   │   ├── db/
│   │   │   │   ├── database.py      # SQLAlchemy session setup
│   │   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   │   └── documents.py     # Beanie MongoDB models
│   │   │   │
│   │   │   ├── repositories/        # Data access layer
│   │   │   │   ├── base.py          # Abstract base classes
│   │   │   │   ├── sql/             # SQL implementations
│   │   │   │   │   ├── user_repo.py
│   │   │   │   │   ├── match_repo.py
│   │   │   │   │   ├── competition_repo.py
│   │   │   │   │   ├── community_repo.py
│   │   │   │   │   └── social_repo.py
│   │   │   │   │
│   │   │   │   └── nosql/          # MongoDB implementations
│   │   │   │       ├── user_repo.py
│   │   │   │       ├── match_repo.py
│   │   │   │       └── ...
│   │   │   │
│   │   │   ├── schemas/
│   │   │   │   └── schemas.py       # Pydantic request/response models
│   │   │   │
│   │   │   └── services/            # Business logic layer
│   │   │       ├── auth_service.py
│   │   │       ├── user_service.py
│   │   │       ├── competition_service.py
│   │   │       ├── match_service.py
│   │   │       ├── elo_service.py
│   │   │       └── chess_service.py
│   │   │
│   │   └── routers/                 # API endpoints
│   │       ├── main.py              # FastAPI app instantiation
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── competitions.py
│   │       ├── matches.py
│   │       └── communities.py
│   │
│   ├── tests/python/                # Test suite
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_integration.py
│   │   ├── test_matchmaking.py
│   │   ├── test_service.py
│   │   └── ...
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── requirements/                # Dependency groups
│   ├── setup.py                     # Package setup
│   ├── pytest.ini                   # Pytest configuration
│   ├── tox.ini                      # Tox test environments
│   ├── alembic.ini                  # Alembic configuration
│   └── Dockerfile                   # Container image
│
├── lambda/                           # AWS Lambda functions (future)
├── webapp/                           # Frontend (future)
└── LICENSE
```

---

## 🔐 Security

The application implements modern security best practices:

- **JWT Authentication**: Asymmetric token signing with configurable expiration
- **Password Security**: bcrypt hashing with automatic salt generation
- **Rate Limiting**: Prevents brute force attacks on auth endpoints
- **CORS**: Configurable cross-origin access control
- **Security Headers**: 
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security` (when HTTPS enabled)
- **Input Validation**: Pydantic validates all request data
- **Database**: Prepared statements prevent SQL injection (SQLAlchemy)

---

## 📈 Performance & Monitoring

### Metrics Collection
- **Prometheus**: Instrumented via `prometheus-fastapi-instrumentator`
- **Endpoint Metrics**: Request count, latency percentiles, status codes
- **Custom Metrics**: Database query times, ELO calculation duration

### Logging
- **Structured Logging**: JSON-formatted logs via structlog
- **Log Levels**: DEBUG, INFO, WARNING, ERROR with context
- **Correlation IDs**: Track requests through async operations

### Async Performance
- Non-blocking I/O with asyncpg (PostgreSQL)
- Connection pooling configured for concurrent requests
- MongoDB async driver (Motor) for NoSQL operations

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🗺️ Roadmap

See [Roadmap.md](Roadmap.md) for planned features and improvements.

---

## 📞 Support & Questions

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
