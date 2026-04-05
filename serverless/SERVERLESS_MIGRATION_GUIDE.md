non su dev nulla# Chesspunk Serverless Migration Guide
## AWS Lambda + API Gateway + DynamoDB Architecture

---

## Executive Summary

This guide outlines a phased migration of Chesspunk from **FastAPI on EC2/ECS** to a **fully serverless architecture** on AWS:

| Component | Current | Target | Change |
|-----------|---------|--------|--------|
| **Compute** | FastAPI + Uvicorn | AWS Lambda | Managed, auto-scaling |
| **HTTP Gateway** | FastAPI routing | API Gateway | RESTful routing, request/response transformation |
| **Database** | PostgreSQL/MongoDB | DynamoDB | NoSQL, serverless, managed auto-scaling |
| **Auth** | JWT + OAuth2PasswordBearer | API Gateway Authorizers + Cognito | Native AWS auth integration |
| **Rate Limiting** | slowapi middleware | API Gateway Throttling | Native AWS rate limiting |
| **Logging/Metrics** | structlog + Prometheus | CloudWatch + X-Ray | Native AWS observability |
| **Deployment** | Docker + compose | Serverless Framework / SAM / Terraform | IaC with CloudFormation |

**Key Benefits:**
- ✅ Zero infrastructure management (no EC2/ECS teams)
- ✅ Automatic horizontal scaling (DynamoDB on-demand pricing)
- ✅ Pay-per-request pricing (cost efficient for variable workloads)
- ✅ Native AWS integration (Cognito, X-Ray, CloudWatch)
- ✅ Cold start optimization (Python 3.11 + Lambda layers)

**Challenges:**
- ⚠️ DynamoDB schema redesign (from relational to document-oriented)
- ⚠️ Query pattern changes (no complex JOINs like SQL)
- ⚠️ Cold start latency (mitigatable with provisioned concurrency)
- ⚠️ Lambda payload size limits (6 MB request/response)
- ⚠️ Authentication redesign (OAuth2PasswordBearer → API Gateway + Cognito)

---

## Part 1: Architecture Overview

### Current (FastAPI) Architecture
```
┌──────────────────────────────────────────────────────┐
│              Internet / Load Balancer                 │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   FastAPI App Instance   │
        │   (Uvicorn)              │
        │  - Routers (auth, users, │
        │    competitions, matches) │
        │  - Services (business)    │
        │  - Dependencies           │
        │  - Middleware             │
        └────────────┬──────────────┘
                     │
        ┌────────────▼────────────┐
        │  Repository Layer        │
        │  - SQL or MongoDB        │
        └────────────┬──────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
  ┌───▼────┐                   ┌────▼────┐
  │PostgreSQL  │              │MongoDB    │
  │(Prod)     │              │(Optional) │
  └───────────┘              └──────────┘
```

### Target (Serverless) Architecture
```
┌──────────────────────────────────────────────────────┐
│         Internet / CloudFront Distribution            │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼────────────────────┐
        │    API Gateway                   │
        │  - Route mapping                 │
        │  - Authorizer (Cognito/Custom)   │
        │  - Request/Response transform    │
        │  - Throttling & rate limiting    │
        └────────────┬─────────────────────┘
                     │
    ┌────────────────┼────────────────────┐
    │                │                    │
┌───▼────┐      ┌────▼────┐         ┌────▼────┐
│ Lambda  │      │ Lambda  │  ....  │ Lambda  │
│/auth    │      │/users   │        │/matches │
│POST,    │      │GET,POST │        │GET POST │
│GET      │      │         │        │         │
└───┬────┘      └────┬────┘         └────┬───┘
    │                │                    │
    └────────────────┼────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Repository Layer        │
        │  (DynamoDB-specific      │
        │   implementations)       │
        └────────────┬──────────────┘
                     │
        ┌────────────▼────────────┐
        │    DynamoDB              │
        │  - Global Secondary      │
        │    Indexes (GSI)         │
        │  - On-demand billing      │
        └──────────────────────────┘
```

---

## Part 2: Phase-by-Phase Migration Roadmap

### Phase 1: Code Refactoring (Framework Decoupling)
**Duration:** 2-3 weeks | **Risk:** Low | **Reversible:** Yes

**Objective:** Decouple services and repositories from FastAPI before changing infrastructure.

#### 1.1 Extract Services to Separate Module

Create `/app/main/python/services/__init__.py` layer that's completely framework-agnostic:

```python
# Before: Router depends on FastAPI + Service
@router.post("/competitions/{id}/generate-matches")
async def generate_matches(
    id: str,
    competition_repo = Depends(get_competition_repository)
):
    return await competition_service.generate_matches(competition_repo, id)

# After: All services are pure Python, no FastAPI imports
class CompetitionService:
    async def generate_matches(self, repo: CompetitionRepository, comp_id: str):
        comp = await repo.get_by_id(comp_id)
        matches = self._calculate_pairings(comp)
        return await repo.create_matches(matches)
    
    def _calculate_pairings(self, competition):
        # Pure Python logic, zero framework dependencies
        ...
```

**Actions:**
- Move all business logic from routers to services
- Ensure services only depend on repository abstractions
- Add unit tests for services (test without FastAPI)
- Create service factories for dependency injection

#### 1.2 Abstract Authentication Layer

Replace FastAPI's OAuth2PasswordBearer with a custom authentication abstraction:

```python
# Before: FastAPI-specific
from fastapi.security import OAuth2PasswordBearer, HTTPBearer

# After: Custom abstraction
class AuthProvider:
    async def extract_token(self, auth_header: str) -> str:
        # Tokenextraction logic
        ...
    
    async def verify_token(self, token: str) -> Dict[str, any]:
        # JWT verification - framework-agnostic
        ...
    
    async def get_current_user(self, token: str) -> User:
        # User lookup - framework-agnostic
        ...

# Usage in router (later migrated to Lambda handler)
auth = AuthProvider()
user = await auth.get_current_user(token)
```

**Actions:**
- Create `core/auth/auth_provider.py` with `AuthProvider` class
- Migrate all auth endpoints to use new abstraction
- Write tests for auth logic independently of FastAPI

#### 1.3 Create Handler/Event Abstraction

Prepare for Lambda handlers by creating event transformation layer:

```python
# Lambda receives API Gateway events, needs HTTP-agnostic business functions
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class HTTPRequest:
    """Serverless-agnostic request representation"""
    method: str
    path: str
    headers: Dict[str, str]
    body: str | None
    path_params: Dict[str, str]
    query_params: Dict[str, str]
    user: Dict[str, Any] | None = None

@dataclass
class HTTPResponse:
    status_code: int
    headers: Dict[str, str]
    body: str

# Service functions accept HTTPRequest, return HTTPResponse
async def handle_create_competition(request: HTTPRequest, repo) -> HTTPResponse:
    try:
        data = json.loads(request.body)
        comp = await service.create_competition(repo, data)
        return HTTPResponse(status_code=201, headers={}, body=json.dumps(comp))
    except ValidationError as e:
        return HTTPResponse(status_code=422, headers={}, body=json.dumps({"error": str(e)}))
```

**Actions:**
- Create `core/models/http.py` with `HTTPRequest` and `HTTPResponse` dataclasses
- Add conversion functions: `apigateway_event_to_request()`, `response_to_apigateway()`
- Refactor routers to use this abstraction (allows testing without FastAPI)

### Phase 2: Database Schema Redesign for DynamoDB
**Duration:** 3-4 weeks | **Risk:** Medium | **Reversible:** Partial

**Objective:** Transform relational/document schema to DynamoDB's flat key-value model.

#### 2.1 Understand DynamoDB Constraints

**DynamoDB Fundamentals:**
- **Partition Key (PK)**: Required, must be unique within partition, used for sharding
- **Sort Key (SK)**: Optional, enables range queries and composite keys
- **Attribute**: Any JSON-compatible type (string, number, binary, bool, null, list, map, set)
- **GSI (Global Secondary Index)**: Separate table with different PK/SK for queries
- **Query vs Scan**: Query is fast (uses partition key), Scan is expensive (full table)
- **Item Size Limit**: 400 KB per item
- **No JOINs**: Must denormalize or query multiple times

#### 2.2 Current Schema (PostgreSQL)

```sql
-- Users (relational)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    hashed_password VARCHAR,
    role VARCHAR,
    elo INT DEFAULT 1200
);

-- Competitions (with M2M)
CREATE TABLE competitions (
    id UUID PRIMARY KEY,
    name VARCHAR,
    format VARCHAR,
    status VARCHAR,
    community_id UUID REFERENCES communities
);

CREATE TABLE competition_players (
    competition_id UUID REFERENCES competitions,
    user_id UUID REFERENCES users,
    PRIMARY KEY (competition_id, user_id)
);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY,
    competition_id UUID REFERENCES competitions,
    white_player_id UUID REFERENCES users,
    black_player_id UUID REFERENCES users,
    result VARCHAR,
    pgn_blueprint TEXT,
    round_number INT
);
```

#### 2.3 DynamoDB Schema (Denormalized)

**Core Tables:**

**Table 1: Users**
```
PK: USER#{user_id}
SK: PROFILE

Attributes:
{
  PK: "USER#abc-123-def",
  SK: "PROFILE",
  username: "alice_chess",
  email: "alice@chess.com",
  hashed_password: "...",
  role: "member",
  elo: 1250,
  created_at: 1680000000,
  updated_at: 1680100000
}

GSI1 (for email lookups):
PK: email
SK: user_id
```

**Table 2: Competitions**
```
PK: COMPETITION#{comp_id}
SK: METADATA

Attributes:
{
  PK: "COMPETITION#tournament-2024",
  SK: "METADATA",
  name: "Spring Chess Tournament 2024",
  format: "swiss",      # swiss | roundrobin | knockout
  status: "open",       # open | in_progress | completed
  community_id: "COMMUNITY#chess-club-1",
  created_at: 1680000000,
  updated_at: 1680100000
}

PK: COMPETITION#{comp_id}
SK: PLAYER#{user_id}         # Denormalized: track all players in competition

Attributes:
{
  PK: "COMPETITION#tournament-2024",
  SK: "PLAYER#alice-123",
  user_id: "alice-123",
  username: "alice_chess",    # Denormalized for quick lookup
  elo: 1250,
  current_score: 1.5,
  buchholz: 2.0,
  round_wins: 1,
  round_draws: 1,
  round_losses: 0
}

GSI1 (for community competitions):
PK: community_id
SK: created_at          # Newest competitions first
```

**Table 3: Matches**
```
PK: COMPETITION#{comp_id}
SK: MATCH#{round}#{match_id}     # Enables range queries by round

Attributes:
{
  PK: "COMPETITION#tournament-2024",
  SK: "MATCH#1#match-001",
  match_id: "match-001",
  round: 1,
  white_player_id: "alice-123",
  white_username: "alice_chess",      # Denormalized
  white_elo: 1250,
  black_player_id: "bob-456",
  black_username: "bob_master",       # Denormalized
  black_elo: 1300,
  result: "white_wins",               # white_wins | black_wins | draw | pending
  pgn_blueprint: "1. e4 e5 ...",
  created_at: 1680000000,
  updated_at: 1680100000
}

# For user-specific match queries (GSI)
GSI1:
PK: white_player_id
SK: created_at

GSI2:
PK: black_player_id
SK: created_at
```

**Table 4: Communities**
```
PK: COMMUNITY#{community_id}
SK: METADATA

Attributes:
{
  PK: "COMMUNITY#chess-club-1",
  SK: "METADATA",
  name: "Local Chess Club",
  description: "Community for casual players",
  owner_id: "alice-123",
  created_at: 1680000000,
  member_count: 42
}

PK: COMMUNITY#{community_id}
SK: MEMBER#{user_id}       # Denormalized members

Attributes:
{
  PK: "COMMUNITY#chess-club-1",
  SK: "MEMBER#alice-123",
  user_id: "alice-123",
  username: "alice_chess",
  role: "owner",            # owner | moderator | member
  rank: "champion",
  joined_at: 1680000000
}

GSI1 (for global community list):
PK: "COMMUNITIES"           # Partition constant
SK: created_at
```

**Table 5: Social (Posts/Comments)**
```
PK: COMMUNITY#{community_id}
SK: POST#{post_id}

Attributes:
{
  PK: "COMMUNITY#chess-club-1",
  SK: "POST#post-123",
  post_id: "post-123",
  author_id: "alice-123",
  author_username: "alice_chess",
  title: "Tournament Results",
  content: "Congratulations to the winners...",
  created_at: 1680000000,
  comments: [
    {
      comment_id: "cmt-001",
      author_id: "bob-456",
      content: "Great tournament!",
      created_at: 1680001000
    }
  ]                         # Embedded for small comment lists
}
```

#### 2.4 Schema Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Denormalization (username, elo in matches)** | Avoid read amplification; get full match details in 1 query |
| **sk: PLAYER#{user_id}** | Enable listing all competition players without secondary index |
| **sk: MATCH#{round}#{id}** | Query matches by round with range key filtering |
| **GSI for emails** | User lookups by email still fast (auth flow) |
| **Embedded comments in posts** | Comments < 400 KB total keeps item atomic |
| **No separate M2M table** | Flatten competition_players into COMPETITION#{id} items |

#### 2.5 Migration Strategy

1. **Keep SQL alongside DynamoDB** (dual writes in Phase 2):
   - New code writes to both databases
   - Read from SQL (source of truth)
   - Test DynamoDB consistency
   - Identify query patterns

2. **Create migration scripts:**
   ```python
   # scripts/migrate_to_dynamodb.py
   async def migrate_users(sql_session, dynamodb_table):
       users = await get_all_users(sql_session)
       for user in users:
           item = {
               'PK': f"USER#{user.id}",
               'SK': 'PROFILE',
               'username': user.username,
               'email': user.email,
               'elo': user.elo,
               'created_at': int(user.created_at.timestamp())
           }
           await dynamodb_table.put_item(Item=item)
   ```

3. **Write validation queries:**
   - Compare row counts (SQL vs DynamoDB)
   - Spot-check records for correctness
   - Validate GSI query results

---

### Phase 3: Implement DynamoDB Repositories
**Duration:** 3-4 weeks | **Risk:** Low | **Reversible:** Yes

**Objective:** Create DynamoDB repository implementations mirroring existing SQL repositories.

#### 3.1 DynamoDB Repository Base Class

```python
# app/main/python/core/repositories/dynamodb/base.py
from boto3.dynamodb.conditions import Key, Attr
import boto3

class DynamoDBRepository:
    def __init__(self, table_name: str):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = dynamodb.Table(table_name)
    
    async def get_by_id(self, pk: str, sk: str | None = None) -> Dict | None:
        """Retrieve single item"""
        if sk is None:
            sk = "METADATA"
        
        response = await self.table.get_item(Key={'PK': pk, 'SK': sk})
        return response.get('Item')
    
    async def query(self, pk: str, sk_prefix: str | None = None) -> List[Dict]:
        """Query by partition key with optional sort key prefix"""
        key_condition = Key('PK').eq(pk)
        if sk_prefix:
            key_condition &= Key('SK').begins_with(sk_prefix)
        
        response = await self.table.query(KeyConditionExpression=key_condition)
        return response.get('Items', [])
    
    async def put_item(self, item: Dict) -> None:
        """Create/overwrite item"""
        await self.table.put_item(Item=item)
    
    async def update_item(self, pk: str, sk: str, updates: Dict) -> None:
        """Update specific attributes"""
        update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in updates.keys())
        await self.table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression=update_expression,
            ExpressionAttributeValues={f":{k}": v for k, v in updates.items()}
        )
    
    async def delete_item(self, pk: str, sk: str) -> None:
        """Delete item"""
        await self.table.delete_item(Key={'PK': pk, 'SK': sk})
    
    async def scan_with_filter(self, 
                              filter_expression: Attr | None = None) -> List[Dict]:
        """Scan table with optional filter (expensive operation)"""
        kwargs = {}
        if filter_expression:
            kwargs['FilterExpression'] = filter_expression
        
        response = await self.table.scan(**kwargs)
        return response.get('Items', [])
```

#### 3.2 DynamoDB User Repository

```python
# app/main/python/core/repositories/dynamodb/user_repo.py
from core.repositories.base import UserRepository
from core.db.models import User
from datetime import datetime
import uuid

class DynamoDBUserRepository(UserRepository):
    def __init__(self, dynamodb_table):
        self.table = dynamodb_table
        self.table_name = "chesspunk-users"
    
    async def create(self, user_data: Dict) -> User:
        user_id = str(uuid.uuid4())
        now = int(datetime.utcnow().timestamp())
        
        item = {
            'PK': f"USER#{user_id}",
            'SK': 'PROFILE',
            'user_id': user_id,
            'username': user_data['username'],
            'email': user_data['email'],
            'hashed_password': user_data['hashed_password'],
            'role': user_data.get('role', 'member'),
            'elo': user_data.get('elo', 1200),
            'created_at': now,
            'updated_at': now
        }
        
        await self.table.put_item(Item=item)
        return User(**item)
    
    async def get_by_id(self, user_id: str) -> User | None:
        response = await self.table.get_item(
            Key={'PK': f"USER#{user_id}", 'SK': 'PROFILE'}
        )
        return User(**response['Item']) if 'Item' in response else None
    
    async def get_by_email(self, email: str) -> User | None:
        # Use GSI for email lookup
        response = await self.table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])
        if not items:
            return None
        
        # Convert DynamoDB item to User object
        return User(**items[0])
    
    async def get_by_username(self, username: str) -> User | None:
        response = await self.table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return User(**items[0]) if items else None
    
    async def list(self, skip: int = 0, limit: int = 10) -> List[User]:
        # DynamoDB doesn't support OFFSET, must use pagination
        response = await self.table.scan(Limit=limit + skip)
        items = response['Items'][skip:skip + limit]
        return [User(**item) for item in items]
    
    async def update(self, user_id: str, updates: Dict) -> User:
        updates['updated_at'] = int(datetime.utcnow().timestamp())
        
        await self.table.update_item(
            Key={'PK': f"USER#{user_id}", 'SK': 'PROFILE'},
            UpdateExpression="SET " + ", ".join(f"{k} = :{k}" for k in updates),
            ExpressionAttributeValues={f":{k}": v for k, v in updates.items()}
        )
        
        return await self.get_by_id(user_id)
    
    async def delete(self, user_id: str) -> None:
        await self.table.delete_item(
            Key={'PK': f"USER#{user_id}", 'SK': 'PROFILE'}
        )
```

#### 3.3 DynamoDB Competition Repository

```python
# app/main/python/core/repositories/dynamodb/competition_repo.py
from core.repositories.base import CompetitionRepository
from core.db.models import Competition, Match
from datetime import datetime
import uuid

class DynamoDBCompetitionRepository(CompetitionRepository):
    def __init__(self, dynamodb_table, users_table):
        self.table = dynamodb_table
        self.users_table = users_table
    
    async def create(self, comp_data: Dict) -> Competition:
        comp_id = str(uuid.uuid4())
        now = int(datetime.utcnow().timestamp())
        
        # Metadata item
        item = {
            'PK': f"COMPETITION#{comp_id}",
            'SK': 'METADATA',
            'comp_id': comp_id,
            'name': comp_data['name'],
            'format': comp_data['format'],     # swiss | roundrobin | knockout
            'status': 'open',
            'community_id': comp_data.get('community_id'),
            'created_at': now,
            'updated_at': now
        }
        
        await self.table.put_item(Item=item)
        return Competition(**item)
    
    async def get_by_id(self, comp_id: str) -> Competition:
        response = await self.table.get_item(
            Key={'PK': f"COMPETITION#{comp_id}", 'SK': 'METADATA'}
        )
        if 'Item' not in response:
            raise ValueError(f"Competition {comp_id} not found")
        
        # Fetch all players for this competition
        players_response = await self.table.query(
            KeyConditionExpression=Key('PK').eq(f"COMPETITION#{comp_id}")
            & Key('SK').begins_with('PLAYER#')
        )
        
        comp_data = response['Item']
        comp_data['players'] = players_response.get('Items', [])
        return Competition(**comp_data)
    
    async def add_player(self, comp_id: str, user_id: str, username: str, elo: int):
        """Register player in competition"""
        item = {
            'PK': f"COMPETITION#{comp_id}",
            'SK': f"PLAYER#{user_id}",
            'user_id': user_id,
            'username': username,
            'elo': elo,
            'current_score': 0.0,
            'buchholz': 0.0,
            'round_wins': 0,
            'round_draws': 0,
            'round_losses': 0
        }
        await self.table.put_item(Item=item)
    
    async def get_standings(self, comp_id: str) -> List[Dict]:
        """Get competition standings sorted by FIDE scoring"""
        players_response = await self.table.query(
            KeyConditionExpression=Key('PK').eq(f"COMPETITION#{comp_id}")
            & Key('SK').begins_with('PLAYER#')
        )
        
        players = players_response['Items']
        # Sort by: points desc, buchholz desc, wins desc
        return sorted(
            players,
            key=lambda p: (-p['current_score'], -p['buchholz'], -p['round_wins'])
        )
    
    async def create_matches(self, comp_id: str, round_num: int, matches: List[Dict]):
        """Create matches for a round"""
        for match in matches:
            match_id = str(uuid.uuid4())
            item = {
                'PK': f"COMPETITION#{comp_id}",
                'SK': f"MATCH#{round_num}#{match_id}",
                'match_id': match_id,
                'round': round_num,
                'white_player_id': match['white_id'],
                'white_username': match['white_name'],
                'white_elo': match['white_elo'],
                'black_player_id': match['black_id'],
                'black_username': match['black_name'],
                'black_elo': match['black_elo'],
                'result': 'pending',
                'pgn_blueprint': '',
                'created_at': int(datetime.utcnow().timestamp())
            }
            await self.table.put_item(Item=item)
    
    async def get_matches_by_round(self, comp_id: str, round_num: int) -> List[Match]:
        """Get all matches for a specific round"""
        response = await self.table.query(
            KeyConditionExpression=Key('PK').eq(f"COMPETITION#{comp_id}")
            & Key('SK').begins_with(f'MATCH#{round_num}#')
        )
        return [Match(**item) for item in response.get('Items', [])]
```

#### 3.4 Update Dependencies.py

```python
# app/main/python/core/dependencies.py
import os
import boto3
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.dynamodb.user_repo import DynamoDBUserRepository
from core.db.database import AsyncSessionLocal

async def get_user_repository():
    """Dependency injection with database abstraction"""
    db_engine = os.getenv("DB_ENGINE", "SQL").upper()
    
    if db_engine == "DYNAMODB":
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('chesspunk-users')
        return DynamoDBUserRepository(table)
    elif db_engine == "NOSQL":
        return MongoUserRepository()
    else:
        # Default to SQL
        async with AsyncSessionLocal() as db:
            return SQLUserRepository(db)
```

---

### Phase 4: Lambda Handler Layer
**Duration:** 2-3 weeks | **Risk:** Medium | **Reversible:** Yes

**Objective:** Create Lambda handlers that adapt API Gateway events to service layer.

#### 4.1 Lambda Handler Structure

```
app/
  lambda/
    layers/                         # Lambda layers for dependencies
      python/
        lib/python3.11/site-packages/
          (numpy, boto3, pydantic, etc.)
    
    handlers/                       # Lambda handler functions
      auth/
        signup.py
        login.py
      users/
        list_users.py
        get_user.py
      competitions/
        create.py
        list.py
        get_standings.py
      matches/
        submit_result.py
        get_match.py
      ...
    
    shared/                         # Shared utilities
      auth.py                       # JWT verification
      errors.py                     # StandardError handling
      decorators.py                 # Logging, error handling decorator
      models.py                     # HTTP request/response models
```

#### 4.2 API Gateway Event to Request Adapter

```python
# app/lambda/shared/models.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json

@dataclass
class APIGatewayRequest:
    """Transform API Gateway event into domain model"""
    method: str
    path: str
    resource: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    path_parameters: Dict[str, str]
    query_string_parameters: Dict[str, str]
    request_context: Dict[str, Any]

@dataclass
class APIGatewayResponse:
    status_code: int
    body: str
    headers: Dict[str, str] = None

    def to_lambda_response(self) -> Dict:
        """Convert to Lambda@Edge response format"""
        return {
            "statusCode": self.status_code,
            "body": self.body,
            "headers": self.headers or {"Content-Type": "application/json"}
        }

def parse_api_gateway_event(event: Dict[str, Any]) -> APIGatewayRequest:
    """Convert API Gateway event to domain request"""
    try:
        body = None
        if event.get('body'):
            body = json.loads(event['body'])
    except json.JSONDecodeError:
        body = None
    
    return APIGatewayRequest(
        method=event['httpMethod'],
        path=event['path'],
        resource=event['resource'],
        headers=event.get('headers', {}),
        body=body,
        path_parameters=event.get('pathParameters', {}),
        query_string_parameters=event.get('queryStringParameters', {}),
        request_context=event.get('requestContext', {})
    )
```

#### 4.3 Lambda Decorators for Cross-Cutting Concerns

```python
# app/lambda/shared/decorators.py
import json
import logging
from functools import wraps
from datetime import datetime
import traceback

logger = logging.getLogger()

def lambda_handler(func):
    """
    Decorator for Lambda handlers:
    - Parses API Gateway event
    - Handles errors
    - Serializes response
    - Logs request/response
    """
    @wraps(func)
    async def wrapper(event: Dict, context):
        request_id = context.request_id
        logger.info(f"[{request_id}] Request received", extra={
            "method": event.get('httpMethod'),
            "path": event.get('path'),
            "sourceIP": event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        })
        
        try:
            # Parse request
            request = parse_api_gateway_event(event)
            
            # Call handler
            response = await func(request, context)
            
            logger.info(f"[{request_id}] Request succeeded", extra={
                "status_code": response.status_code
            })
            
            return response.to_lambda_response()
        
        except ValidationError as e:
            logger.warning(f"[{request_id}] Validation error", extra={
                "errors": e.errors()
            })
            return {
                "statusCode": 422,
                "body": json.dumps({"error": "Validation failed", "details": e.errors()})
            }
        
        except Exception as e:
            logger.error(f"[{request_id}] Unhandled error", extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }
    
    return wrapper

def require_auth(func):
    """Decorator to extract & verify JWT from Authorization header"""
    @wraps(func)
    async def wrapper(request: APIGatewayRequest, context):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return APIGatewayResponse(
                status_code=401,
                body=json.dumps({"error": "Missing authorization"})
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            user = await auth_provider.verify_token(token)
            request.user = user
        except Exception as e:
            return APIGatewayResponse(
                status_code=401,
                body=json.dumps({"error": "Invalid token"})
            )
        
        return await func(request, context)
    
    return wrapper
```

#### 4.4 Example Lambda Handler

```python
# app/lambda/handlers/auth/signup.py
import json
from shared.models import APIGatewayRequest, APIGatewayResponse, parse_api_gateway_event
from shared.decorators import lambda_handler
from core.services.auth_service import AuthService
from core.repositories.dynamodb.user_repo import DynamoDBUserRepository
import boto3

@lambda_handler
async def handler(request: APIGatewayRequest, context):
    """POST /auth/signup"""
    
    # Validate request
    if not request.body:
        return APIGatewayResponse(
            status_code=400,
            body=json.dumps({"error": "Request body required"})
        )
    
    try:
        data = request.body
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return APIGatewayResponse(
                status_code=422,
                body=json.dumps({
                    "error": "Missing required fields",
                    "required": ["username", "email", "password"]
                })
            )
        
        # Initialize repository
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table('chesspunk-users')
        user_repo = DynamoDBUserRepository(users_table)
        
        # Initialize service
        auth_service = AuthService(user_repo)
        
        # Perform signup
        user = await auth_service.register_user(
            username=username,
            email=email,
            password=password
        )
        
        return APIGatewayResponse(
            status_code=201,
            body=json.dumps({
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            })
        )
    
    except Exception as e:
        return APIGatewayResponse(
            status_code=500,
            body=json.dumps({"error": str(e)})
        )

# Lambda handler entry point
def lambda_handler_entry(event, context):
    import asyncio
    return asyncio.run(handler(event, context))
```

#### 4.5 Authorization with Cognito

```python
# app/lambda/shared/auth.py
import json
import boto3
from jose import jwt
from datetime import datetime

cognito = boto3.client('cognito-idp')

async def verify_cognito_token(token: str, user_pool_id: str):
    """
    Verify Cognito user pool token
    In production, cache public keys and validate locally
    """
    try:
        # Decode JWT (Cognito public keys are cached locally)
        decoded = jwt.get_unverified_claims(token)
        
        # Validate expiration
        if decoded['exp'] < datetime.utcnow().timestamp():
            raise ValueError("Token expired")
        
        return {
            'user_id': decoded['sub'],
            'username': decoded['cognito:username'],
            'email': decoded['email'],
            'groups': decoded.get('cognito:groups', [])
        }
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")

def create_cognito_authorizer():
    """
    API Gateway Authorizer that validates Cognito tokens
    Attach this to API Gateway as Lambda authorizer
    """
    async def authorizer(event, context):
        token = event.get('authorizationToken', '')
        
        if not token.startswith('Bearer '):
            return deny_policy(event['methodArn'])
        
        try:
            user = await verify_cognito_token(
                token.split(' ')[1],
                "<USER_POOL_ID>"
            )
            return allow_policy(event['methodArn'], user)
        except Exception:
            return deny_policy(event['methodArn'])
    
    return authorizer

def allow_policy(method_arn: str, user: Dict):
    return {
        "principalId": user['user_id'],
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": method_arn
            }]
        },
        "context": {
            "userId": user['user_id'],
            "username": user['username'],
            "email": user['email']
        }
    }

def deny_policy(method_arn: str):
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Deny",
                "Resource": method_arn
            }]
        }
    }
```

---

### Phase 5: Infrastructure as Code (AWS SAM / Terraform)
**Duration:** 2-3 weeks | **Risk:** Medium | **Reversible:** Yes

**Objective:** Define all AWS resources (API Gateway, Lambda, DynamoDB, Cognito) as code.

#### 5.1 Using AWS SAM (Serverless Application Model)

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2.0

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Globals:
  Function:
    Timeout: 30
    Runtime: python3.11
    Environment:
      Variables:
        DB_ENGINE: DYNAMODB
        AWS_LAMBDA_LOG_LEVEL: INFO

Resources:
  # ============ DynamoDB Tables ============
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'chesspunk-users-${Environment}'
      BillingMode: PAY_PER_REQUEST              # On-demand pricing
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: email
          AttributeType: S
        - AttributeName: username
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: email-index
          KeySchema:
            - AttributeName: email
              KeyType: HASH
          Projection:
            ProjectionType: ALL
        - IndexName: username-index
          KeySchema:
            - AttributeName: username
              KeyType: HASH
          Projection:
            ProjectionType: ALL
      Tags:
        - Key: Environment
          Value: !Ref Environment

  CompetitionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'chesspunk-competitions-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: community_id
          AttributeType: S
        - AttributeName: created_at
          AttributeType: N
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: community-competitions-index
          KeySchema:
            - AttributeName: community_id
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES   # For Lambda triggers
      Tags:
        - Key: Environment
          Value: !Ref Environment

  # ============ Lambda Layers ============
  DependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub 'chesspunk-dependencies-${Environment}'
      Description: 'Python dependencies for Lambda'
      ContentUri: lambda/layers/
      CompatibleRuntimes:
        - python3.11

  # ============ API Gateway ============
  ChessunkAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Auth:
        Authorizers:
          CognitoAuthorizer:
            UserPoolArn: !GetAtt ChessunkUserPool.Arn
            Identity:
              Header: Authorization
      Cors:
        AllowHeaders: "'Authorization,Content-Type'"
        AllowMethods: "'GET,POST,PUT,DELETE,PATCH'"
        AllowOrigin: "'*'"
        MaxAge: "'600'"
      LoggingLevel: INFO
      DataTraceEnabled: true

  # ============ Auth Functions ============
  SignupFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'chesspunk-auth-signup-${Environment}'
      CodeUri: lambda/handlers/auth/signup
      Handler: app.lambda_handler_entry
      Runtime: python3.11
      Layers:
        - !Ref DependenciesLayer
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
      Events:
        SignupEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ChessunkAPI
            Path: /auth/signup
            Method: POST

  LoginFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'chesspunk-auth-login-${Environment}'
      CodeUri: lambda/handlers/auth/login
      Handler: app.lambda_handler_entry
      Runtime: python3.11
      Layers:
        - !Ref DependenciesLayer
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
      Events:
        LoginEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ChessunkAPI
            Path: /auth/login
            Method: POST

  # ============ Competition Functions ============
  CreateCompetitionFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'chesspunk-competition-create-${Environment}'
      CodeUri: lambda/handlers/competitions/create
      Handler: app.lambda_handler_entry
      Runtime: python3.11
      Layers:
        - !Ref DependenciesLayer
      Timeout: 30
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref CompetitionsTable
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
      Environment:
        Variables:
          COMPETITIONS_TABLE: !Ref CompetitionsTable
          USERS_TABLE: !Ref UsersTable
      Events:
        CreateCompEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ChessunkAPI
            Path: /competitions
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer

  # ============ Cognito User Pool ============
  ChessunkUserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: !Sub 'chesspunk-${Environment}'
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireUppercase: true
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: false
      Schema:
        - Name: email
          AttributeDataType: String
          Required: true
          Mutable: true
        - Name: username
          AttributeDataType: String
          Required: true
          Mutable: false
        - Name: elo
          AttributeDataType: Number
          Mutable: true

  ChessunkUserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref ChessunkUserPool
      ClientName: !Sub 'chesspunk-client-${Environment}'
      ExplicitAuthFlows:
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      GenerateSecret: false

  # ============ CloudWatch Alarms ============
  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'chesspunk-lambda-errors-${Environment}'
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 10
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref AlertTopic

  DynamoDBThrottleAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'chesspunk-dynamodb-throttle-${Environment}'
      MetricName: ConsumedWriteCapacityUnits
      Namespace: AWS/DynamoDB
      Statistic: Sum
      Period: 60
      Threshold: 100
      ComparisonOperator: GreaterThanThreshold

Outputs:
  APIEndpoint:
    Description: "API Gateway endpoint URL"
    Value: !Sub 'https://${ChessunkAPI}.execute-api.${AWS::Region}.amazonaws.com/${Environment}'
  
  UserPoolId:
    Description: "Cognito User Pool ID"
    Value: !Ref ChessunkUserPool
  
  UserPoolClientId:
    Description: "Cognito User Pool Client ID"
    Value: !Ref ChessunkUserPoolClient
```

#### 5.2 Deploy with SAM

```bash
# Install SAM CLI
pip install aws-sam-cli

# Validate template
sam validate -t template.yaml

# Build Python dependencies into layers
sam build

# Deploy to AWS
sam deploy \
  --guided \
  --parameter-overrides Environment=dev \
  --stack-name chesspunk-dev

# View outputs
aws cloudformation describe-stacks \
  --stack-name chesspunk-dev \
  --query 'Stacks[0].Outputs'
```

#### 5.3 Alternative: Terraform

```hcl
# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# DynamoDB Users Table
resource "aws_dynamodb_table" "users" {
  name           = "chesspunk-users-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Environment = var.environment
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "chesspunk-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Lambda Signup Function
resource "aws_lambda_function" "signup" {
  filename      = "lambda/handlers/auth/signup.zip"
  function_name = "chesspunk-auth-signup"
  role          = aws_iam_role.lambda_role.arn
  handler       = "app.lambda_handler_entry"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      DB_ENGINE    = "DYNAMODB"
      USERS_TABLE  = aws_dynamodb_table.users.name
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "chesspunk-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    allow_headers = ["Authorization", "Content-Type"]
  }
}

# API Route: POST /auth/signup
resource "aws_apigatewayv2_route" "signup" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /auth/signup"
  target    = "integrations/${aws_apigatewayv2_integration.signup.id}"
}

resource "aws_apigatewayv2_integration" "signup" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
  target_arn      = aws_lambda_function.signup.arn
}
```

---

### Phase 6: Testing & Optimization
**Duration:** 2-3 weeks | **Risk:** Low | **Reversible:** Yes

#### 6.1 Local Testing with SAM CLI

```bash
# Start local API Gateway + Lambda
sam local start-api

# Test endpoint
curl -X POST http://localhost:3000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@chess.com",
    "password": "SecurePass123!"
  }'
```

#### 6.2 Integration Tests with AWS

```python
# tests/test_auth_lambda.py
import boto3
import json
import pytest

@pytest.fixture
def lambda_client():
    return boto3.client('lambda', region_name='us-east-1')

@pytest.mark.asyncio
async def test_signup_lambda(lambda_client):
    """Test signup Lambda handler"""
    payload = {
        "httpMethod": "POST",
        "path": "/auth/signup",
        "body": json.dumps({
            "username": "testuser",
            "email": "test@chess.com",
            "password": "Test123!"
        }),
        "headers": {"Content-Type": "application/json"},
        "requestContext": {"requestId": "test-123"}
    }
    
    response = lambda_client.invoke(
        FunctionName='chesspunk-auth-signup-dev',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    assert response['StatusCode'] == 200
    result = json.loads(response['Payload'].read())
    assert result['statusCode'] == 201

@pytest.mark.asyncio
async def test_dynamodb_query_performance():
    """Test DynamoDB query performance"""
    import time
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('chesspunk-users-dev')
    
    start = time.time()
    response = table.query(
        IndexName='email-index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq('alice@chess.com')
    )
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # Should be <100ms
    assert len(response['Items']) > 0
```

#### 6.3 Performance Optimization

**Cold Start Reduction:**
```yaml
# template.yaml - Enable Provisioned Concurrency
SignupFunction:
  ...
  Properties:
    ...
    ReservedConcurrentExecutions: 10     # Always keep 10 warm
    ProvisionedConcurrencyConfig:
      ProvisionedConcurrentExecutions: 5 # Warm 5 instances

# Or use Lambda SnapStart (Java, requires different runtime)
```

**DynamoDB Optimization:**
```python
# Use batch operations for bulk writes
from boto3.dynamodb.conditions import Key
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('chesspunk-competitions')

with table.batch_writer(
    batch_size=25   # Max batch size for DynamoDB
) as batch:
    for match in new_matches:
        batch.put_item(Item=match)
```

**Caching with ElastiCache:**
```python
# Cache expensive queries (standings, leaderboards)
import json
import redis

cache = redis.Redis(host='chesspunk-cache.abc.ng.0001.use1.cache.amazonaws.com')

async def get_standings(comp_id: str):
    cache_key = f"standings:{comp_id}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query DynamoDB
    standings = await comp_repo.get_standings(comp_id)
    
    # Cache for 5 minutes
    cache.setex(cache_key, 300, json.dumps(standings))
    return standings
```

---

## Part 3: Migration Execution Timeline

### Recommended Timeline: 12-16 Weeks

```
Week 1-3:     Phase 1 - Code Refactoring (Framework Decoupling)
              - Extract services to framework-agnostic modules
              - Abstract authentication
              - Create HTTP request/response models
              
Week 4-7:     Phase 2-3 - DynamoDB & Repositories
              - Design DynamoDB schema with GSIs
              - Implement dual-write pattern (SQL + DynamoDB)
              - Create DynamoDB repositories
              - Migrate data, validate consistency
              
Week 8-10:    Phase 4 - Lambda Handlers
              - Create Lambda handler layer
              - Implement API Gateway event adapters
              - Handle authorization with Cognito
              - Implement error handling decorators
              
Week 11-12:   Phase 5 - Infrastructure as Code
              - Write SAM/Terraform templates
              - Deploy to AWS
              - Set up CloudWatch monitoring
              
Week 13-16:   Phase 6 - Testing & Optimization
              - Integration testing
              - Load testing
              - Cold start optimization
              - Production readiness

```

---

## Part 4: Key Architectural Decisions & Trade-offs

### Table: Architecture Decisions

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| **DynamoDB over RDS** | No JOINs, must denormalize | Cost per request, auto-scaling, serverless managed |
| **Cognito vs JWT-only** | Tighter AWS coupling | Built-in MFA, account recovery, user management |
| **Lambda per endpoint** | More code duplication | Granular monitoring, scaling, deployments |
| **On-demand billing** | Higher per-request cost for high traffic | No capacity planning, perfect for variable tournaments |
| **Embedded comments in posts** | 400KB item limit | Atomic updates, no transactional concerns |
| **Denormalized competition players** | Inconsistency risk | Fast leaderboard queries, no N+1 reads |

---

## Part 5: Cost Estimation

### AWS Pricing (Rough Estimates)

**Compute (Lambda):**
- 1 million requests/month × 500ms avg duration
- Cost: $0.20/million requests + $0.0000166667/GB-second
- ~$10-20/month (development), $100-200/month (production)

**Database (DynamoDB):**
- On-demand: $1.25 per million write units, $0.25 per million read units
- 1M reads, 100K writes/month = ~$0.30/month

**API Gateway:**
- $3.50 per million API calls
- 1M calls = $3.50/month

**Total (Development):** ~$15-30/month
**Total (Production @ 100x scale):** ~$1,500-3,000/month

*Comparison with EC2:*
- m5.large instance: $100/month (compute only)
- RDS PostgreSQL: $50-100/month
- Data transfer: $20/month
- **Total:** ~$170-220/month (fixed cost, underutilized)

**Serverless wins for variable workloads; EC2/RDS better for sustained high traffic**

---

## Part 6: Risk Mitigation

### Critical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Data loss during migration** | HIGH | Backup SQL database, dual-write validation, rollback plan |
| **DynamoDB hot partition** | MEDIUM | Design PK/SK carefully, use on-demand billing, monitor throttling |
| **Cold start latency** | MEDIUM | Provisioned concurrency, Lambda SnapStart, local caching |
| **Authentication failures** | MEDIUM | Test Cognito integration thoroughly, fallback to API key auth |
| **Query performance issues** | MEDIUM | Load test with production data, optimize GSIs, caching strategy |
| **Cost overruns** | LOW | Set CloudWatch alarms, reserved capacity for predictable components |

---

## Part 7: Code organization after migration

```
chesspunk-serverless/
├── app/
│   ├── main/python/
│   │   ├── core/                      # Pure business logic (framework-agnostic)
│   │   │   ├── services/              # Tournament logic, ELO calc, etc.
│   │   │   ├── repositories/
│   │   │   │   ├── base.py            # Abstract interfaces (unchanged)
│   │   │   │   ├── dynamodb/          # DynamoDB implementations (NEW)
│   │   │   │   ├── sql/               # SQL implementations (DEPRECATED)
│   │   │   │   └── nosql/             # MongoDB (DEPRECATED)
│   │   │   ├── schemas/               # Pydantic models for validation
│   │   │   └── auth/                  # Auth provider (framework-agnostic)
│   │   └── routers/                   # DEPRECATED - replaced by Lambda handlers
│   
│   ├── lambda/                        # NEW: Serverless handlers
│   │   ├── handlers/
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   ├── competitions/
│   │   │   ├── matches/
│   │   │   └── communities/
│   │   ├── layers/                    # Lambda layer dependencies
│   │   └── shared/
│   │       ├── auth.py                # Cognito/JWT verification
│   │       ├── decorators.py          # Logging, error handling
│   │       └── models.py              # HTTP request/response adapters
│   
│   └── tests/
│       ├── unit/                      # Services (no AWS SDK needed)
│       ├── integration/               # Lambda handlers (with SAM CLI)
│       └── e2e/                       # Full AWS stack
│
├── infrastructure/
│   ├── template.yaml                  # AWS SAM definition
│   ├── terraform/                     # Alternative IaC
│   └── monitoring/
│       └── alarms.yaml                # CloudWatch alarm definitions
│
├── scripts/
│   ├── migrate_sql_to_dynamodb.py     # Data migration script
│   ├── validate_migration.py          # Consistency checks
│   └── rollback.py                    # Emergency rollback
│
└── docs/
    ├── SERVERLESS_MIGRATION_GUIDE.md  # This file
    ├── DYNAMODB_DESIGN.md             # Schema rationale
    └── LAMBDA_DEVELOPMENT.md          # Handler development guide
```

---

## Conclusion

This migration transforms Chesspunk from a traditional FastAPI application to a fully
serverless architecture with:

✅ **Zero infrastructure management**
✅ **Automatic scaling** based on demand
✅ **Pay-per-request pricing**
✅ **Native AWS integration** (Cognito, CloudWatch, X-Ray)
✅ **Improved development velocity** (deploy individual functions)

The key to success is phased migration with careful validation at each step, starting
with code refactoring (lowest risk) and progressing to infrastructure changes (highest risk).
