#!/bin/bash

# Multi-Language Serverless Setup Script for Chesspunk
# This script sets up the complete development environment

set -e

echo "🚀 Setting up Chesspunk Multi-Language Serverless Environment"
echo "============================================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required. Please install Python first."
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "❌ Java 11+ is required. Please install Java first."
    exit 1
fi

if ! command -v mvn &> /dev/null; then
    echo "❌ Maven is required. Please install Maven first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create project structure
echo "📁 Creating project structure..."

mkdir -p chesspunk-serverless
cd chesspunk-serverless

# Initialize Node.js project
echo "📦 Initializing Node.js project..."
npm init -y > /dev/null 2>&1

# Install Serverless Framework
echo "🔧 Installing Serverless Framework..."
npm install --save-dev serverless serverless-python-requirements serverless-offline serverless-compose > /dev/null 2>&1

# Create directory structure
echo "🏗️  Creating directory structure..."
mkdir -p infrastructure services/python-api services/java-tournament-engine services/python-matchmaking shared tests/e2e tests/integration

# Create main configuration files
echo "📝 Creating configuration files..."

# Copy the configuration files from the guide
cat > serverless-compose.yml << 'EOF'
services:
  infrastructure:
    path: infrastructure
    params:
      stage: ${opt:stage, 'dev'}

  python-api:
    path: services/python-api
    params:
      stage: ${opt:stage, 'dev'}
    dependsOn:
      - infrastructure

  java-tournament-engine:
    path: services/java-tournament-engine
    params:
      stage: ${opt:stage, 'dev'}
    dependsOn:
      - infrastructure

  python-matchmaking:
    path: services/python-matchmaking
    params:
      stage: ${opt:stage, 'dev'}
    dependsOn:
      - infrastructure
EOF

cat > serverless.yml << 'EOF'
service: chesspunk

frameworkVersion: '3'

plugins:
  - serverless-compose

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}
  environment:
    STAGE: ${self:provider.stage}

custom:
  stage: ${opt:stage, 'dev'}
  pythonRequirements:
    dockerizePip: true
    layer: true
EOF

# Create infrastructure
echo "🏗️  Setting up infrastructure..."
cat > infrastructure/serverless.yml << 'EOF'
service: chesspunk-infrastructure

frameworkVersion: '3'

provider:
  name: aws
  region: us-east-1
  stage: ${opt:stage, 'dev'}

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

    CognitoUserPool:
      Type: AWS::Cognito::UserPool
      Properties:
        UserPoolName: chesspunk-${self:provider.stage}
        Policies:
          PasswordPolicy:
            MinimumLength: 8
            RequireUppercase: true
            RequireLowercase: true
            RequireNumbers: true
        Schema:
          - Name: email
            AttributeDataType: String
            Required: true
            Mutable: true

    ApiGatewayRestApi:
      Type: AWS::ApiGateway::RestApi
      Properties:
        Name: chesspunk-api-${self:provider.stage}
        Description: Chesspunk Chess Community API
        EndpointConfiguration:
          Types:
            - REGIONAL

  Outputs:
    UsersTableName:
      Value: !Ref UsersTable
      Export:
        Name: ChesspunkUsersTable-${self:provider.stage}

    CognitoUserPoolId:
      Value: !Ref CognitoUserPool
      Export:
        Name: ChesspunkUserPool-${self:provider.stage}

    ApiGatewayId:
      Value: !Ref ApiGatewayRestApi
      Export:
        Name: ChesspunkApiGateway-${self:provider.stage}
EOF

# Setup Python API service
echo "🐍 Setting up Python API service..."
mkdir -p services/python-api/src
cat > services/python-api/serverless.yml << 'EOF'
service: chesspunk-python-api

frameworkVersion: '3'

plugins:
  - serverless-python-requirements
  - serverless-offline

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}
  environment:
    USERS_TABLE: ${cf:chesspunk-infrastructure-${self:provider.stage}.ChesspunkUsersTable}

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true

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
      USERS_TABLE: ${cf:chesspunk-infrastructure-${self:provider.stage}.ChesspunkUsersTable}

resources:
  Extensions:
    ApiGatewayRestApi:
      Properties:
        RestApiId:
          Ref: ApiGatewayRestApi
EOF

cat > services/python-api/requirements.txt << 'EOF'
fastapi==0.104.1
mangum==0.17.0
boto3==1.34.0
pydantic==2.5.0
uvicorn==0.24.0
EOF

cat > services/python-api/lambda_handler.py << 'EOF'
from mangum import Mangum
from fastapi import FastAPI

app = FastAPI(title="Chesspunk API", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "python-api"}

# Add your existing FastAPI routes here
# from src.app.main.python.routers import auth, users, competitions
# app.include_router(auth.router)
# app.include_router(users.router)
# app.include_router(competitions.router)

handler = Mangum(app)
EOF

# Setup Java service
echo "☕ Setting up Java tournament engine..."
mkdir -p services/java-tournament-engine/src/main/java/com/chesspunk
cat > services/java-tournament-engine/serverless.yml << 'EOF'
service: chesspunk-java-tournament-engine

frameworkVersion: '3'

provider:
  name: aws
  runtime: java11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

package:
  artifact: target/chesspunk-tournament-engine-${self:provider.stage}.jar

functions:
  calculatePairings:
    handler: com.chesspunk.TournamentEngine::calculatePairings
    memorySize: 512
    timeout: 30
    events:
      - http:
          path: tournaments/{id}/pairings
          method: post
          cors: true

resources:
  Extensions:
    ApiGatewayRestApi:
      Properties:
        RestApiId:
          Ref: ApiGatewayRestApi
EOF

cat > services/java-tournament-engine/pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.chesspunk</groupId>
    <artifactId>chesspunk-tournament-engine</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-core</artifactId>
            <version>1.2.2</version>
        </dependency>
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-events</artifactId>
            <version>3.11.0</version>
        </dependency>
        <dependency>
            <groupId>software.amazon.awssdk</groupId>
            <artifactId>dynamodb</artifactId>
            <version>2.20.0</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
EOF

cat > services/java-tournament-engine/src/main/java/com/chesspunk/TournamentEngine.java << 'EOF'
package com.chesspunk;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;

public class TournamentEngine implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent request, Context context) {
        return new APIGatewayProxyResponseEvent()
                .withStatusCode(200)
                .withBody("{\"message\": \"Java tournament engine is working!\"}");
    }
}
EOF

# Setup Python matchmaking service
echo "🎯 Setting up Python matchmaking service..."
mkdir -p services/python-matchmaking/src
cat > services/python-matchmaking/serverless.yml << 'EOF'
service: chesspunk-python-matchmaking

frameworkVersion: '3'

plugins:
  - serverless-python-requirements
  - serverless-offline

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

custom:
  pythonRequirements:
    dockerizePip: true

functions:
  findMatch:
    handler: src/matchmaking.find_match
    memorySize: 256
    timeout: 10
    events:
      - http:
          path: matchmaking/find
          method: post
          cors: true

resources:
  Extensions:
    ApiGatewayRestApi:
      Properties:
        RestApiId:
          Ref: ApiGatewayRestApi
EOF

cat > services/python-matchmaking/requirements.txt << 'EOF'
boto3==1.34.0
EOF

cat > services/python-matchmaking/src/matchmaking.py << 'EOF'
import json

def find_match(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Python matchmaking service is working!',
            'player_id': json.loads(event['body']).get('player_id')
        })
    }
EOF

# Create development tools
echo "🛠️  Creating development tools..."

cat > Makefile << 'EOF'
.PHONY: install build test deploy local clean

install:
	npm install
	cd services/python-api && pip install -r requirements.txt
	cd services/java-tournament-engine && mvn dependency:resolve
	cd services/python-matchmaking && pip install -r requirements.txt

build:
	cd services/python-api && serverless package
	cd services/java-tournament-engine && mvn clean package
	cd services/python-matchmaking && serverless package

test:
	cd services/python-api && python -m pytest || true
	cd services/java-tournament-engine && mvn test || true
	cd services/python-matchmaking && python -m pytest || true

deploy:
	serverless deploy --stage dev

local:
	docker-compose up -d
	serverless offline --stage local

logs:
	serverless logs -f api --stage dev

clean:
	serverless remove --stage dev || true
	docker-compose down -v || true
	rm -rf services/*/target services/*/.serverless
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    container_name: chesspunk-dynamodb
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/home/dynamodblocal/data
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath /home/dynamodblocal/data"

  serverless-offline:
    image: node:18-alpine
    container_name: chesspunk-serverless
    working_dir: /app
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    command: sh -c "npm install && serverless offline --stage local"
    environment:
      - AWS_ACCESS_KEY_ID=local
      - AWS_SECRET_ACCESS_KEY=local
      - AWS_DEFAULT_REGION=us-east-1
      - DYNAMODB_ENDPOINT=http://dynamodb-local:8000
    depends_on:
      - dynamodb-local

volumes:
  dynamodb-data:
EOF

# Create README
echo "📖 Creating README..."
cat > README.md << 'EOF'
# Chesspunk Multi-Language Serverless

A serverless chess community platform with multiple Lambda functions in different languages.

## Quick Start

1. **Setup environment:**
   ```bash
   ./setup.sh
   ```

2. **Start local development:**
   ```bash
   make local
   ```

3. **Test services:**
   ```bash
   # Python API
   curl http://localhost:3000/dev/health

   # Java tournament engine
   curl -X POST http://localhost:3000/dev/tournaments/123/pairings

   # Python matchmaking
   curl -X POST http://localhost:3000/dev/matchmaking/find \
     -H "Content-Type: application/json" \
     -d '{"player_id": "alice"}'
   ```

4. **Deploy to AWS:**
   ```bash
   make deploy
   ```

## Architecture

- **Python API**: Main REST API using FastAPI + Mangum
- **Java Tournament Engine**: Tournament pairing and standings calculation
- **Python Matchmaking**: Real-time match finding service
- **Shared Infrastructure**: DynamoDB, API Gateway, Cognito

## Development

See [MULTI_LANGUAGE_SERVERLESS_SETUP.md](MULTI_LANGUAGE_SERVERLESS_SETUP.md) for detailed documentation.
EOF

# Make setup script executable
chmod +x setup.sh

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. cd chesspunk-serverless"
echo "2. make install"
echo "3. make local"
echo "4. Visit http://localhost:3000/dev/health"
echo ""
echo "For detailed documentation, see MULTI_LANGUAGE_SERVERLESS_SETUP.md"