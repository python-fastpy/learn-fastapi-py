# AWS API Gateway: Usage Plans, Custom Domains & Stages — Complete Guide

---

## Table of Contents

1. [Three Core Concepts](#1-three-core-concepts)
2. [API Stage — The Central Connection Point](#2-api-stage--the-central-connection-point)
3. [Custom Domain — Friendly URL Layer](#3-custom-domain--friendly-url-layer)
4. [Usage Plan — Throttling & Quota Layer](#4-usage-plan--throttling--quota-layer)
5. [How They Connect — The Stage is the Glue](#5-how-they-connect--the-stage-is-the-glue)
6. [Complete Request Flow](#6-complete-request-flow)
7. [Step-by-Step Setup in AWS Console](#7-step-by-step-setup-in-aws-console)
8. [CloudFormation / SAM Template](#8-cloudformation--sam-template)
9. [Key Takeaways](#9-key-takeaways)

---

## 1. Three Core Concepts

| Concept | What It Is | Purpose |
|---------|-----------|---------|
| **API Stage** | A named deployment snapshot of your API (e.g., `dev`, `qa`, `prod`) | Gives your API a URL and environment-specific config |
| **Custom Domain** | A friendly domain name (e.g., `api.example.com`) mapped to your API | Replaces the ugly default `abc123.execute-api...` URL |
| **Usage Plan** | Rate limiting + quota rules + API keys | Controls who can call your API and how much |

### Relationship Summary

```
Custom Domain ──► maps to ──► API Stage ◄── attached to ◄── Usage Plan
                                  │
                          (Stage is the GLUE)
                                  │
                                  ▼
                          Lambda / Integration
```

- Custom Domain and Usage Plan DO NOT link to each other directly
- Both independently reference the same API Stage
- The API Stage is the central connection point

---

## 2. API Stage — The Central Connection Point

### What is a Stage?

A Stage is a **named label + configuration** attached to a **deployment snapshot** of your API. Think of it as an environment (dev, qa, prod) for your API.

```
API (my-api)
│
├── Stage: dev    →  https://abc123.execute-api.us-east-1.amazonaws.com/dev
├── Stage: qa     →  https://abc123.execute-api.us-east-1.amazonaws.com/qa
└── Stage: prod   →  https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

### How a Stage is Created

A stage is created **during API deployment** — there is no standalone "Create Stage" action.

```
Step 1: Define your API (routes, methods, integrations)
               │
Step 2: Click "Deploy API" button (top right of Resources page)
               │
Step 3: In the popup:
               │
               ├── Choose [New Stage] from dropdown → type stage name (e.g., "prod")
               │   (This CREATES a new stage)
               │
               └── OR choose an existing stage (e.g., "prod")
                   (This UPDATES the existing stage with latest API config)
               │
Step 4: Stage now exists with its own URL
```

```
API Definition  ──deploy──►  Deployment (frozen snapshot)  ──assign──►  Stage ("prod")
                              (immutable)                                (mutable config)
```

- **Deployment** = immutable snapshot of your API routes and integrations
- **Stage** = mutable label + environment config attached to a deployment
- Every time you change your API, you must re-deploy to a stage for changes to go live

### What You Can Configure Per Stage

| Setting | Example |
|---------|---------|
| Stage variables | `${stageVariables.tableName}` → `users-dev` vs `users-prod` |
| Throttling limits | dev: 10 req/s, prod: 1000 req/s |
| Logging level | dev: full logging, prod: errors only |
| Caching | dev: disabled, prod: enabled |
| Lambda alias/version | dev → `$LATEST`, prod → `v5` |
| WAF Web ACL | Attach different firewall rules |
| X-Ray Tracing | Enable/disable per stage |

### Console Path

```
API Gateway → APIs → [Your API] → Stages (left sidebar) → prod
│
├── Stage Editor tab   → Cache, Throttling, WAF
├── Logs/Tracing tab   → CloudWatch, Access Logging, X-Ray
├── Stage Variables tab → Key-value pairs
├── SDK Generation tab  → Generate client SDK
└── Export tab          → Export as Swagger/OpenAPI
```

---

## 3. Custom Domain — Friendly URL Layer

### What Problem It Solves

Without custom domain:
```
https://abc123.execute-api.us-east-1.amazonaws.com/prod/users
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ugly, changes if you recreate the API
```

With custom domain:
```
https://api.example.com/v1/users
        ^^^^^^^^^^^^^^^
        stable, branded, professional
```

### Components

```
Custom Domain (api.example.com)
│
├── ACM Certificate     → SSL/TLS for your domain
├── Endpoint Type       → Regional or Edge-optimized
├── API Gateway Domain   → d-xxx.execute-api.us-east-1.amazonaws.com
│   Name                  (this is what DNS points to)
│
└── API Mappings         → Routes to API Stage(s)
    ├── /v1  → my-api / prod
    ├── /v2  → my-api-v2 / prod
    └── /admin → admin-api / prod
```

### How Custom Domain Connects to Stage

```
Custom Domain
      │
      ├── API Mapping (you create this manually)
      │   ├── API:        my-api       ← select from dropdown
      │   ├── Stage:      prod         ← select from dropdown
      │   └── Base Path:  /v1          ← optional prefix
      │
      └── DNS Record (Route 53)
          ├── Record:     api.example.com
          ├── Type:       A (Alias)
          └── Target:     d-xxx.execute-api... (API Gateway domain name)
```

### Where to Find the API Gateway Domain Name

```
API Gateway Console
└── Custom Domain Names
    └── api.example.com
        └── Configuration tab
            └── API Gateway domain name: d-abc123.execute-api.us-east-1.amazonaws.com
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                          THIS is what you put in Route 53 as the alias target
```

---

## 4. Usage Plan — Throttling & Quota Layer

### What It Does

Controls **how much** and **how fast** clients can call your API using API keys.

```
Usage Plan: "Premium Plan"
│
├── Throttle Settings
│   ├── Rate:   1000 requests/second    (steady-state)
│   └── Burst:  500 requests            (spike allowance)
│
├── Quota Settings
│   ├── Limit:  100,000 requests
│   └── Period: per MONTH
│
├── Associated API Stages              ← links to stage
│   └── my-api / prod
│
└── API Keys                           ← clients use these
    ├── CustomerA-Key: ak-xxxx1111
    ├── CustomerB-Key: ak-xxxx2222
    └── CustomerC-Key: ak-xxxx3333
```

### How Usage Plan Connects to Stage

```
Usage Plan
      │
      └── Associated API Stages (you add this manually)
          ├── API:    my-api     ← select from dropdown
          └── Stage:  prod       ← select from dropdown
```

### When Does Usage Plan Apply?

The plan ONLY enforces limits when:
1. The API method has `apiKeyRequired: true`
2. The request includes an `x-api-key` header
3. That key belongs to a Usage Plan associated with the request's stage

| `apiKeyRequired` | `x-api-key` sent? | Behavior |
|---|---|---|
| `true` | Yes (valid key) | Usage Plan enforced (throttle + quota checked) |
| `true` | No or invalid | **403 Forbidden** |
| `false` (default) | Any | Request passes — Usage Plan ignored |

---

## 5. How They Connect — The Stage is the Glue

### Connection Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                        API STAGE ("prod")                           │
│                     ┌─────────────────────┐                         │
│                     │   my-api / prod      │                        │
│                     │                     │                         │
│                     │   Invoke URL:       │                         │
│                     │   https://abc123..  │                         │
│                     │   .../prod          │                         │
│                     └──────────┬──────────┘                         │
│                                │                                    │
│              ┌─────────────────┼─────────────────┐                  │
│              │                 │                  │                  │
│              ▼                 ▼                  ▼                  │
│   ┌──────────────────┐  ┌───────────┐  ┌──────────────────┐        │
│   │  Custom Domain    │  │  Lambda   │  │   Usage Plan      │       │
│   │  api.example.com  │  │  or any   │  │   "Premium Plan"  │       │
│   │                   │  │  backend  │  │                   │       │
│   │  Points TO stage  │  │           │  │  Enforces ON      │       │
│   │  (via API Mapping)│  │           │  │  stage (via       │       │
│   │                   │  │           │  │  Associated Stage)│       │
│   └──────────────────┘  └───────────┘  └──────────────────┘        │
│                                                                     │
│     DNS layer                Backend        Rate limiting layer      │
│     (no awareness of         integration    (no awareness of         │
│      Usage Plan)                             Custom Domain)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Insight

- **Custom Domain** knows about the Stage (via API Mapping)
- **Usage Plan** knows about the Stage (via Associated API Stages)
- **Custom Domain does NOT know about Usage Plan** — and vice versa
- They are independently attached to the same Stage
- The Stage is where enforcement happens internally

---

## 6. Complete Request Flow

### End-to-End: Client Hits Custom Domain → Usage Plan Enforced

```
CLIENT
│
│  GET https://api.example.com/v1/users
│  Headers:
│    x-api-key: ak-xxxx1111
│
▼
┌──────────────────────────────────────────┐
│  STEP 1: DNS Resolution (Route 53)       │
│                                          │
│  api.example.com                         │
│    → CNAME/Alias                         │
│    → d-abc123.execute-api.us-east-1...   │
│                                          │
│  (Route 53 resolves to API Gateway       │
│   domain name)                           │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│  STEP 2: Custom Domain (API Gateway)     │
│                                          │
│  api.example.com                         │
│    → API Mapping: /v1 → my-api / prod    │
│                                          │
│  (Custom Domain routes request to the    │
│   correct API + Stage based on path)     │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│  STEP 3: API Stage receives request      │
│                                          │
│  my-api / prod                           │
│                                          │
│  API Gateway internally checks:          │
│                                          │
│  a) Does this method require API key?    │
│     → apiKeyRequired: true ✅            │
│                                          │
│  b) Is x-api-key present?               │
│     → ak-xxxx1111 ✅                    │
│                                          │
│  c) Is there a Usage Plan for this       │
│     stage with this key?                 │
│     → "Premium Plan" has my-api/prod     │
│       and key ak-xxxx1111 ✅             │
│                                          │
│  d) Is the caller within limits?         │
│     → Rate: 500/1000 req/s ✅           │
│     → Quota: 45,000/100,000 this month ✅│
│                                          │
│  ALL CHECKS PASS → forward request       │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│  STEP 4: Backend Integration             │
│                                          │
│  Lambda / HTTP endpoint / Mock           │
│  processes the request                   │
│                                          │
│  Response: 200 OK { users: [...] }       │
└──────────────────────┬───────────────────┘
                       │
                       ▼
                    CLIENT
              receives response
```

### What Happens When Checks Fail

```
FAILURE SCENARIOS:
│
├── DNS fails              → Client gets DNS resolution error
│
├── No API Mapping match   → 403 Forbidden (API Gateway)
│
├── apiKeyRequired: true
│   └── No x-api-key       → 403 Forbidden: "x-api-key header is missing"
│
├── API key not in any     → 403 Forbidden: "API key is not authorized"
│   Usage Plan for stage
│
├── Rate limit exceeded    → 429 Too Many Requests: "Rate exceeded"
│
└── Quota exceeded         → 429 Too Many Requests: "Quota exceeded"
```

---

## 7. Step-by-Step Setup in AWS Console

### Step 1: Create and Deploy API (Creates Stage)

```
API Gateway Console
│
├── Create API → REST API → Build
│   ├── API name: my-api
│   └── Create API
│
├── Create Resources & Methods
│   ├── /users (GET, POST)
│   └── /users/{id} (GET, PUT, DELETE)
│
├── Set apiKeyRequired: true on methods
│   └── Method Request → API Key Required → true
│
└── Deploy API (button top-right)
    ├── Deployment stage: [New Stage]
    ├── Stage name: prod
    └── Deploy
    
    ✅ Stage "prod" is now created
    ✅ Invoke URL: https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

### Step 2: Create Custom Domain

```
API Gateway Console → Custom Domain Names
│
├── Create domain name
│   ├── Domain name: api.example.com
│   ├── ACM Certificate: select your certificate
│   │   (must be in us-east-1 for edge-optimized)
│   ├── Endpoint configuration: Regional
│   └── Create domain name
│
│   ✅ API Gateway domain name generated:
│      d-abc123.execute-api.us-east-1.amazonaws.com
│
├── API Mappings tab → Configure API mappings
│   ├── API: my-api
│   ├── Stage: prod              ← ATTACHING STAGE TO DOMAIN
│   ├── Path: /v1
│   └── Save
│
│   ✅ api.example.com/v1 → my-api / prod
│
└── Go to Route 53 → Create Record
    ├── Record name: api.example.com
    ├── Record type: A - IPv4
    ├── Alias: Yes
    ├── Route traffic to: API Gateway custom domain
    │   → d-abc123.execute-api.us-east-1.amazonaws.com
    └── Create records
    
    ✅ DNS configured
```

### Step 3: Create Usage Plan

```
API Gateway Console → Usage Plans
│
├── Create Usage Plan
│   ├── Name: Premium Plan
│   ├── Throttling:
│   │   ├── Rate: 1000 requests per second
│   │   └── Burst: 500
│   ├── Quota:
│   │   ├── 100,000 requests
│   │   └── per Month
│   └── Create
│
├── Associated API Stages tab
│   └── Add API Stage
│       ├── API: my-api
│       ├── Stage: prod          ← ATTACHING STAGE TO USAGE PLAN
│       └── Save (checkmark)
│
│   ✅ Usage Plan now enforces on my-api / prod
│
└── API Keys tab
    └── Add API Key to Usage Plan
        ├── Create new key OR select existing
        ├── Name: CustomerA-Key
        └── Add
    
    ✅ API Key linked to Usage Plan
```

### Setup Timeline Summary

```
1. Define API routes & methods
         │
2. Click "Deploy API" → Stage "prod" created
         │
         ├──3a. Custom Domain Names → Create domain
         │       → Add API Mapping → select my-api / prod
         │       → Route 53 → Create alias record
         │
         └──3b. Usage Plans → Create plan (throttle + quota)
                 → Add Associated Stage → select my-api / prod
                 → Add API Keys
```

---

## 8. CloudFormation / SAM Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: API Gateway with Custom Domain + Usage Plan (complete setup)

Parameters:
  DomainName:
    Type: String
    Default: api.example.com
  CertificateArn:
    Type: String
    Description: ACM Certificate ARN for the custom domain
  HostedZoneId:
    Type: String
    Description: Route 53 Hosted Zone ID

Resources:

  # ──────────────────────────────────────────
  # 1. API Definition
  # ──────────────────────────────────────────
  MyApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: my-api
      Description: Example API with Usage Plan and Custom Domain

  UsersResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref MyApi
      ParentId: !GetAtt MyApi.RootResourceId
      PathPart: users

  UsersGetMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref MyApi
      ResourceId: !Ref UsersResource
      HttpMethod: GET
      AuthorizationType: NONE
      ApiKeyRequired: true            # Requires API key for Usage Plan enforcement
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MyLambda.Arn}/invocations

  # ──────────────────────────────────────────
  # 2. Deployment + Stage (Stage is created here)
  # ──────────────────────────────────────────
  ApiDeployment:
    Type: AWS::ApiGateway::Deployment
    DependsOn: UsersGetMethod
    Properties:
      RestApiId: !Ref MyApi

  ProdStage:
    Type: AWS::ApiGateway::Stage
    Properties:
      RestApiId: !Ref MyApi
      DeploymentId: !Ref ApiDeployment
      StageName: prod
      Description: Production stage
      Variables:
        tableName: users-prod
        lambdaAlias: live
      MethodSettings:
        - HttpMethod: '*'
          ResourcePath: '/*'
          ThrottlingBurstLimit: 500
          ThrottlingRateLimit: 1000
          LoggingLevel: ERROR

  # ──────────────────────────────────────────
  # 3. Custom Domain (maps to Stage)
  # ──────────────────────────────────────────
  CustomDomain:
    Type: AWS::ApiGateway::DomainName
    Properties:
      DomainName: !Ref DomainName
      RegionalCertificateArn: !Ref CertificateArn
      EndpointConfiguration:
        Types:
          - REGIONAL

  # API Mapping — links Custom Domain to Stage
  ApiMapping:
    Type: AWS::ApiGateway::BasePathMapping
    DependsOn: ProdStage
    Properties:
      DomainName: !Ref CustomDomain
      RestApiId: !Ref MyApi
      Stage: prod                      # ← Stage attached to Custom Domain
      BasePath: v1

  # Route 53 DNS Record
  DnsRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostedZoneId
      Name: !Ref DomainName
      Type: A
      AliasTarget:
        DNSName: !GetAtt CustomDomain.RegionalDomainName
        HostedZoneId: !GetAtt CustomDomain.RegionalHostedZoneId

  # ──────────────────────────────────────────
  # 4. Usage Plan (attaches to Stage)
  # ──────────────────────────────────────────
  PremiumUsagePlan:
    Type: AWS::ApiGateway::UsagePlan
    DependsOn: ProdStage
    Properties:
      UsagePlanName: Premium Plan
      Description: For paid customers
      Throttle:
        BurstLimit: 500
        RateLimit: 1000
      Quota:
        Limit: 100000
        Period: MONTH
      ApiStages:
        - ApiId: !Ref MyApi
          Stage: prod                  # ← Stage attached to Usage Plan

  # API Key
  CustomerAKey:
    Type: AWS::ApiGateway::ApiKey
    DependsOn: ProdStage
    Properties:
      Name: CustomerA-Key
      Enabled: true
      StageKeys:
        - RestApiId: !Ref MyApi
          StageName: prod

  # Link API Key to Usage Plan
  UsagePlanKey:
    Type: AWS::ApiGateway::UsagePlanKey
    Properties:
      KeyId: !Ref CustomerAKey
      KeyType: API_KEY
      UsagePlanId: !Ref PremiumUsagePlan

  # ──────────────────────────────────────────
  # 5. Lambda Backend (example)
  # ──────────────────────────────────────────
  MyLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: my-api-handler
      Runtime: python3.12
      Handler: index.handler
      Code:
        ZipFile: |
          def handler(event, context):
              return {
                  'statusCode': 200,
                  'body': '{"message": "Hello from Lambda"}'
              }
      Role: !GetAtt LambdaRole.Arn

  LambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref MyLambda
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${MyApi}/*

  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

Outputs:
  DefaultInvokeUrl:
    Value: !Sub https://${MyApi}.execute-api.${AWS::Region}.amazonaws.com/prod
    Description: Default API Gateway URL (before custom domain)

  CustomDomainUrl:
    Value: !Sub https://${DomainName}/v1
    Description: Custom domain URL

  ApiGatewayDomainName:
    Value: !GetAtt CustomDomain.RegionalDomainName
    Description: API Gateway domain name (for DNS CNAME/Alias)

  ApiKeyId:
    Value: !Ref CustomerAKey
    Description: API Key ID (use GET /apikeys/{id} to retrieve the value)
```

---

## 9. Key Takeaways

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│    CLIENT  ──request──►  ROUTE 53  ──DNS──►  CUSTOM DOMAIN              │
│                                                    │                    │
│                                              API Mapping                │
│                                                    │                    │
│                                                    ▼                    │
│                                             ┌─────────────┐            │
│                              ┌──────────────│  API STAGE   │──────────┐ │
│                              │              │   (prod)     │          │ │
│                              │              └──────┬──────┘          │ │
│                              │                     │                 │ │
│                              ▼                     ▼                 ▼ │
│                        ┌───────────┐        ┌───────────┐    ┌──────┐ │
│                        │  USAGE    │        │  LAMBDA / │    │ STAGE│ │
│                        │  PLAN     │        │  BACKEND  │    │ VARS │ │
│                        │           │        └───────────┘    └──────┘ │
│                        │ Throttle  │                                   │
│                        │ Quota     │                                   │
│                        │ API Keys  │                                   │
│                        └───────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Rules to Remember

| Rule | Detail |
|------|--------|
| Stage is created during deployment | You cannot create a stage without deploying your API |
| Custom Domain links to Stage via API Mapping | Manual step after stage exists |
| Usage Plan links to Stage via Associated API Stages | Manual step after stage exists |
| Custom Domain and Usage Plan don't know about each other | They independently reference the same stage |
| Usage Plan only works when `apiKeyRequired: true` | Otherwise requests bypass the plan entirely |
| Re-deploy to update a stage | API changes don't go live until you deploy to the stage |
| Multiple stages = multiple environments | Same API, different configs (dev, qa, prod) |
| Multiple API Mappings on one domain | `/v1` → API-A/prod, `/v2` → API-B/prod |
| Multiple stages in one Usage Plan | One plan can cover `my-api/prod` + `other-api/prod` |

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| Created API but can't see stage | You forgot to deploy — click "Deploy API" |
| Custom domain returns 403 | API Mapping missing or wrong stage selected |
| Usage Plan not enforcing | `apiKeyRequired` is `false` on the method |
| Changed API but nothing happened | Re-deploy to the stage — changes aren't live |
| DNS not working | Check Route 53 alias points to API Gateway domain name (not invoke URL) |
