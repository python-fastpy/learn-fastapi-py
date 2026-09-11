"""
Lambda entrypoint — the ONLY file the serverless deploy path adds.

WHY THIS FILE EXISTS
────────────────────
FastAPI speaks ASGI. Lambda speaks "here is a JSON event dict, give me
back a JSON response dict". They don't understand each other:

    API Gateway  ──▶  Lambda invokes:  handler(event, context)
                                              │
                                        (event is a dict describing the
                                         HTTP request — path, method,
                                         headers, body, query string)
                                              │
                                              ▼
                                       Mangum translates it
                                              │
                                              ▼
                                   FastAPI's normal ASGI interface
                                              │
                                    your @app.get / @app.post run
                                              │
                                       Mangum translates back
                                              ▼
                              {"statusCode": 200, "body": "...", ...}

Mangum is that adapter. Without it you would have to parse the event
dict by hand in every function.

Note main.py is completely unchanged — the same app object serves
uvicorn locally, a Docker container on Fargate, AND Lambda.

Deployed config: infra-lambda.yaml sets this file+function as the
handler (`lambda_handler.handler`) and sets STORAGE=dynamodb, so the
same code path picks the DynamoDB repository automatically.

See docs/04-deploy-lambda.md for the full walkthrough.
"""

from mangum import Mangum

from main import app

# lifespan="off" is important and easy to get wrong.
#
# FastAPI's lifespan (startup/shutdown) assumes a long-running server.
# Lambda's execution model is different: the container is frozen between
# invocations and destroyed unpredictably, so "shutdown" may never run.
# Mangum's default ("auto") tries to run lifespan events per invocation,
# which adds latency to every single request.
#
# With lifespan="off", main.py's lifespan does not run — which means
# app.state.repository is never set by startup. That is handled:
# repository.py's get_repository() builds the repository on the first
# request and CACHES it on app.state, so the boto3 client is created
# once per warm container rather than once per invocation. Combined with
# Lambda reusing warm containers, the cost is paid on cold start only.
handler = Mangum(app, lifespan="off")
