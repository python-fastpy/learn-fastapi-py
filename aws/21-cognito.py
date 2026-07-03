# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Cognito (Step 18)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 20-rds.py  |  next: 22-ssm-parameter-store.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 18: COGNITO — AUTH & USER MANAGEMENT       ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: User authentication and authorization. Managed sign-up,
#       sign-in, MFA, social login. Issues JWT tokens that your
#       API validates on every request.
#
# REAL REPO: The reuters-ai_assistant backend uses Thomson Reuters
#            Sphinx Auth for JWT validation (enterprise SSO).
#            Cognito is the AWS-native alternative. API Gateway
#            authorizers can use Cognito directly — zero custom
#            auth code needed.
#
# ── User Pool vs Identity Pool ──────────────────────────────
#
#   Cognito has TWO separate services. Most people only need
#   User Pools. They solve different problems:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │                                                          │
#   │  USER POOL                    IDENTITY POOL              │
#   │  (user directory)             (AWS credential broker)    │
#   │                                                          │
#   │  ┌──────────────────┐        ┌──────────────────┐       │
#   │  │ Sign-up / Sign-in│        │ Exchange tokens   │       │
#   │  │ Password policy  │        │ for temporary     │       │
#   │  │ MFA             │        │ AWS credentials   │       │
#   │  │ Email verify    │        │ (IAM roles)       │       │
#   │  │ Social login    │        │                    │       │
#   │  │ SAML / OIDC     │        │ "I have a Google  │       │
#   │  │                  │        │  token, give me   │       │
#   │  │ Issues JWTs:     │        │  S3 access"       │       │
#   │  │  - ID token      │        │                    │       │
#   │  │  - Access token  │        │ Sources:           │       │
#   │  │  - Refresh token │        │  - Cognito User    │       │
#   │  └──────────────────┘        │    Pool tokens     │       │
#   │                               │  - Google/Facebook │       │
#   │  USE FOR:                     │  - SAML providers  │       │
#   │  API authentication,         │  - Apple ID        │       │
#   │  user management,            └──────────────────┘       │
#   │  most web/mobile apps                                    │
#   │                               USE FOR:                   │
#   │                               Direct AWS resource        │
#   │                               access from client         │
#   │                               (S3 uploads from mobile,   │
#   │                                IoT devices)              │
#   └──────────────────────────────────────────────────────────┘
#
#   For the book-store API: User Pool only. Your API validates
#   JWTs from the User Pool. No Identity Pool needed.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console -> search "Cognito" -> click it
#
#   2. Click "Create user pool"
#      ┌──────────────────────────────────────────────────┐
#      │  Step 1: Sign-in experience                       │
#      │                                                    │
#      │  Sign-in options:                                 │
#      │    [x] Email  (recommended — most flexible)       │
#      │    [ ] Phone                                      │
#      │    [ ] Username                                   │
#      │                                                    │
#      │  (Cannot change sign-in options after creation!)  │
#      └──────────────────────────────────────────────────┘
#      -> Next
#
#      ┌──────────────────────────────────────────────────┐
#      │  Step 2: Security requirements                    │
#      │                                                    │
#      │  Password policy:                                 │
#      │    Minimum length: 8                              │
#      │    Require uppercase: Yes                         │
#      │    Require number: Yes                            │
#      │    Require symbol: Yes                            │
#      │                                                    │
#      │  MFA:                                             │
#      │    Optional MFA (let users choose)                │
#      │    Methods: Authenticator app, SMS                │
#      │                                                    │
#      │  Account recovery:                                │
#      │    Email only (most common)                       │
#      └──────────────────────────────────────────────────┘
#      -> Next
#
#      ┌──────────────────────────────────────────────────┐
#      │  Step 3: Sign-up experience                       │
#      │                                                    │
#      │  Self-registration: Enabled                       │
#      │  Verification: Send email with code               │
#      │                                                    │
#      │  Required attributes:                             │
#      │    email (auto-selected from sign-in)             │
#      │                                                    │
#      │  Custom attributes (optional):                    │
#      │    custom:organization                            │
#      │    custom:role                                    │
#      │    (prefixed with "custom:" automatically)        │
#      └──────────────────────────────────────────────────┘
#      -> Next
#
#      ┌──────────────────────────────────────────────────┐
#      │  Step 4: Message delivery                         │
#      │                                                    │
#      │  Email: Send with Cognito (free, 50/day limit)   │
#      │    or: Amazon SES (production — no limit)        │
#      └──────────────────────────────────────────────────┘
#      -> Next
#
#      ┌──────────────────────────────────────────────────┐
#      │  Step 5: App integration                          │
#      │                                                    │
#      │  User pool name: book-store-users                 │
#      │                                                    │
#      │  Hosted UI: Use Cognito Hosted UI                 │
#      │    Domain: book-store-auth  (.auth.<region>.      │
#      │     amazoncognito.com)                            │
#      │                                                    │
#      │  App client:                                      │
#      │    Name: book-store-web-client                    │
#      │    Client secret: No (for public web/mobile apps) │
#      │    Auth flows:                                    │
#      │      [x] ALLOW_USER_SRP_AUTH (secure sign-in)     │
#      │      [x] ALLOW_REFRESH_TOKEN_AUTH                 │
#      │                                                    │
#      │  Callback URL: http://localhost:3000/callback      │
#      │  Sign-out URL:  http://localhost:3000/             │
#      │                                                    │
#      │  OAuth flows:                                     │
#      │    [x] Authorization code grant                   │
#      │  Scopes:                                          │
#      │    [x] openid  [x] email  [x] profile            │
#      └──────────────────────────────────────────────────┘
#      -> Next -> Create user pool
#
# ── JWT Tokens ──────────────────────────────────────────────
#
#   Cognito issues three tokens after successful sign-in:
#
#   ┌──────────────────┬───────────────────────────────────┐
#   │ Token            │ Purpose                           │
#   ├──────────────────┼───────────────────────────────────┤
#   │ ID Token         │ User attributes (email, name,     │
#   │ (1 hour)         │ custom attributes). Use for       │
#   │                  │ displaying user info in the UI.   │
#   ├──────────────────┼───────────────────────────────────┤
#   │ Access Token     │ Authorization scopes. Use for     │
#   │ (1 hour)         │ API authorization. Send in        │
#   │                  │ Authorization: Bearer <token>     │
#   ├──────────────────┼───────────────────────────────────┤
#   │ Refresh Token    │ Get new ID/Access tokens without  │
#   │ (30 days default)│ re-authenticating. Stored on the  │
#   │                  │ client (httpOnly cookie ideally).  │
#   └──────────────────┴───────────────────────────────────┘
#
#   Token expiration is configurable per app client:
#     ID/Access token:  5 min to 24 hours (default: 1 hour)
#     Refresh token:    1 hour to 10 years (default: 30 days)
#
# ── API Gateway Integration ─────────────────────────────────
#
#   API Gateway can validate Cognito JWTs with zero custom code.
#
#   Setup:
#     API Gateway -> Authorizers -> Create authorizer
#     ┌──────────────────────────────────────────────────┐
#     │  Name: book-store-cognito-auth                    │
#     │  Type: Cognito                                    │
#     │  User Pool: book-store-users                      │
#     │  Token source: Authorization header               │
#     └──────────────────────────────────────────────────┘
#
#   Then attach to routes:
#     GET  /books  -> Authorizer: book-store-cognito-auth
#     POST /books  -> Authorizer: book-store-cognito-auth
#
#   API Gateway validates the JWT signature, expiration,
#   and issuer automatically. Invalid tokens get 401.
#
# ── OAuth 2.0 Flows ─────────────────────────────────────────
#
#   Cognito app clients support three OAuth flows:
#
#   Authorization Code (recommended for web apps):
#     User -> Hosted UI -> Cognito -> redirect with code
#     Backend -> exchange code for tokens (server-side)
#     Most secure. Code is short-lived, tokens stay server-side.
#
#   Implicit (legacy, avoid):
#     Tokens returned directly in URL fragment.
#     Less secure — tokens exposed in browser history.
#
#   Client Credentials (machine-to-machine):
#     Service -> Cognito with client_id + client_secret
#     Returns access token only (no user context).
#     For backend-to-backend API calls.
#
# ── Groups and Roles ────────────────────────────────────────
#
#   Create groups in the User Pool to manage permissions:
#
#     Group: editors    -> users who can create/edit books
#     Group: admins     -> users who can delete books
#     Group: readers    -> users who can only read
#
#   Groups appear in the JWT token's "cognito:groups" claim.
#   Your API checks group membership for authorization:
#
#     # In FastAPI
#     if "admins" not in token["cognito:groups"]:
#         raise HTTPException(403, "Admin access required")
#
#   Groups can optionally be mapped to IAM roles
#   (for Identity Pool use cases).
#
# ── Lambda Triggers ─────────────────────────────────────────
#
#   Hook custom logic into the auth flow with Lambda functions:
#
#   ┌──────────────────────────┬──────────────────────────────┐
#   │ Trigger                  │ Use Case                     │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Pre sign-up              │ Validate email domain,       │
#   │                          │ block disposable emails      │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Post confirmation        │ Send welcome email, create   │
#   │                          │ user record in your DB       │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Pre authentication       │ Block users by IP or region  │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Post authentication      │ Log sign-in events           │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Pre token generation     │ Add custom claims to JWT,    │
#   │                          │ modify group memberships     │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ Custom message           │ Customize verification email │
#   │                          │ or SMS message text          │
#   ├──────────────────────────┼──────────────────────────────┤
#   │ User migration           │ Migrate users from old auth  │
#   │                          │ system on first sign-in      │
#   └──────────────────────────┴──────────────────────────────┘
#
# ── Cognito vs Sphinx Auth vs Auth0 ─────────────────────────
#
#   ┌────────────────┬──────────────┬──────────────┬──────────┐
#   │                │ Cognito      │ Sphinx Auth  │ Auth0    │
#   ├────────────────┼──────────────┼──────────────┼──────────┤
#   │ Provider       │ AWS          │ Thomson      │ Okta     │
#   │                │              │ Reuters      │          │
#   │ AWS integration│ Native       │ Custom JWT   │ OIDC     │
#   │ Enterprise SSO │ SAML/OIDC    │ Built-in SSO │ SAML     │
#   │ User mgmt UI   │ Hosted UI    │ Internal     │ Universal│
#   │ Cost           │ Free 50K MAU │ Enterprise   │ Free 7K  │
#   │ Best for       │ AWS-native   │ TR products  │ Multi-   │
#   │                │ apps         │ only         │ cloud    │
#   └────────────────┴──────────────┴──────────────┴──────────┘
#
#   The real backend uses Sphinx Auth because it is a Thomson
#   Reuters product — Sphinx provides enterprise SSO, user
#   rights (like reuterAIAssistantAllAccessRight), and
#   integrates with TR's identity infrastructure.
#
# ── Practical Example: Protect Book Store API ───────────────
#
#   1. Create User Pool "book-store-users" (steps above)
#   2. Create app client (no client secret for web app)
#   3. In your FastAPI app, validate the JWT:
#
#     from fastapi import Depends, HTTPException
#     from fastapi.security import HTTPBearer
#     import jwt  # python-jose or PyJWT
#
#     security = HTTPBearer()
#     COGNITO_REGION = "eu-west-1"
#     COGNITO_USER_POOL_ID = "eu-west-1_Abc123"
#     COGNITO_APP_CLIENT_ID = "1abc2def3ghi4jkl"
#
#     async def get_current_user(token = Depends(security)):
#         try:
#             payload = jwt.decode(
#                 token.credentials,
#                 algorithms=["RS256"],
#                 # Cognito publishes JWKS at:
#                 # https://cognito-idp.{region}.amazonaws.com/
#                 #   {pool_id}/.well-known/jwks.json
#             )
#             return payload
#         except jwt.InvalidTokenError:
#             raise HTTPException(401, "Invalid token")
#
#     @app.get("/books")
#     async def list_books(user = Depends(get_current_user)):
#         return {"books": [...], "user": user["email"]}
#
# ── Cost ────────────────────────────────────────────────────
#
#   Monthly Active Users (MAUs) pricing:
#
#   ┌───────────────────┬─────────────────────────────────┐
#   │ Tier              │ Price per MAU                    │
#   ├───────────────────┼─────────────────────────────────┤
#   │ First 50,000 MAUs │ FREE                            │
#   │ 50,001-100,000    │ $0.0055/MAU                     │
#   │ 100,001-1,000,000 │ $0.0046/MAU                     │
#   │ 1,000,001-10M     │ $0.00325/MAU                    │
#   └───────────────────┴─────────────────────────────────┘
#
#   A MAU is a user who signs in, signs up, resets password,
#   or has their token refreshed in a calendar month.
#
#   Advanced Security (optional add-on):
#     Compromised credential detection, adaptive auth,
#     advanced risk analysis. $0.050/MAU.
#
#   Example:
#     10,000 MAUs = FREE
#     75,000 MAUs = 50K free + 25K x $0.0055 = $137.50/month
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. Sign-in attributes (email, phone, username) CANNOT be
#      changed after User Pool creation. Plan carefully.
#      If you need to change them, you must create a new pool
#      and migrate users.
#
#   2. Hosted UI customization is limited. You can change the
#      logo and CSS, but the layout is fixed. For full control,
#      build your own sign-in page using the Cognito SDK.
#
#   3. Token expiration is per app client, not per user.
#      All users of the same app client share the same
#      token lifetimes.
#
#   4. User migration requires a Lambda trigger. There is no
#      bulk import that preserves passwords — users must sign
#      in once to migrate (the Lambda fetches from old system).
#
#   5. Custom attributes cannot be required and cannot be
#      changed to required after creation. Plan ahead.
#
#   6. Cognito emails: Free tier sends from no-reply@verificationemail.com
#      (50/day limit). For production, configure SES with your
#      own domain to remove limits and improve deliverability.
#
#   7. User Pool has a hard limit of 40 custom attributes.
#      Use them sparingly — store complex user data in your
#      own database, not in Cognito attributes.
