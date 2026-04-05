# Mangum Alternative: Running FastAPI on AWS Lambda

## Overview

**Mangum** is an ASGI adapter that allows running FastAPI applications directly on AWS Lambda, providing a **less disruptive** alternative to the full serverless migration.

## How Mangum Works

```python
# app/main/python/routers/main.py (modified)
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

# Your existing FastAPI routes...
@app.get("/users")
async def list_users():
    # Your existing code
    pass

# Add Mangum handler for Lambda
handler = Mangum(app)
```

**Architecture:**
```
API Gateway → Lambda (with Mangum) → FastAPI App → Repository → DynamoDB
```

## Pros & Cons vs Full Serverless Migration

### ✅ Advantages of Mangum Approach

| Aspect | Mangum | Full Serverless Migration |
|--------|--------|---------------------------|
| **Code Changes** | Minimal (add 2 lines) | Extensive (rewrite all handlers) |
| **FastAPI Features** | 100% preserved | Lost (Dependency Injection, middleware) |
| **Development Speed** | Fast (weeks, not months) | Slow (3-4 months) |
| **Testing** | Existing tests work | Need to rewrite for Lambda |
| **Debugging** | Standard FastAPI debugging | Lambda-specific debugging |
| **Cold Starts** | Same issue | Same issue |

### ⚠️ Disadvantages of Mangum Approach

| Issue | Impact | Mitigation |
|-------|--------|-----------|
| **Single Lambda Function** | All endpoints share one function | Use API Gateway routing, monitor performance |
| **Memory/Timeout Limits** | 10GB RAM, 15min timeout | Optimize for common paths, split if needed |
| **No Granular Scaling** | All traffic hits one function | API Gateway throttling, Lambda concurrency limits |
| **Not "Serverless Native"** | Still running a web server in Lambda | Consider full migration for high scale |
| **Cost** | Higher for sustained traffic | Better for bursty workloads |

## Implementation Steps

### Step 1: Add Mangum to Dependencies

```python
# requirements.txt
fastapi==0.104.1
mangum==0.17.0
# ... existing dependencies
```

### Step 2: Modify FastAPI App for Lambda

```python
# app/main/python/routers/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from routers import auth, users, competitions, matches, communities
from core.config import settings
from core.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database connections
    if os.getenv("DB_ENGINE", "SQL") == "NOSQL":
        # MongoDB initialization
        pass
    else:
        # SQL database initialization
        await init_db()
    
    yield
    
    # Shutdown: Close connections
    pass

app = FastAPI(
    title="Chesspunk API",
    lifespan=lifespan,
    # Disable docs in production Lambda
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "prod" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "prod" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(competitions.router, prefix="/competitions", tags=["Competitions"])
app.include_router(matches.router, prefix="/matches", tags=["Matches"])
app.include_router(communities.router, prefix="/communities", tags=["Communities"])

# Health check for Lambda
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "chesspunk"}

# Mangum handler for AWS Lambda
handler = Mangum(app, lifespan="off")  # Disable lifespan in Lambda
```

### Step 3: Lambda Handler Entry Point

```python
# lambda_handler.py (new file in root)
from app.main.python.routers.main import handler

# This is the Lambda entry point
def lambda_handler(event, context):
    return handler(event, context)
```

### Step 4: AWS SAM Template for Mangum

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2.0

Parameters:
  Environment:
    Type: String
    Default: dev

Globals:
  Function:
    Timeout: 30
    MemorySize: 1024
    Runtime: python3.11
    Environment:
      Variables:
        DB_ENGINE: DYNAMODB
        ENVIRONMENT: !Ref Environment

Resources:
  # DynamoDB Tables (same as before)
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'chesspunk-users-${Environment}'
      BillingMode: PAY_PER_REQUEST
      # ... table definition

  # Single Lambda Function with Mangum
  ChessunkAPIFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'chesspunk-api-${Environment}'
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 30
      Layers:
        - !Ref DependenciesLayer
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
        - DynamoDBCrudPolicy:
            TableName: !Ref CompetitionsTable
        - DynamoDBCrudPolicy:
            TableName: !Ref MatchesTable
        - DynamoDBCrudPolicy:
            TableName: !Ref CommunitiesTable
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
          COMPETITIONS_TABLE: !Ref CompetitionsTable
          MATCHES_TABLE: !Ref MatchesTable
          COMMUNITIES_TABLE: !Ref CommunitiesTable
      Events:
        # All API routes go to the same Lambda function
        AnyApi:
          Type: Api
          Properties:
            RestApiId: !Ref ChessunkAPI
            Path: /{proxy+}
            Method: ANY

  # API Gateway
  ChessunkAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Cors:
        AllowHeaders: "'Authorization,Content-Type'"
        AllowMethods: "'GET,POST,PUT,DELETE,PATCH,OPTIONS'"
        AllowOrigin: "'*'"
        MaxAge: "'600'"
      MethodSettings:
        - ResourcePath: /{proxy+}
          HttpMethod: "*"
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true

  # Dependencies Layer
  DependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub 'chesspunk-dependencies-${Environment}'
      ContentUri: lambda/layers/
      CompatibleRuntimes:
        - python3.11
```

## Database Migration (Still Required)

Mangum doesn't change the database requirements. You still need to migrate from PostgreSQL to DynamoDB:

### Option A: Keep PostgreSQL with Aurora Serverless

```yaml
# Add Aurora Serverless cluster
AuroraCluster:
  Type: AWS::RDS::DBCluster
  Properties:
    Engine: aurora-postgresql
    EngineMode: serverless
    ScalingConfiguration:
      MinCapacity: 0.5
      MaxCapacity: 4
      AutoPause: true
      SecondsUntilAutoPause: 300
```

**Pros:** Minimal code changes, familiar SQL queries
**Cons:** Higher cost than DynamoDB, not truly serverless

### Option B: Migrate to DynamoDB (Recommended)

Still need the DynamoDB repositories and schema from the full migration guide.

## Performance Considerations

### Cold Start Optimization

```yaml
# template.yaml - Provisioned Concurrency
ChessunkAPIFunction:
  Type: AWS::Serverless::Function
  Properties:
    # ...
    ReservedConcurrentExecutions: 5    # Always keep 5 instances warm
    ProvisionedConcurrencyConfig:
      ProvisionedConcurrentExecutions: 2  # Warm 2 instances
```

### Memory Tuning

```yaml
# Start with 1024MB, monitor and adjust
MemorySize: 1024  # Increase to 2048MB if needed
```

### API Gateway Caching

```yaml
ChessunkAPI:
  Type: AWS::Serverless::Api
  Properties:
    # ...
    Caching:
      Enabled: true
      TtlInSeconds: 300  # 5-minute cache for GET requests
```

## Comparison: Mangum vs Full Serverless

| Criteria | Mangum Approach | Full Serverless Migration |
|----------|-----------------|---------------------------|
| **Migration Time** | 2-4 weeks | 12-16 weeks |
| **Code Changes** | Minimal | Extensive |
| **FastAPI Compatibility** | 100% | 0% (lose middleware, DI) |
| **Scaling Granularity** | Function level | Endpoint level |
| **Cold Start Impact** | High (large function) | Medium (smaller functions) |
| **Cost Efficiency** | Good for moderate traffic | Better for variable traffic |
| **Monitoring** | API Gateway + CloudWatch | Per-function metrics |
| **Development Experience** | Familiar FastAPI | Lambda-specific patterns |

## When to Choose Mangum

### ✅ Good Fit Scenarios

1. **Time Constraints**: Need to migrate quickly (2-4 weeks vs 3-4 months)
2. **Small Team**: Don't have resources for full rewrite
3. **Moderate Traffic**: <10M requests/month
4. **Keep FastAPI Features**: Need Dependency Injection, middleware, etc.
5. **Familiar Patterns**: Want to keep existing FastAPI development workflow

### ❌ Poor Fit Scenarios

1. **High Scale**: >100M requests/month (single function bottleneck)
2. **Variable Traffic**: Chess tournaments create traffic spikes
3. **Cost Optimization**: Need granular per-endpoint scaling
4. **Serverless Native**: Want to embrace serverless patterns fully
5. **Microservices**: Plan to split into separate services later

## Hybrid Approach Recommendation

For **Chesspunk**, I recommend a **hybrid approach**:

### Phase 1: Quick Win with Mangum (4 weeks)
- Deploy existing FastAPI app to Lambda using Mangum
- Migrate database to DynamoDB (repositories already exist)
- Get running on serverless infrastructure quickly

### Phase 2: Optimize for Scale (8 weeks)
- If traffic grows, split high-traffic endpoints to separate Lambda functions
- Implement per-endpoint scaling and monitoring
- Consider full serverless migration for core tournament logic

## Implementation Code

Would you like me to show you the specific code changes needed to integrate Mangum with your existing FastAPI application?