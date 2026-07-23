# AWS Application Load Balancer (ALB) — Complete Hands-On Guide

## Table of Contents
- [1. What is an ALB?](#1-what-is-an-alb)
- [2. Core Concepts](#2-core-concepts)
- [3. Architecture Diagram](#3-architecture-diagram)
- [4. How Routing Works](#4-how-routing-works)
- [5. Health Checks](#5-health-checks)
- [6. Step-by-Step: Create ALB via Console](#6-step-by-step-create-alb-via-console)
- [7. Step-by-Step: Create ALB via CloudFormation](#7-step-by-step-create-alb-via-cloudformation)
- [8. ALB + Lambda (Serverless Target)](#8-alb--lambda-serverless-target)
- [9. Common Patterns](#9-common-patterns)
- [10. Troubleshooting](#10-troubleshooting)

------

## 1. What is an ALB?

An **Application Load Balancer** distributes incoming HTTP/HTTPS traffic across multiple targets
(EC2 instances, containers, Lambda functions, IPs) so no single server gets overwhelmed.

Think of it like a **restaurant host**:
- **ALB** = the host at the front door
- **Listeners** = the host's rulebook ("lunch guests go left, dinner guests go right")
- **Target Groups** = tables in different sections
- **Targets** = actual servers (chairs at each table)
- **Health Checks** = the host checking if a table is clean and ready before seating anyone

ALB operates at **Layer 7** (HTTP/HTTPS) — it can read the URL path, headers, query strings,
and make smart routing decisions. This is the key difference from a Network Load Balancer (NLB),
which operates at Layer 4 (TCP/UDP) and only sees IP + port.

------

## 2. Core Concepts

| Concept | What It Is | Example |
|---------|-----------|---------|
| **Load Balancer** | Entry point that receives all traffic | `my-app-alb-123456.eu-west-1.elb.amazonaws.com` |
| **Listener** | Listens on a port + protocol, has rules | Port 80 (HTTP), Port 443 (HTTPS) |
| **Listener Rule** | Conditions → route to a target group | Path `/api/*` → API target group |
| **Target Group** | A pool of targets that receive traffic | "api-servers" group with 3 EC2 instances |
| **Target** | Individual destination (EC2, IP, Lambda) | `i-0abc123def` on port 8080 |
| **Health Check** | Periodic ping to verify target is alive | GET `/health` every 30s, expect 200 |
| **Security Group** | Firewall rules for the ALB itself | Allow inbound 80/443 from `0.0.0.0/0` |
| **Availability Zone** | ALB spans multiple AZs for fault tolerance | `eu-west-1a` + `eu-west-1b` |

**ALB vs other AWS load balancers:**

| Type | Layer | Use Case |
|------|-------|----------|
| **ALB** (Application) | Layer 7 (HTTP/HTTPS) | Web apps, APIs, microservices, path/host routing |
| **NLB** (Network) | Layer 4 (TCP/UDP) | Ultra-low latency, static IP, non-HTTP protocols |
| **CLB** (Classic) | Layer 4/7 | Legacy — don't use for new projects |
| **GWLB** (Gateway) | Layer 3 | Firewalls, intrusion detection appliances |

------

## 3. Architecture Diagram

```
  Internet
    |
    v
┌─────────────────────────────────────────────────────────┐
│              Application Load Balancer                  │
│         (my-app-alb.eu-west-1.elb.amazonaws.com)        │
│                                                         │
│  Listener :80 (HTTP)  ──► redirect to :443              │
│  Listener :443 (HTTPS) ──► rules below                  │
│    ├── Path /api/*    ──► Target Group: api-servers      │
│    ├── Path /admin/*  ──► Target Group: admin-servers    │
│    └── Default        ──► Target Group: web-servers      │
└────────────┬──────────────────┬──────────────────┬──────┘
             │                  │                  │
             v                  v                  v
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ AZ-a         │   │ AZ-b         │   │ AZ-a         │
   │ EC2: api-1   │   │ EC2: api-2   │   │ EC2: web-1   │
   │ port 8080    │   │ port 8080    │   │ port 80      │
   └──────────────┘   └──────────────┘   └──────────────┘
   Target Group:       Target Group:      Target Group:
   api-servers         api-servers        web-servers
```

**Traffic flow:**

```
  User browser
    │  HTTPS request: GET https://myapp.com/api/users
    v
  Route 53 (DNS) ──► resolves myapp.com to ALB DNS name
    │
    v
  ALB Listener :443
    │  evaluates rules top-to-bottom
    │  matches: path = /api/*
    v
  Target Group "api-servers"
    │  picks healthy target (round-robin by default)
    v
  EC2 instance api-2 (port 8080)
    │  processes request
    v
  Response travels back: EC2 → ALB → User
```

------

## 4. How Routing Works

ALB evaluates listener rules **top to bottom by priority** (lowest number = first).
First matching rule wins. There is always a **default rule** (priority = last) as a catch-all.

### Rule Conditions (can combine with AND)

| Condition | Example | Matches |
|-----------|---------|---------|
| **Path pattern** | `/api/*` | `/api/users`, `/api/orders/123` |
| **Host header** | `api.myapp.com` | requests to that subdomain |
| **HTTP method** | `GET` | only GET requests |
| **Query string** | `version=2` | `?version=2` in URL |
| **Source IP** | `10.0.0.0/8` | internal network only |
| **HTTP header** | `X-Custom: blue` | A/B testing, canary deployments |

### Rule Actions

| Action | What It Does |
|--------|-------------|
| **Forward** | Send to a target group (or weighted split across multiple) |
| **Redirect** | Return 301/302 (e.g., HTTP → HTTPS) |
| **Fixed response** | Return a static response (e.g., maintenance page) |

### Example: Weighted routing (canary deployment)

```
Rule: path = /api/*
  Action: forward
    90% → target-group-v1
    10% → target-group-v2  (new version, testing)
```

------

## 5. Health Checks

ALB pings each target periodically. Unhealthy targets stop receiving traffic.

| Setting | Default | Recommended |
|---------|---------|-------------|
| **Protocol** | HTTP | HTTP (or HTTPS if app requires) |
| **Path** | `/` | `/health` (dedicated lightweight endpoint) |
| **Port** | traffic port | traffic port |
| **Healthy threshold** | 5 | 2 (faster recovery) |
| **Unhealthy threshold** | 2 | 2 |
| **Timeout** | 5s | 5s |
| **Interval** | 30s | 10s (faster detection) |
| **Success codes** | 200 | 200 (or 200-299) |

```
Health Check Flow:

  ALB ──GET /health──► Target (port 8080)
                        │
                        ├── 200 OK        → count healthy++
                        │                   (reaches threshold → HEALTHY)
                        │
                        └── 500 / timeout → count unhealthy++
                                            (reaches threshold → UNHEALTHY → no traffic)
```

**Tip:** Your `/health` endpoint should check that the app is truly ready (DB connection alive,
dependencies reachable), not just return 200 unconditionally.

------

## 6. Step-by-Step: Create ALB via Console

### Prerequisites
- A VPC with at least 2 public subnets in different AZs
- EC2 instances running a web server (or you'll create them below)

### Step 1: Launch 2 EC2 Instances (simple web servers)

1. **EC2 → Launch Instances**
2. Name: `web-server-1`
3. AMI: Amazon Linux 2023
4. Instance type: `t2.micro` (free tier)
5. Key pair: select or create one
6. Network: your VPC, **public subnet in AZ-a**, Auto-assign public IP = Enable
7. Security Group: create new
   - Inbound: **SSH (22)** from your IP, **HTTP (80)** from anywhere
8. Under **Advanced details → User data**, paste:
   ```bash
   #!/bin/bash
   yum update -y
   yum install -y httpd
   echo "<h1>Hello from $(hostname -f) in AZ-a</h1>" > /var/www/html/index.html
   echo "OK" > /var/www/html/health
   systemctl start httpd
   systemctl enable httpd
   ```
9. Launch.
10. Repeat for `web-server-2` in **AZ-b** (change the echo text to `AZ-b`).

### Step 2: Create a Target Group

1. **EC2 → Target Groups → Create target group**
2. Target type: **Instances**
3. Name: `my-web-targets`
4. Protocol: HTTP, Port: 80
5. VPC: your VPC
6. Health check path: `/health`
7. Click **Next**
8. Select both `web-server-1` and `web-server-2`
9. Click **Include as pending below**
10. Click **Create target group**

### Step 3: Create the ALB

1. **EC2 → Load Balancers → Create Load Balancer**
2. Select **Application Load Balancer**
3. Name: `my-first-alb`
4. Scheme: **Internet-facing**
5. IP address type: IPv4
6. Network mapping:
   - VPC: your VPC
   - Select **at least 2 AZs** with public subnets
7. Security group: create new
   - Inbound: **HTTP (80)** from `0.0.0.0/0`
8. Listener: HTTP : 80 → forward to `my-web-targets`
9. Click **Create load balancer**

### Step 4: Test

1. Wait for ALB state to become **Active** (1-2 minutes)
2. Copy the **DNS name** (e.g., `my-first-alb-123456.eu-west-1.elb.amazonaws.com`)
3. Open in browser — you should see "Hello from ... in AZ-a" or "AZ-b"
4. Refresh multiple times — the response alternates between the two instances

### Step 5: Add HTTPS (Optional but recommended)

1. Request a certificate in **ACM** (AWS Certificate Manager) for your domain
2. Add a new listener: HTTPS : 443, forward to `my-web-targets`, select certificate
3. Edit the HTTP : 80 listener → change action to **Redirect to HTTPS : 443**
4. Update your DNS (Route 53) to point your domain to the ALB

------

## 7. Step-by-Step: Create ALB via CloudFormation

Save this as `alb-with-ec2.yaml` and deploy with:

```bash
aws cloudformation create-stack \
  --stack-name my-alb-stack \
  --template-body file://alb-with-ec2.yaml \
  --capabilities CAPABILITY_IAM \
  --region eu-west-1
```

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: >
  ALB with 2 EC2 instances across 2 AZs.
  Creates: VPC, subnets, internet gateway, ALB, target group, 2 EC2 instances.

  Architecture:
  ┌─────────┐      ┌──────────────┐      ┌──────────────┐
  │  User   │─────▶│     ALB      │─────▶│  EC2 (AZ-a)  │
  │ Browser │ HTTP │  Listener:80 │      ├──────────────┤
  └─────────┘      └──────┬───────┘      │  EC2 (AZ-b)  │
                          │              └──────────────┘
                   Target Group
                   (round-robin)

Parameters:
  InstanceType:
    Type: String
    Default: t2.micro
    Description: EC2 instance type (t2.micro = free tier)

  LatestAmiId:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
    Description: Latest Amazon Linux 2023 AMI (auto-resolved via SSM)

Resources:
  # ============================================================
  # NETWORKING — VPC, Subnets, Internet Gateway, Route Table
  # ============================================================
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: alb-demo-vpc

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  PublicSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: alb-demo-public-a

  PublicSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: alb-demo-public-b

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  SubnetARouteTableAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnetA
      RouteTableId: !Ref PublicRouteTable

  SubnetBRouteTableAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnetB
      RouteTableId: !Ref PublicRouteTable

  # ============================================================
  # SECURITY GROUPS
  # ============================================================
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP to ALB
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: alb-demo-alb-sg

  EC2SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP from ALB only
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup
      Tags:
        - Key: Name
          Value: alb-demo-ec2-sg

  # ============================================================
  # EC2 INSTANCES
  # ============================================================
  WebServerA:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: !Ref LatestAmiId
      SubnetId: !Ref PublicSubnetA
      SecurityGroupIds:
        - !Ref EC2SecurityGroup
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          yum install -y httpd
          TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
          AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
          INSTANCE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
          echo "<h1>Hello from $INSTANCE in $AZ</h1>" > /var/www/html/index.html
          echo "OK" > /var/www/html/health
          systemctl start httpd
          systemctl enable httpd
      Tags:
        - Key: Name
          Value: alb-demo-web-a

  WebServerB:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: !Ref LatestAmiId
      SubnetId: !Ref PublicSubnetB
      SecurityGroupIds:
        - !Ref EC2SecurityGroup
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          yum install -y httpd
          TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
          AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
          INSTANCE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
          echo "<h1>Hello from $INSTANCE in $AZ</h1>" > /var/www/html/index.html
          echo "OK" > /var/www/html/health
          systemctl start httpd
          systemctl enable httpd
      Tags:
        - Key: Name
          Value: alb-demo-web-b

  # ============================================================
  # ALB — Load Balancer, Target Group, Listener
  # ============================================================
  ALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: my-demo-alb
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnetA
        - !Ref PublicSubnetB
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Tags:
        - Key: Name
          Value: alb-demo

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: my-web-targets
      Protocol: HTTP
      Port: 80
      VpcId: !Ref VPC
      TargetType: instance
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 10
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 2
      Targets:
        - Id: !Ref WebServerA
          Port: 80
        - Id: !Ref WebServerB
          Port: 80

  HTTPListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 80
      Protocol: HTTP
      DefaultAction:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

Outputs:
  ALBDNSName:
    Description: ALB public DNS name — open this in your browser
    Value: !GetAtt ALB.DNSName

  ALBURL:
    Description: Full URL
    Value: !Sub http://${ALB.DNSName}
```

### After Deploying

1. Wait for the stack to reach `CREATE_COMPLETE` (~3-5 minutes)
2. Go to **Outputs** tab → copy `ALBURL`
3. Open in browser — refresh to see it alternate between instances
4. Go to **EC2 → Target Groups → my-web-targets → Targets** to see health status

### Cleanup

```bash
aws cloudformation delete-stack --stack-name my-alb-stack --region eu-west-1
```

------

## 8. ALB + Lambda (Serverless Target)

ALB can invoke Lambda functions directly — no API Gateway needed.

```
  User  ──►  ALB  ──►  Lambda function
              │          (target type: lambda)
              │
          Target Group
          (type: lambda)
```

**When to use ALB + Lambda vs API Gateway + Lambda:**

| Feature | ALB + Lambda | API Gateway + Lambda |
|---------|-------------|---------------------|
| **Cost** | Pay per ALB hour + LCU | Pay per request |
| **Best for** | High-traffic, steady load | Bursty/low traffic, REST APIs |
| **WebSocket** | No | Yes |
| **Request validation** | No | Yes |
| **Usage plans / API keys** | No | Yes |
| **Fixed monthly cost** | ~$16/month minimum (ALB) | $0 at zero traffic |

**Lambda function for ALB** (different event format from API Gateway):

```python
import json

def lambda_handler(event, context):
    # ALB sends a different event structure than API Gateway
    return {
        "statusCode": 200,
        "statusDescription": "200 OK",        # required for ALB
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Hello from Lambda via ALB!",
            "path": event.get("path", "/")
        })
    }
```

------

## 9. Common Patterns

### Pattern 1: HTTP → HTTPS Redirect

```
Listener :80
  Rule: default → redirect to HTTPS :443, status 301

Listener :443 (certificate from ACM)
  Rule: default → forward to target group
```

### Pattern 2: Path-Based Routing (Microservices)

```
Listener :443
  Rule 1: path = /api/*      → target-group-api     (priority 1)
  Rule 2: path = /admin/*    → target-group-admin    (priority 2)
  Rule 3: path = /static/*   → target-group-cdn      (priority 3)
  Default:                    → target-group-frontend
```

### Pattern 3: Host-Based Routing (Multi-Tenant)

```
Listener :443
  Rule 1: host = api.myapp.com     → target-group-api
  Rule 2: host = admin.myapp.com   → target-group-admin
  Default: host = myapp.com        → target-group-frontend
```

### Pattern 4: Blue/Green Deployment

```
Listener :443
  Rule: default → forward
    100% → target-group-blue   (current live)
      0% → target-group-green  (new version)

  # Shift traffic gradually: 90/10 → 50/50 → 0/100
```

### Pattern 5: Maintenance Page

```
Listener :443
  Rule 1: default → fixed-response
    Status: 503
    Content-Type: text/html
    Body: "<h1>We'll be right back</h1><p>Scheduled maintenance in progress.</p>"
```

------

## 10. Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| ALB returns **502 Bad Gateway** | Target group targets are unhealthy | Check EC2 security group allows traffic from ALB SG |
| ALB returns **503 Service Unavailable** | No healthy targets | Verify health check path returns 200 |
| Health check keeps failing | Wrong port or path | Ensure app listens on the port configured in target group |
| Can't reach ALB at all | ALB security group | Allow inbound 80/443 from `0.0.0.0/0` |
| Traffic only goes to one instance | Sticky sessions enabled | Disable stickiness or test in incognito |
| Intermittent 504 Gateway Timeout | Target takes too long to respond | Increase idle timeout on ALB (default 60s) |
| ERR_CONNECTION_REFUSED after deploy | ALB still provisioning | Wait 1-2 min for state to become Active |

### Quick Debugging Commands

```bash
# Check target health from CLI
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-west-1:ACCOUNT:targetgroup/my-web-targets/abc123

# Check ALB state
aws elbv2 describe-load-balancers --names my-demo-alb

# Check listener rules
aws elbv2 describe-rules --listener-arn <listener-arn>

# Test ALB from terminal
curl -v http://my-demo-alb-123456.eu-west-1.elb.amazonaws.com/
curl -v http://my-demo-alb-123456.eu-west-1.elb.amazonaws.com/health
```
