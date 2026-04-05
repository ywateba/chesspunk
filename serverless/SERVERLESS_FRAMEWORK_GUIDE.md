# Serverless Framework for Chesspunk Migration

## What is the Serverless Framework?

The **Serverless Framework** is an open-source CLI tool that simplifies deploying and managing serverless applications across multiple cloud providers (AWS, Azure, Google Cloud, etc.).

## Key Features

### ✅ Multi-Provider Support
```yaml
# serverless.yml
service: chesspunk

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: dev

# Or switch to Google Cloud:
provider:
  name: google
  runtime: python311
```

### ✅ Plugin Ecosystem
```yaml
plugins:
  - serverless-python-requirements  # Auto-package dependencies
  - serverless-offline             # Local development
  - serverless-dynamodb-local      # Local DynamoDB
  - serverless-step-functions      # Workflow orchestration
```

### ✅ Rich CLI Commands
```bash
serverless deploy        # Deploy entire stack
serverless deploy -f     # Deploy single function
serverless invoke        # Test functions locally/remotely
serverless logs          # View function logs
serverless remove        # Clean up resources
```

## Serverless Framework vs AWS SAM

| Feature | Serverless Framework | AWS SAM |
|---------|---------------------|---------|
| **Language** | YAML/JSON | YAML/JSON |
| **Provider Support** | AWS, Azure, GCP, IBM | AWS only |
| **CLI** | `sls` or `serverless` | `sam` |
| **Local Testing** | `serverless-offline` | `sam local` |
| **Deployment** | `serverless deploy` | `sam deploy` |
| **Community** | Large, active | AWS-backed |
| **Learning Curve** | Gentle | Gentle |

## Chesspunk Serverless Configuration

### Option 1: Mangum Approach (Single Function)

```yaml
# serverless.yml
service: chesspunk-api

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}
  environment:
    DB_ENGINE: DYNAMODB
    ENVIRONMENT: ${self:provider.stage}

plugins:
  - serverless-python-requirements
  - serverless-offline

package:
  exclude:
    - node_modules/**
    - .git/**
    - tests/**

functions:
  api:
    handler: lambda_handler.lambda_handler
    memorySize: 1024
    timeout: 30
    events:
      - http:
          path: /{proxy+}
          method: any
          cors: true
    environment:
      USERS_TABLE: !Ref UsersTable
      COMPETITIONS_TABLE: !Ref CompetitionsTable

resources:
  Resources:
    UsersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: chesspunk-users-${self:provider.stage}
        BillingMode: PAY_PER_REQUEST
        AttributeDefinitions:
          - AttributeName: PK
            AttributeType: S
          - AttributeName: SK
            AttributeType: S
          - AttributeName: email
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

    CompetitionsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: chesspunk-competitions-${self:provider.stage}
        BillingMode: PAY_PER_REQUEST
        # ... table definitions
```

### Option 2: Multi-Function Approach (Full Serverless)

```yaml
# serverless.yml
service: chesspunk

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

plugins:
  - serverless-python-requirements
  - serverless-offline

package:
  individually: true  # Each function packages separately

functions:
  signup:
    handler: app/lambda/handlers/auth/signup.lambda_handler_entry
    memorySize: 512
    timeout: 10
    events:
      - http:
          path: auth/signup
          method: post
          cors: true
    environment:
      USERS_TABLE: !Ref UsersTable

  login:
    handler: app/lambda/handlers/auth/login.lambda_handler_entry
    memorySize: 512
    timeout: 10
    events:
      - http:
          path: auth/login
          method: post
          cors: true
    environment:
      USERS_TABLE: !Ref UsersTable

  createCompetition:
    handler: app/lambda/handlers/competitions/create.lambda_handler_entry
    memorySize: 1024
    timeout: 30
    events:
      - http:
          path: competitions
          method: post
          cors: true
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: !Ref CognitoAuthorizer
    environment:
      COMPETITIONS_TABLE: !Ref CompetitionsTable
      USERS_TABLE: !Ref UsersTable

  # ... more functions

resources:
  Resources:
    # DynamoDB Tables
    UsersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        # ... table definition

    # Cognito User Pool
    CognitoUserPool:
      Type: AWS::Cognito::UserPool
      Properties:
        UserPoolName: chesspunk-${self:provider.stage}
        Policies:
          PasswordPolicy:
            MinimumLength: 8
        Schema:
          - Name: email
            Required: true

    CognitoUserPoolClient:
      Type: AWS::Cognito::UserPoolClient
      Properties:
        UserPoolId: !Ref CognitoUserPool
        ClientName: chesspunk-client-${self:provider.stage}

    # API Gateway Authorizer
    CognitoAuthorizer:
      Type: AWS::ApiGateway::Authorizer
      Properties:
        RestApiId: !Ref ApiGatewayRestApi
        Type: COGNITO_USER_POOLS
        ProviderARNs:
          - !GetAtt CognitoUserPool.Arn
```

## Installation & Setup

### 1. Install Serverless Framework
```bash
npm install -g serverless
```

### 2. Initialize Project
```bash
cd chesspunk
serverless
# Or create from template:
serverless create --template aws-python3 --path chesspunk-serverless
```

### 3. Configure AWS Credentials
```bash
serverless config credentials --provider aws --key <key> --secret <secret>
# Or use AWS CLI: aws configure
```

### 4. Deploy
```bash
serverless deploy
# Or deploy to specific stage:
serverless deploy --stage production
```

## Local Development

### Serverless Offline Plugin
```bash
npm install --save-dev serverless-offline
```

```yaml
# serverless.yml
plugins:
  - serverless-offline

# Add to functions
functions:
  api:
    # ...
    events:
      - http:
          path: /{proxy+}
          method: any
```

```bash
serverless offline
# API available at http://localhost:3000
```

### Local DynamoDB
```bash
npm install --save-dev serverless-dynamodb-local
```

```yaml
# serverless.yml
plugins:
  - serverless-dynamodb-local

custom:
  dynamodb:
    start:
      port: 8000
      inMemory: true
      migrate: true
    stages:
      - dev
```

## Advanced Features

### Custom Domains
```yaml
# serverless.yml
plugins:
  - serverless-domain-manager

custom:
  customDomain:
    domainName: api.chesspunk.com
    basePath: ''
    stage: ${self:provider.stage}
    createRoute53Record: true
```

### Environment Variables
```yaml
# serverless.yml
provider:
  environment:
    NODE_ENV: ${self:provider.stage}
    DB_ENGINE: DYNAMODB

functions:
  api:
    environment:
      TABLE_NAME: !Ref MyTable
```

### Layers for Dependencies
```yaml
# serverless.yml
layers:
  pythonRequirements:
    path: python_requirements
    compatibleRuntimes:
      - python3.11

functions:
  api:
    layers:
      - { Ref: PythonRequirementsLambdaLayer }
```

### Monitoring & Alerts
```yaml
# serverless.yml
plugins:
  - serverless-plugin-aws-alerts

custom:
  alerts:
    stages:
      - production
    topics:
      alarm: arn:aws:sns:us-east-1:123456789:alerts
    alarms:
      - functionErrors
      - functionDuration
      - functionThrottles
      - functionInvocations
```

## Comparison with AWS SAM

### When to Choose Serverless Framework:

✅ **Multi-cloud deployments** (AWS + GCP + Azure)
✅ **Rich plugin ecosystem** (offline dev, custom domains, etc.)
✅ **Simpler syntax** for complex deployments
✅ **Active community** and extensive documentation
✅ **Better local development** experience

### When to Choose AWS SAM:

✅ **AWS-only focus** (deeper AWS integration)
✅ **Official AWS tooling** (better support)
✅ **SAM CLI local testing** (good for Lambda + API Gateway)
✅ **CloudFormation native** (advanced AWS features)
✅ **Free** (no additional tooling cost)

## Recommendation for Chesspunk

**Use Serverless Framework** because:

1. **Better local development** - `serverless-offline` is excellent
2. **Plugin ecosystem** - `serverless-python-requirements` handles packaging
3. **Multi-stage support** - easy dev/staging/prod deployments
4. **Community** - more examples and help available
5. **Flexibility** - can start with Mangum, migrate to multi-function later

## Quick Start Commands

```bash
# Install
npm install -g serverless

# Create project
cd chesspunk
serverless create --template aws-python3

# Configure
serverless config credentials --provider aws --key XXX --secret XXX

# Deploy
serverless deploy --stage dev

# Test locally
serverless offline

# View logs
serverless logs -f api

# Clean up
serverless remove
```

The Serverless Framework would be an excellent choice for deploying Chesspunk to AWS Lambda, especially with its strong local development capabilities and plugin ecosystem.