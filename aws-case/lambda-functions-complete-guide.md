# AWS Lambda — Simple Guide

------

## 1. What is Lambda?

You upload a function, AWS runs it when triggered. No servers. Pay only when it runs.

```
  Trigger (API/S3/SQS/Cron)  →  Lambda runs your code  →  Returns response
```

------

## 2. Core Concepts

| Concept | What It Is |
|---------|-----------|
| **Handler** | Function AWS calls: `lambda_function.lambda_handler` |
| **Event** | Input data (JSON) — shape depends on trigger |
| **Context** | Runtime metadata: request ID, timeout, memory |
| **Execution Role** | IAM role — what AWS services Lambda can access |
| **Cold Start** | First run is slower (~200ms Python) — container initializes |
| **Warm Start** | Reuses container — much faster |

**Limits:** Max 15 min timeout, 10 GB memory, 250 MB code (unzipped)

### Why Does Lambda Need an IAM Role?

Lambda is just code — it has no permissions by default. The IAM **Execution Role** tells AWS what your Lambda is allowed to do.

```
  Without IAM Role:
    Lambda tries to write to DynamoDB  →  ACCESS DENIED
    Lambda tries to read from S3       →  ACCESS DENIED
    Lambda tries to write logs         →  ACCESS DENIED (no logs at all!)

  With IAM Role:
    Lambda assumes the role  →  role says "you can write to DynamoDB, read S3, write logs"  →  WORKS
```

Think of it like a badge at an office:
- **Lambda** = the person (your code)
- **IAM Role** = the badge (what doors you can open)
- **No badge** = you can't do anything, not even log in

Every Lambda needs at minimum `AWSLambdaBasicExecutionRole` — which only grants CloudWatch Logs access (`print()` won't work without it). If your Lambda talks to DynamoDB, S3, SQS etc., you add those permissions to the role.

```
  AWSLambdaBasicExecutionRole (minimum — always needed):
    ✓ logs:CreateLogGroup
    ✓ logs:CreateLogStream
    ✓ logs:PutLogEvents

  Add more as needed:
    + dynamodb:GetItem, PutItem, Scan     → if Lambda reads/writes DynamoDB
    + s3:GetObject, PutObject              → if Lambda reads/writes S3
    + sqs:SendMessage, ReceiveMessage      → if Lambda uses SQS
```

------

## 3. Diagram

```
  Client (browser / curl / app)
    |  HTTPS
    v
  API Gateway  --->  Lambda Function  --->  DynamoDB / S3 / etc.
  (gives Lambda      handler(event)
   a public URL)  <---  returns {statusCode, body}
    |
    v
  JSON response

  Lambda has NO public URL by itself.
  API Gateway (or ALB) sits in front to receive HTTP and invoke Lambda.
  Without it, Lambda can only be called via CLI, SDK, or other AWS services.

  Cold Start:  [Download code] → [Start runtime] → [Init] → [Run handler]
  Warm Start:  [Run handler]  (container reused, ~5-15 min idle before destroyed)
```

------

## 4. Minimal Function (Python)

```python
# lambda_function.py
import json

def lambda_handler(event, context):
    name = event.get("name", "World")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Hello, {name}!"})
    }
```

**Event shapes by trigger:**

```python
# API Gateway:  event["httpMethod"], event["path"], event["body"], event["queryStringParameters"]
# S3:           event["Records"][0]["s3"]["bucket"]["name"], event["Records"][0]["s3"]["object"]["key"]
# SQS:          event["Records"][0]["body"]
# Cron:         event["source"] == "aws.events"
```

------

## 5. Create via Console (UI)

```
1. Lambda → Create function → "Author from scratch"
2. Name: my-hello-function, Runtime: Python 3.12
3. Click "Create function"
4. Paste your code in the editor → Click "Deploy"
5. Click "Test" → Create event: {"name": "Tester"} → Click "Test"
6. Configuration tab → set Memory (256 MB), Timeout (30s), Environment variables
```

------

## 6. Create via CloudFormation

### Simple Lambda

```yaml
# lambda-simple.yaml
AWSTemplateFormatVersion: '2010-09-09'       # CloudFormation template version (always this value)

Resources:

  # STEP 1: Create an IAM Role (the "badge" Lambda needs to do anything)
  LambdaRole:
    Type: AWS::IAM::Role                      # creates an IAM role in your AWS account
    Properties:
      RoleName: simple-lambda-role            # name you'll see in IAM console
      AssumeRolePolicyDocument:               # WHO can use this role? (trust policy)
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com   # only the Lambda service can assume this role
            Action: sts:AssumeRole            # "assume" = temporarily become this role
      ManagedPolicyArns:                      # WHAT can this role do? (permissions)
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        # ^ AWS-managed policy that grants: logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
        #   Without this, your Lambda can't even write print() to CloudWatch

  # STEP 2: Create the Lambda Function itself
  HelloFunction:
    Type: AWS::Lambda::Function               # creates a Lambda function
    Properties:
      FunctionName: hello-cfn-function        # name you'll see in Lambda console
      Runtime: python3.12                     # which Python version to run your code
      Handler: index.lambda_handler           # "index" = filename (ZipFile creates index.py)
                                              # "lambda_handler" = function name inside that file
                                              # so AWS calls: index.lambda_handler(event, context)
      Role: !GetAtt LambdaRole.Arn            # !GetAtt = get attribute from another resource
                                              # fetches the ARN of LambdaRole created above
                                              # (ARN = unique ID like arn:aws:iam::123456:role/simple-lambda-role)
      Timeout: 30                             # max 30 seconds to run (default is 3s, max is 900s)
      MemorySize: 256                         # 256 MB RAM — more memory = more CPU = faster but costs more
      Code:
        ZipFile: |                            # inline code — CloudFormation wraps this into a zip
          import json                         # the file is named "index.py" (matches Handler: index.xxx)
          def lambda_handler(event, context):
              name = event.get("name", "World")
              return {"statusCode": 200, "body": json.dumps({"message": f"Hello, {name}!"})}

Outputs:                                      # values printed after deploy (also queryable via CLI)
  FunctionArn:
    Value: !GetAtt HelloFunction.Arn          # prints the Lambda ARN so you can use it elsewhere
    # e.g. arn:aws:lambda:eu-west-1:123456789012:function:hello-cfn-function
```

```bash
aws cloudformation deploy --template-file lambda-simple.yaml \
  --stack-name my-lambda-stack --capabilities CAPABILITY_NAMED_IAM
```

### Using S3 Instead of Inline Code

Inline `ZipFile` has a **4096 character limit**. For real projects, you zip your code and upload to S3.

```
  Inline (ZipFile):                     S3:
  Code lives inside the YAML            Code lives in an S3 bucket
  Max 4096 chars                        Max 250 MB (unzipped)
  Good for: tiny functions              Good for: real projects with dependencies
```

**Step 1 — Upload your code to S3:**

```bash
# Create bucket (one-time)
aws s3 mb s3://my-lambda-code-bucket-12345

# Zip your code (include dependencies if any)
zip function.zip lambda_function.py

# Upload to S3
aws s3 cp function.zip s3://my-lambda-code-bucket-12345/function.zip
```

**Step 2 — Point CloudFormation to S3:**

```yaml
  HelloFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: hello-from-s3
      Runtime: python3.12
      Handler: lambda_function.lambda_handler    # now it's "lambda_function" not "index"
                                                  # because your file is lambda_function.py
      Role: !GetAtt LambdaRole.Arn
      Code:
        S3Bucket: my-lambda-code-bucket-12345    # bucket where you uploaded
        S3Key: function.zip                       # path to the zip file in that bucket
        # S3ObjectVersion: abc123                 # optional — pin to specific version
```

```
  ZipFile (inline):                      S3:
  Handler: index.lambda_handler          Handler: lambda_function.lambda_handler
           ↑                                      ↑
    CloudFormation creates                 your zip contains
    "index.py" automatically              "lambda_function.py"
```

**To update code:** upload new zip to S3, then update the stack (or change `S3Key`/`S3ObjectVersion`).

------

## 7. How Does an API Call Lambda?

Lambda can't receive HTTP requests directly. **API Gateway** sits in front and routes HTTP calls to your Lambda.

```
  Browser/curl/App
       |
       |  GET https://abc123.execute-api.eu-west-1.amazonaws.com/v1/hello
       v
  API Gateway          Lambda
  +-----------+       +------------------+
  | receives  | ----> | handler(event,   |
  | HTTP req  |       |   context)       |
  | converts  | <---- | returns          |
  | to event  |       | {statusCode,body}|
  +-----------+       +------------------+
       |
       v
  JSON response back to caller
```

### Console (quickest way)

```
1. Lambda → your function → "Add trigger" → select "API Gateway"
2. Choose: Create new API → HTTP API → Security: Open → Click "Add"
3. You get a URL instantly:
   https://abc123.execute-api.eu-west-1.amazonaws.com/default/my-hello-function
4. curl that URL — your Lambda runs
```

### CloudFormation

```yaml
# lambda-with-api.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
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

  HelloFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: hello-api-function
      Runtime: python3.12
      Handler: index.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      Code:
        ZipFile: |
          import json
          def lambda_handler(event, context):
              return {"statusCode": 200, "body": json.dumps({"message": "Hello from Lambda!"})}

  # HTTP API (simpler & cheaper than REST API)
  HttpApi:
    Type: AWS::ApiGatewayV2::Api                   # creates the API
    Properties:
      Name: hello-api
      ProtocolType: HTTP

  # Connect API → Lambda
  Integration:
    Type: AWS::ApiGatewayV2::Integration           # links API to Lambda
    Properties:
      ApiId: !Ref HttpApi
      IntegrationType: AWS_PROXY                   # pass full request to Lambda
      IntegrationUri: !GetAtt HelloFunction.Arn
      PayloadFormatVersion: '2.0'

  # Route: any request → Lambda
  Route:
    Type: AWS::ApiGatewayV2::Route                 # URL path mapping
    Properties:
      ApiId: !Ref HttpApi
      RouteKey: 'GET /hello'                       # GET /hello → Lambda
      Target: !Sub 'integrations/${Integration}'

  # Deploy the API
  Stage:
    Type: AWS::ApiGatewayV2::Stage                 # makes the API live
    Properties:
      ApiId: !Ref HttpApi
      StageName: '$default'                        # no stage prefix in URL
      AutoDeploy: true

  # Allow API Gateway to call Lambda
  Permission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref HelloFunction
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${HttpApi}/*'

Outputs:
  ApiUrl:
    Value: !Sub 'https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com/hello'
```

```bash
aws cloudformation deploy --template-file lambda-with-api.yaml \
  --stack-name lambda-api-stack --capabilities CAPABILITY_NAMED_IAM
```

> **Without API Gateway**, Lambda can only be invoked by: other AWS services (S3/SQS/EventBridge) or SDK calls. It has no public URL on its own.

------

## 8. Lambda + CloudWatch Logs

Every Lambda automatically sends logs to CloudWatch. Every `print()` or logging call in your code appears there.

```
  Lambda Function
    |  print("hello")
    |  logger.info("processing order 123")
    |  (also: START, END, REPORT lines auto-added)
    v
  CloudWatch Logs
    Log Group:   /aws/lambda/my-hello-function     (one per function)
      Log Stream:  2024/01/15/[$LATEST]abc123       (one per container instance)
        → START RequestId: a1b2c3
        → hello
        → processing order 123
        → END RequestId: a1b2c3
        → REPORT RequestId: a1b2c3  Duration: 45ms  Memory: 128MB  MaxMemory: 36MB
```

### How to Log in Your Lambda

```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")      # structured log
    print("This also goes to CloudWatch")         # simple log
    
    try:
        result = do_something()
        logger.info(f"Success: {result}")
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)   # logs full traceback
        raise
```

### Check Logs — Console (UI)

```
1. Lambda → Functions → my-hello-function → "Monitor" tab → "View CloudWatch logs"
   (or)
   CloudWatch → Log groups → /aws/lambda/my-hello-function

2. Click the latest Log stream

3. You'll see:
   START RequestId: a1b2c3-d4e5 Version: $LATEST
   [INFO] Received event: {"name": "test"}
   [INFO] Success: done
   END RequestId: a1b2c3-d4e5
   REPORT RequestId: a1b2c3-d4e5 Duration: 12.34 ms Billed: 13 ms Memory: 256 MB Max Memory Used: 45 MB
```

### CloudFormation — Lambda with Custom Log Retention

By default logs are kept **forever**. Set a retention period to save costs:

```yaml
# lambda-with-logs.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:

  # IAM Role — lets Lambda write logs to CloudWatch
  # "AssumeRole" = Lambda service is allowed to use this role
  # "AWSLambdaBasicExecutionRole" = AWS managed policy that grants:
  #   logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
  LambdaRole:
    Type: AWS::IAM::Role                          # creates an IAM role
    Properties:
      RoleName: lambda-logs-role
      AssumeRolePolicyDocument:                   # WHO can use this role?
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com       # only Lambda service can assume it
            Action: sts:AssumeRole
      ManagedPolicyArns:                          # WHAT can the role do?
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole  # CloudWatch Logs access

  # Lambda Function — the actual code that runs
  HelloFunction:
    Type: AWS::Lambda::Function                   # creates a Lambda function
    Properties:
      FunctionName: hello-with-logs
      Runtime: python3.12                         # Python version
      Handler: index.lambda_handler               # file "index" (from ZipFile), function "lambda_handler"
      Role: !GetAtt LambdaRole.Arn                # !GetAtt = get the ARN of LambdaRole defined above
      Timeout: 30                                 # max 30 seconds per invocation
      MemorySize: 256                             # 256 MB RAM (also scales CPU proportionally)
      Code:
        ZipFile: |                                # inline code (max 4096 chars, file is named "index.py")
          import json, logging
          logger = logging.getLogger()            # get root logger
          logger.setLevel(logging.INFO)           # show INFO and above (INFO, WARNING, ERROR)
          
          def lambda_handler(event, context):     # entry point — AWS calls this
              logger.info(f"Event: {event}")      # logs the full input → appears in CloudWatch
              name = event.get("name", "World")   # read "name" from event, default "World"
              logger.info(f"Greeting {name}")      # another log line
              return {"statusCode": 200, "body": json.dumps({"message": f"Hello, {name}!"})}

  # Log Group — controls WHERE logs go and HOW LONG they're kept
  # Without this, AWS auto-creates the log group with NO expiry (logs kept forever = costs pile up)
  LambdaLogGroup:
    Type: AWS::Logs::LogGroup                     # creates a CloudWatch Log Group
    Properties:
      LogGroupName: !Sub '/aws/lambda/${HelloFunction}'  # !Sub = string substitution, resolves to /aws/lambda/hello-with-logs
      RetentionInDays: 14                         # delete logs after 14 days (saves cost)
      # Options: 1,3,5,7,14,30,60,90,120,150,180,365,400,545,731,1096,1827,2192,2557,2922,3288,3653

Outputs:
  FunctionName:
    Value: !Ref HelloFunction                     # !Ref = returns the resource name (hello-with-logs)
  LogGroup:
    Value: !Ref LambdaLogGroup                    # returns the log group name
```

```bash
aws cloudformation deploy --template-file lambda-with-logs.yaml \
  --stack-name lambda-logs-stack --capabilities CAPABILITY_NAMED_IAM
```

### Key Things to Know

| What | Detail |
|------|--------|
| Log group name | Always `/aws/lambda/{function-name}` — created automatically on first invoke |
| Permission needed | `AWSLambdaBasicExecutionRole` includes CloudWatch Logs write access |
| Default retention | **Forever** (costs add up!) — set `RetentionInDays` in CloudFormation |
| `print()` | Works, goes to CloudWatch — but `logging` module gives you levels (INFO/ERROR/WARNING) |
| REPORT line | Auto-added after every invocation — shows duration, billed time, memory used |
| Log delay | Logs appear in CloudWatch within a few seconds of invocation |

------

## 9. Testing

### A) Console — click "Test" tab, paste event JSON, click "Test"

### B) curl (via API Gateway)

```bash
curl https://abc123.execute-api.eu-west-1.amazonaws.com/v1/users
```

### C) Local Testing with SAM CLI (yes, you can test locally!)

```bash
# Install: brew install aws-sam-cli  (or pip install aws-sam-cli)

# Create template.yaml
cat > template.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Resources:
  HelloFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: lambda_function.lambda_handler
      Runtime: python3.12
      Events:
        Api:
          Type: Api
          Properties:
            Path: /hello
            Method: get
EOF

# Run locally (needs Docker)
sam build
sam local start-api          # starts local API on http://localhost:3000
curl http://localhost:3000/hello

# Or invoke once:
sam local invoke HelloFunction --event '{"name": "local"}'
```

### D) Local Testing with Docker (no SAM needed)

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
CMD ["lambda_function.lambda_handler"]
```

```bash
docker build -t my-lambda .
docker run -p 9000:8080 my-lambda

# In another terminal:
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"name": "Docker"}'
```

### E) Unit Testing with pytest + moto

```bash
pip install pytest moto boto3
```

```python
# test_handler.py
import json, boto3, pytest
from moto import mock_aws

@mock_aws
def test_get_users():
    # Create mock table
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    dynamodb.create_table(
        TableName="test-users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    
    import os
    os.environ["TABLE_NAME"] = "test-users"
    from lambda_function import lambda_handler
    
    result = lambda_handler({"httpMethod": "GET"}, None)
    assert result["statusCode"] == 200
```

```bash
pytest test_handler.py -v
```

------

## 10. Event Sources (Triggers)

| Trigger | How It Works | Use Case |
|---------|-------------|----------|
| **API Gateway** | HTTP request → Lambda → response | REST APIs |
| **S3** | File uploaded → Lambda runs | Image processing |
| **SQS** | Message in queue → Lambda processes | Background jobs |
| **EventBridge** | Cron schedule → Lambda runs | Scheduled tasks |
| **DynamoDB Streams** | DB change → Lambda reacts | Change data capture |

```
  Sync (wait):     API Gateway, ALB
  Async (fire):    S3, SNS, EventBridge
  Poll (batch):    SQS, Kinesis, DynamoDB Streams
```

------

## 11. Pricing

```
  Free Tier (always free, not 12-month):
    1M requests/month + 400,000 GB-seconds

  After free tier:
    $0.20 per 1M requests
    + duration cost based on memory (256 MB, 200ms avg = very cheap)

  Example: 3M requests/month, 256 MB, 200ms avg = ~$0.40/month
```

------

## 12. Common Errors

| Error | Fix |
|-------|-----|
| `Task timed out` | Increase timeout or optimize code |
| `ImportModuleError` | Missing dependency — add to zip/layer |
| `AccessDeniedException` | Add IAM permissions to execution role |
| `Unable to import module` | Wrong handler: should be `filename.function_name` |

------

## Cheat Sheet

```bash
# Deploy (CloudFormation)
aws cloudformation deploy --template-file t.yaml --stack-name S --capabilities CAPABILITY_NAMED_IAM

# Local (SAM)
sam build && sam local start-api
```
