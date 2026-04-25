# Chesspunk Serverless Deployment Guide

Welcome to the `serverless` architecture layer of Chesspunk! This sub-system decouples the core API logic away from the localized ASGI server (FastAPI) and deploys it as highly-available, independently scaling **AWS Lambda functions** natively managed by the **Serverless Framework**.

## Architecture Overview

This deployment strategy provisions the following resources natively in AWS:
- **Compute**: Isolated synchronous Boto3 Python 3.10 hooks executed on **AWS Lambda**.
- **Database**: On-demand (PAY_PER_REQUEST) **AWS DynamoDB** backing tables for `Users`, `Competitions`, `Communities`, and `Social` schemas.
- **Routing**: **AWS API Gateway** mapping the HTTP paths directly onto Lambda targets.
- **Authentication**: **AWS Cognito** User Pools and Identity Apps safeguarding protected endpoints strictly.
- **Edge Acceleration**: A distributed **Amazon CloudFront** distribution caching the API Gateway targets securely around the world via TLS.

---

## 1. Prerequisites

Before deploying the serverless stack, ensure your local workstation satisfies these requirements:
1. **Node.js (>= 18.x)**: Required to install and run the Serverless Framework CLI.
2. **AWS CLI**: Configured locally with valid `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` representing a user with CloudFormation deployment authority.
3. **Conda & Python 3.10**: Required to execute the local Python tests mimicking the lambdas securely.

## 2. Installation & Setup

Navigate into the root application directory (`app/`) and install the serverless automation plugins:

```bash
# Initialize Node packages natively 
npm init -y

# Install the Serverless Framework CLI & Plugin Requirements
npm install -g serverless
npx serverless plugin install -n serverless-python-requirements
```

Because **Serverless Framework V.4** now strictly enforces authentication bounds, you must login or register a dashboard identity before usage:

```bash
npx serverless login
```

## 3. Local Testing

We utilize native mocked evaluation via `pytest` and `moto` to ensure our DynamoDB pipelines operate effectively before syncing onto the cloud.

The entire test suite is orchestrated simply via `tox`:

```bash
# Evaluate the serverless logic exclusively bypassing local ASGI bugs
conda run -n fastapi tox -e py310-serverless
```
*(This triggers all tests located natively under `tests/python/serverless/*`)*

## 4. Deployment

Once authenticated via the Serverless CLI and locally tested, deploying the Infrastructure-as-Code natively across your active AWS profile only requires a single command:

```bash
# Deploy to your default AWS profile and region (us-east-1) dynamically
npx serverless deploy --stage dev
```

### What happens when you deploy?
1. The `serverless-python-requirements` plugin bundles all strictly necessary pip dependencies (e.g. `boto3`).
2. CloudFormation provisions the `AWS::Cognito`, `AWS::DynamoDB`, and `AWS::CloudFront` blueprints dynamically.
3. The server natively provisions API gateway hooks, attaches the Cognito Authorizer, and registers the serverless endpoints. 

Upon success, the CLI will output the active **API Gateway URL** as well as your accelerated **CloudFront Edge URL**. Use these endpoints to begin testing authentication and request cycles directly!

## 5. Teardown (Optional)

If evaluating temporary deployments or rotating configurations, clean up the AWS pipeline purely via the framework:

```bash
# Erase all dynamic CloudFormation artifacts including DynamoDB schemas natively!
npx serverless remove --stage dev
```
