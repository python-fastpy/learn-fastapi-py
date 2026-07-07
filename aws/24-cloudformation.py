# ══════════════════════════════════════════════════════════════════
# AWS Deployment — CloudFormation (Step 23)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 23-iam.py

# ╔══════════════════════════════════════════════════════════════╗
# ║   STEP 23: CLOUDFORMATION — INFRASTRUCTURE AS CODE          ║
# ╚══════════════════════════════════════════════════════════════╝
#
# WHAT: AWS CloudFormation lets you define ALL your AWS resources
#       in YAML (or JSON) templates. You describe WHAT you want,
#       CloudFormation figures out HOW to create it, in what ORDER,
#       and rolls back if anything fails.
#
# WHY:  Instead of clicking through the console 50 times (and
#       forgetting a setting), you write it once and deploy to
#       dev/qa/uat/prod with one command. It's like a Dockerfile
#       but for your entire AWS infrastructure.
#
# COST: CloudFormation itself is FREE. You only pay for the
#       resources it creates (EC2, S3, RDS, etc.).
#
# ── Console Steps vs CloudFormation ─────────────────────────
#
#   The previous files (02-vpc.py through 23-iam.py) show console
#   steps. This file shows how to do the SAME things as code.
#
#   ┌──────────────────────┬──────────────────────────────────┐
#   │ Console (manual)     │ CloudFormation (code)             │
#   ├──────────────────────┼──────────────────────────────────┤
#   │ Click "Create bucket"│ Type: AWS::S3::Bucket            │
#   │ Fill in form         │ Properties: BucketName: ...      │
#   │ Click "Create"       │ aws cloudformation create-stack   │
#   │ Repeat for QA, prod  │ Change --parameters and redeploy │
#   │ Delete manually      │ aws cloudformation delete-stack   │
#   │ Forgot a setting?    │ Git diff shows exactly what       │
#   │   Start over         │   changed. Update-stack applies.  │
#   └──────────────────────┴──────────────────────────────────┘
#
#
# ══════════════════════════════════════════════════════════════════
# PART 1: CORE CONCEPTS
# ══════════════════════════════════════════════════════════════════
#
# ── Template Anatomy ─────────────────────────────────────────
#
#   Every CloudFormation template has this structure:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  AWSTemplateFormatVersion: '2010-09-09'   # always this │
#   │  Description: What this stack does                       │
#   │                                                          │
#   │  Parameters:      # inputs (like function arguments)     │
#   │    ...                                                   │
#   │                                                          │
#   │  Conditions:      # if/else logic (optional)             │
#   │    ...                                                   │
#   │                                                          │
#   │  Resources:       # THE MAIN PART — what to create       │
#   │    ...            # (this is the only required section)  │
#   │                                                          │
#   │  Outputs:         # values to export (like return values)│
#   │    ...                                                   │
#   └──────────────────────────────────────────────────────────┘
#
# ── Intrinsic Functions (the !Bang syntax) ───────────────────
#
#   CloudFormation has built-in functions prefixed with !
#   Think of them like Python built-ins for YAML:
#
#   ┌────────────┬──────────────────────────────────────────────┐
#   │ Function   │ What it does                                 │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !Ref       │ Get value of a Parameter or resource ID.     │
#   │            │ !Ref Environment → "dev"                     │
#   │            │ !Ref MyBucket → "book-store-covers-123..."   │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !Sub       │ String substitution (like Python f-strings). │
#   │            │ !Sub 'arn:aws:s3:::${BucketName}/*'          │
#   │            │ ${AWS::AccountId} → your account number      │
#   │            │ ${AWS::Region} → eu-west-1                   │
#   │            │ ${AWS::StackName} → the stack's name         │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !GetAtt    │ Get a specific attribute of a resource.      │
#   │            │ !GetAtt MyBucket.Arn → full ARN              │
#   │            │ !GetAtt MyBucket.DomainName → S3 domain      │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !Join      │ Join strings with a delimiter.               │
#   │            │ !Join ['-', ['book', 'store']] → "book-store"│
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !Select    │ Pick item from a list by index.              │
#   │            │ !Select [0, [a, b, c]] → "a"                │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !Split     │ Split a string into a list.                  │
#   │            │ !Split [',', 'a,b,c'] → ['a', 'b', 'c']     │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !If        │ Conditional value (uses Conditions section). │
#   │            │ !If [IsProd, 2, 1] → 2 if prod, else 1      │
#   ├────────────┼──────────────────────────────────────────────┤
#   │ !ImportVal │ Import output from ANOTHER stack.            │
#   │            │ !ImportValue dev-CoverImagesBucketArn        │
#   └────────────┴──────────────────────────────────────────────┘
#
#   Pseudo-parameters (available in every template, no declaration):
#     ${AWS::AccountId}   → 060725138335
#     ${AWS::Region}      → eu-west-1
#     ${AWS::StackName}   → book-store-s3-dev
#     ${AWS::StackId}     → arn:aws:cloudformation:...
#     ${AWS::NoValue}     → removes a property conditionally
#
#
# ══════════════════════════════════════════════════════════════════
# PART 2: S3 BUCKET (from 03-s3.py — now as CloudFormation)
# ══════════════════════════════════════════════════════════════════
#
# ── Template ─────────────────────────────────────────────────
#
#   Save as  cloudformation/s3-bucket.yaml:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  AWSTemplateFormatVersion: '2010-09-09'                  │
#   │  Description: S3 bucket for book store cover images      │
#   │                                                          │
#   │  Parameters:                                             │
#   │    Environment:                                          │
#   │      Type: String                                        │
#   │      Default: dev                                        │
#   │      AllowedValues: [dev, qa, uat, prod]                 │
#   │                                                          │
#   │  Resources:                                              │
#   │    CoverImagesBucket:                                    │
#   │      Type: AWS::S3::Bucket                               │
#   │      Properties:                                         │
#   │        BucketName: !Sub                                  │
#   │          'book-store-covers-${AWS::AccountId}-${Environment}'│
#   │        VersioningConfiguration:                          │
#   │          Status: Enabled                                 │
#   │        BucketEncryption:                                 │
#   │          ServerSideEncryptionConfiguration:               │
#   │            - ServerSideEncryptionByDefault:               │
#   │                SSEAlgorithm: AES256                       │
#   │        PublicAccessBlockConfiguration:                    │
#   │          BlockPublicAcls: true                            │
#   │          BlockPublicPolicy: true                          │
#   │          IgnorePublicAcls: true                           │
#   │          RestrictPublicBuckets: true                      │
#   │        OwnershipControls:                                │
#   │          Rules:                                          │
#   │            - ObjectOwnership: BucketOwnerEnforced         │
#   │        LifecycleConfiguration:                           │
#   │          Rules:                                          │
#   │            - Id: MoveOldCoversToIA                        │
#   │              Status: Enabled                             │
#   │              Transitions:                                │
#   │                - StorageClass: STANDARD_IA                │
#   │                  TransitionInDays: 90                     │
#   │        Tags:                                             │
#   │          - Key: Project                                  │
#   │            Value: book-store                             │
#   │          - Key: Environment                              │
#   │            Value: !Ref Environment                       │
#   │                                                          │
#   │    CoverImagesBucketPolicy:                              │
#   │      Type: AWS::S3::BucketPolicy                         │
#   │      Properties:                                         │
#   │        Bucket: !Ref CoverImagesBucket                    │
#   │        PolicyDocument:                                   │
#   │          Version: '2012-10-17'                            │
#   │          Statement:                                      │
#   │            - Sid: AllowCloudFrontOAC                      │
#   │              Effect: Allow                               │
#   │              Principal:                                  │
#   │                Service: cloudfront.amazonaws.com          │
#   │              Action: s3:GetObject                        │
#   │              Resource: !Sub                              │
#   │                '${CoverImagesBucket.Arn}/*'              │
#   │              Condition:                                  │
#   │                StringEquals:                              │
#   │                  AWS:SourceArn: !Sub                      │
#   │                    'arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontDistId}'│
#   │                                                          │
#   │  Outputs:                                                │
#   │    BucketName:                                           │
#   │      Value: !Ref CoverImagesBucket                       │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-CoverImagesBucketName' │
#   │    BucketArn:                                            │
#   │      Value: !GetAtt CoverImagesBucket.Arn                │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-CoverImagesBucketArn'  │
#   └──────────────────────────────────────────────────────────┘
#
# ── Console ↔ CloudFormation mapping ─────────────────────────
#
#   ┌─────────────────────────────┬────────────────────────────────┐
#   │ Console Setting             │ CloudFormation Property         │
#   ├─────────────────────────────┼────────────────────────────────┤
#   │ Bucket name                 │ BucketName                      │
#   │ Region                      │ --region flag (CLI) or console  │
#   │ ACLs disabled               │ OwnershipControls →             │
#   │                             │   BucketOwnerEnforced           │
#   │ Block ALL public access     │ PublicAccessBlockConfiguration  │
#   │                             │   (all four set to true)        │
#   │ Bucket Versioning: Enable   │ VersioningConfiguration →      │
#   │                             │   Status: Enabled               │
#   │ Encryption: SSE-S3          │ BucketEncryption →              │
#   │                             │   SSEAlgorithm: AES256          │
#   │ Bucket policy (JSON)        │ AWS::S3::BucketPolicy resource  │
#   └─────────────────────────────┴────────────────────────────────┘
#
#
# ══════════════════════════════════════════════════════════════════
# PART 3: VPC (from 02-vpc.py — now as CloudFormation)
# ══════════════════════════════════════════════════════════════════
#
#   Save as  cloudformation/vpc.yaml:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  AWSTemplateFormatVersion: '2010-09-09'                  │
#   │  Description: VPC with public/private subnets in 2 AZs   │
#   │                                                          │
#   │  Parameters:                                             │
#   │    Environment:                                          │
#   │      Type: String                                        │
#   │      Default: dev                                        │
#   │      AllowedValues: [dev, qa, uat, prod]                 │
#   │                                                          │
#   │  Resources:                                              │
#   │    # ── The VPC itself ────────────────────────────────── │
#   │    VPC:                                                  │
#   │      Type: AWS::EC2::VPC                                 │
#   │      Properties:                                         │
#   │        CidrBlock: 10.0.0.0/16                            │
#   │        EnableDnsSupport: true                            │
#   │        EnableDnsHostnames: true                          │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-vpc-${Environment}'   │
#   │                                                          │
#   │    # ── Internet Gateway (front door to internet) ────── │
#   │    InternetGateway:                                      │
#   │      Type: AWS::EC2::InternetGateway                     │
#   │      Properties:                                         │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-igw-${Environment}'   │
#   │                                                          │
#   │    VPCGatewayAttachment:                                 │
#   │      Type: AWS::EC2::VPCGatewayAttachment                │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │        InternetGatewayId: !Ref InternetGateway           │
#   │                                                          │
#   │    # ── Public Subnets ──────────────────────────────── │
#   │    PublicSubnetA:                                        │
#   │      Type: AWS::EC2::Subnet                              │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │        CidrBlock: 10.0.1.0/24                            │
#   │        AvailabilityZone: !Select                         │
#   │          - 0                                             │
#   │          - !GetAZs ''                                    │
#   │        MapPublicIpOnLaunch: true                         │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-public-a-${Environment}'│
#   │                                                          │
#   │    PublicSubnetB:                                        │
#   │      Type: AWS::EC2::Subnet                              │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │        CidrBlock: 10.0.2.0/24                            │
#   │        AvailabilityZone: !Select                         │
#   │          - 1                                             │
#   │          - !GetAZs ''                                    │
#   │        MapPublicIpOnLaunch: true                         │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-public-b-${Environment}'│
#   │                                                          │
#   │    # ── Private Subnets ─────────────────────────────── │
#   │    PrivateSubnetA:                                       │
#   │      Type: AWS::EC2::Subnet                              │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │        CidrBlock: 10.0.11.0/24                           │
#   │        AvailabilityZone: !Select                         │
#   │          - 0                                             │
#   │          - !GetAZs ''                                    │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-private-a-${Environment}'│
#   │                                                          │
#   │    PrivateSubnetB:                                       │
#   │      Type: AWS::EC2::Subnet                              │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │        CidrBlock: 10.0.12.0/24                           │
#   │        AvailabilityZone: !Select                         │
#   │          - 1                                             │
#   │          - !GetAZs ''                                    │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-private-b-${Environment}'│
#   │                                                          │
#   │    # ── NAT Gateway (private→internet, 1-way) ────────  │
#   │    NatEIP:                                               │
#   │      Type: AWS::EC2::EIP                                 │
#   │      Properties:                                         │
#   │        Domain: vpc                                       │
#   │                                                          │
#   │    NatGateway:                                           │
#   │      Type: AWS::EC2::NatGateway                          │
#   │      Properties:                                         │
#   │        AllocationId: !GetAtt NatEIP.AllocationId         │
#   │        SubnetId: !Ref PublicSubnetA                      │
#   │        Tags:                                             │
#   │          - Key: Name                                     │
#   │            Value: !Sub 'book-store-nat-${Environment}'   │
#   │                                                          │
#   │    # ── Route Tables ────────────────────────────────── │
#   │    PublicRouteTable:                                     │
#   │      Type: AWS::EC2::RouteTable                          │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │                                                          │
#   │    PublicRoute:                                          │
#   │      Type: AWS::EC2::Route                               │
#   │      DependsOn: VPCGatewayAttachment                    │
#   │      Properties:                                         │
#   │        RouteTableId: !Ref PublicRouteTable               │
#   │        DestinationCidrBlock: 0.0.0.0/0                   │
#   │        GatewayId: !Ref InternetGateway                   │
#   │                                                          │
#   │    PublicSubnetARouteTableAssoc:                         │
#   │      Type: AWS::EC2::SubnetRouteTableAssociation         │
#   │      Properties:                                         │
#   │        SubnetId: !Ref PublicSubnetA                      │
#   │        RouteTableId: !Ref PublicRouteTable               │
#   │                                                          │
#   │    PublicSubnetBRouteTableAssoc:                         │
#   │      Type: AWS::EC2::SubnetRouteTableAssociation         │
#   │      Properties:                                         │
#   │        SubnetId: !Ref PublicSubnetB                      │
#   │        RouteTableId: !Ref PublicRouteTable               │
#   │                                                          │
#   │    PrivateRouteTable:                                    │
#   │      Type: AWS::EC2::RouteTable                          │
#   │      Properties:                                         │
#   │        VpcId: !Ref VPC                                   │
#   │                                                          │
#   │    PrivateRoute:                                        │
#   │      Type: AWS::EC2::Route                               │
#   │      Properties:                                         │
#   │        RouteTableId: !Ref PrivateRouteTable              │
#   │        DestinationCidrBlock: 0.0.0.0/0                   │
#   │        NatGatewayId: !Ref NatGateway                     │
#   │                                                          │
#   │    PrivateSubnetARouteTableAssoc:                        │
#   │      Type: AWS::EC2::SubnetRouteTableAssociation         │
#   │      Properties:                                         │
#   │        SubnetId: !Ref PrivateSubnetA                     │
#   │        RouteTableId: !Ref PrivateRouteTable              │
#   │                                                          │
#   │    PrivateSubnetBRouteTableAssoc:                        │
#   │      Type: AWS::EC2::SubnetRouteTableAssociation         │
#   │      Properties:                                         │
#   │        SubnetId: !Ref PrivateSubnetB                     │
#   │        RouteTableId: !Ref PrivateRouteTable              │
#   │                                                          │
#   │    # ── Security Groups ─────────────────────────────── │
#   │    ALBSecurityGroup:                                     │
#   │      Type: AWS::EC2::SecurityGroup                       │
#   │      Properties:                                         │
#   │        GroupDescription: Allow HTTP/HTTPS from internet   │
#   │        VpcId: !Ref VPC                                   │
#   │        SecurityGroupIngress:                             │
#   │          - IpProtocol: tcp                               │
#   │            FromPort: 80                                  │
#   │            ToPort: 80                                    │
#   │            CidrIp: 0.0.0.0/0                             │
#   │          - IpProtocol: tcp                               │
#   │            FromPort: 443                                 │
#   │            ToPort: 443                                   │
#   │            CidrIp: 0.0.0.0/0                             │
#   │                                                          │
#   │    AppSecurityGroup:                                     │
#   │      Type: AWS::EC2::SecurityGroup                       │
#   │      Properties:                                         │
#   │        GroupDescription: Allow traffic only from ALB      │
#   │        VpcId: !Ref VPC                                   │
#   │        SecurityGroupIngress:                             │
#   │          - IpProtocol: tcp                               │
#   │            FromPort: 8000                                │
#   │            ToPort: 8000                                  │
#   │            SourceSecurityGroupId: !Ref ALBSecurityGroup  │
#   │                                                          │
#   │  Outputs:                                                │
#   │    VpcId:                                                │
#   │      Value: !Ref VPC                                     │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-VpcId'                 │
#   │    PublicSubnetIds:                                      │
#   │      Value: !Join                                        │
#   │        - ','                                             │
#   │        - [!Ref PublicSubnetA, !Ref PublicSubnetB]        │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-PublicSubnetIds'       │
#   │    PrivateSubnetIds:                                     │
#   │      Value: !Join                                        │
#   │        - ','                                             │
#   │        - [!Ref PrivateSubnetA, !Ref PrivateSubnetB]      │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-PrivateSubnetIds'      │
#   │    ALBSecurityGroupId:                                   │
#   │      Value: !Ref ALBSecurityGroup                        │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-ALBSecurityGroupId'    │
#   │    AppSecurityGroupId:                                   │
#   │      Value: !Ref AppSecurityGroup                        │
#   │      Export:                                             │
#   │        Name: !Sub '${Environment}-AppSecurityGroupId'    │
#   └──────────────────────────────────────────────────────────┘
#
# ── Console ↔ CloudFormation mapping ─────────────────────────
#
#   ┌─────────────────────────────┬────────────────────────────────┐
#   │ Console Setting (VPC)       │ CloudFormation Resource         │
#   ├─────────────────────────────┼────────────────────────────────┤
#   │ "VPC and more" wizard       │ VPC + Subnets + IGW + NAT +    │
#   │                             │ RouteTables (each a resource)  │
#   │ CIDR block: 10.0.0.0/16    │ VPC → CidrBlock               │
#   │ Number of AZs: 2           │ Two subnets with !Select       │
#   │                             │ [0/1, !GetAZs '']             │
#   │ Public subnets: 2          │ PublicSubnetA, PublicSubnetB    │
#   │ Private subnets: 2         │ PrivateSubnetA, PrivateSubnetB │
#   │ NAT gateways: In 1 AZ     │ One NatGateway + EIP resource  │
#   │ DNS hostnames: Enable      │ EnableDnsHostnames: true        │
#   │ DNS resolution: Enable     │ EnableDnsSupport: true          │
#   │ ALB SG inbound rules       │ SecurityGroupIngress list       │
#   │ App SG: source = ALB SG    │ SourceSecurityGroupId: !Ref     │
#   └─────────────────────────────┴────────────────────────────────┘
#
#
# ══════════════════════════════════════════════════════════════════
# PART 4: ECS FARGATE (from 08-ecs-fargate.py — now as CFN)
# ══════════════════════════════════════════════════════════════════
#
#   Save as  cloudformation/ecs-fargate.yaml:
#
#   This template imports VPC outputs from the VPC stack above
#   using !ImportValue, so deploy the VPC stack first.
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  AWSTemplateFormatVersion: '2010-09-09'                  │
#   │  Description: ECS Fargate service for book store API     │
#   │                                                          │
#   │  Parameters:                                             │
#   │    Environment:                                          │
#   │      Type: String                                        │
#   │      Default: dev                                        │
#   │    ImageUri:                                             │
#   │      Type: String                                        │
#   │      Description: ECR image URI (acct.dkr.ecr.region...) │
#   │    ContainerPort:                                        │
#   │      Type: Number                                        │
#   │      Default: 8000                                       │
#   │                                                          │
#   │  Resources:                                              │
#   │    # ── ECS Cluster ─────────────────────────────────── │
#   │    ECSCluster:                                           │
#   │      Type: AWS::ECS::Cluster                             │
#   │      Properties:                                         │
#   │        ClusterName: !Sub 'book-store-${Environment}'     │
#   │                                                          │
#   │    # ── Task Execution Role (ECS pulls image, writes    │
#   │    #    logs — NOT your app's permissions) ──────────── │
#   │    TaskExecutionRole:                                    │
#   │      Type: AWS::IAM::Role                                │
#   │      Properties:                                         │
#   │        AssumeRolePolicyDocument:                         │
#   │          Version: '2012-10-17'                            │
#   │          Statement:                                      │
#   │            - Effect: Allow                               │
#   │              Principal:                                  │
#   │                Service: ecs-tasks.amazonaws.com           │
#   │              Action: sts:AssumeRole                      │
#   │        ManagedPolicyArns:                                │
#   │          - arn:aws:iam::aws:policy/service-role/          │
#   │              AmazonECSTaskExecutionRolePolicy            │
#   │                                                          │
#   │    # ── Task Definition (what to run) ───────────────── │
#   │    TaskDefinition:                                       │
#   │      Type: AWS::ECS::TaskDefinition                      │
#   │      Properties:                                         │
#   │        Family: !Sub 'book-store-api-${Environment}'      │
#   │        Cpu: '256'                                        │
#   │        Memory: '512'                                     │
#   │        NetworkMode: awsvpc                               │
#   │        RequiresCompatibilities: [FARGATE]                │
#   │        ExecutionRoleArn: !GetAtt TaskExecutionRole.Arn   │
#   │        ContainerDefinitions:                             │
#   │          - Name: api                                     │
#   │            Image: !Ref ImageUri                          │
#   │            PortMappings:                                 │
#   │              - ContainerPort: !Ref ContainerPort         │
#   │            LogConfiguration:                             │
#   │              LogDriver: awslogs                          │
#   │              Options:                                    │
#   │                awslogs-group: !Ref LogGroup              │
#   │                awslogs-region: !Ref 'AWS::Region'        │
#   │                awslogs-stream-prefix: ecs                │
#   │                                                          │
#   │    # ── CloudWatch Log Group ────────────────────────── │
#   │    LogGroup:                                             │
#   │      Type: AWS::Logs::LogGroup                           │
#   │      Properties:                                         │
#   │        LogGroupName: !Sub                                │
#   │          '/ecs/book-store-${Environment}'                │
#   │        RetentionInDays: 30                               │
#   │                                                          │
#   │    # ── ECS Service (how many tasks, which subnets) ─── │
#   │    ECSService:                                           │
#   │      Type: AWS::ECS::Service                             │
#   │      Properties:                                         │
#   │        Cluster: !Ref ECSCluster                          │
#   │        TaskDefinition: !Ref TaskDefinition               │
#   │        DesiredCount: 2                                   │
#   │        LaunchType: FARGATE                               │
#   │        NetworkConfiguration:                             │
#   │          AwsvpcConfiguration:                            │
#   │            Subnets:                                      │
#   │              - !ImportValue                              │
#   │                  !Sub '${Environment}-PrivateSubnetA'    │
#   │              - !ImportValue                              │
#   │                  !Sub '${Environment}-PrivateSubnetB'    │
#   │            SecurityGroups:                               │
#   │              - !ImportValue                              │
#   │                  !Sub '${Environment}-AppSecurityGroupId'│
#   └──────────────────────────────────────────────────────────┘
#
#
# ══════════════════════════════════════════════════════════════════
# PART 5: DEPLOYING STACKS
# ══════════════════════════════════════════════════════════════════
#
# ── Deploy via CLI ───────────────────────────────────────────
#
#   # Validate (catches syntax errors before deploying)
#   aws cloudformation validate-template \
#       --template-body file://cloudformation/s3-bucket.yaml
#
#   # Create a new stack
#   aws cloudformation create-stack \
#       --stack-name book-store-s3-dev \
#       --template-body file://cloudformation/s3-bucket.yaml \
#       --parameters ParameterKey=Environment,ParameterValue=dev \
#       --region eu-west-1
#
#   # Update an existing stack (after changing the template)
#   aws cloudformation update-stack \
#       --stack-name book-store-s3-dev \
#       --template-body file://cloudformation/s3-bucket.yaml \
#       --parameters ParameterKey=Environment,ParameterValue=dev \
#       --region eu-west-1
#
#   # Check stack status
#   aws cloudformation describe-stacks \
#       --stack-name book-store-s3-dev \
#       --query 'Stacks[0].StackStatus'
#
#   # View stack outputs (bucket name, ARN, etc.)
#   aws cloudformation describe-stacks \
#       --stack-name book-store-s3-dev \
#       --query 'Stacks[0].Outputs'
#
#   # Preview changes before applying (like terraform plan)
#   aws cloudformation create-change-set \
#       --stack-name book-store-s3-dev \
#       --template-body file://cloudformation/s3-bucket.yaml \
#       --change-set-name my-changes
#   aws cloudformation describe-change-set \
#       --stack-name book-store-s3-dev \
#       --change-set-name my-changes
#   # If it looks good:
#   aws cloudformation execute-change-set \
#       --stack-name book-store-s3-dev \
#       --change-set-name my-changes
#
#   # Delete the stack (removes ALL resources it created)
#   aws cloudformation delete-stack \
#       --stack-name book-store-s3-dev
#
#   # For stacks that create IAM resources, add:
#   --capabilities CAPABILITY_IAM
#   # or for custom-named IAM resources:
#   --capabilities CAPABILITY_NAMED_IAM
#
# ── Deploy via Console ───────────────────────────────────────
#
#   1. AWS Console → search "CloudFormation" → click CloudFormation
#
#   2. Click "Create stack" → "With new resources (standard)"
#
#   3. Template source:
#      ┌──────────────────────────────────────────────────┐
#      │  Template source: Upload a template file          │
#      │  Choose file:     cloudformation/s3-bucket.yaml   │
#      └──────────────────────────────────────────────────┘
#
#   4. Stack name: book-store-s3-dev
#
#   5. Parameters:
#      ┌──────────────────────────────────────────────────┐
#      │  Environment: dev                                 │
#      └──────────────────────────────────────────────────┘
#
#   6. Click "Next" → "Next" → check "I acknowledge that AWS
#      CloudFormation might create IAM resources" → "Submit"
#
#   7. Wait for status: CREATE_COMPLETE (~1-2 minutes for S3,
#      ~5 minutes for VPC, ~10 minutes for ECS)
#
#   8. Click "Outputs" tab → see exported values
#
#   9. To update: select stack → "Update" → upload new template
#
#  10. To delete: select stack → "Delete" → confirm
#
# ── Deploy Order (stacks depend on each other) ──────────────
#
#   Stacks that Export values must be deployed BEFORE stacks
#   that ImportValue from them. Our deploy order:
#
#   ┌───────────────────┐
#   │  1. VPC stack      │  exports: VpcId, SubnetIds, SG IDs
#   └────────┬──────────┘
#            │ imports VpcId, SubnetIds
#            ▼
#   ┌───────────────────┐
#   │  2. S3 stack       │  exports: BucketName, BucketArn
#   └────────┬──────────┘  (independent — can deploy in parallel
#            │              with VPC, but shown sequential for clarity)
#            ▼
#   ┌───────────────────┐
#   │  3. ECS stack      │  imports: SubnetIds, SG IDs from VPC
#   └───────────────────┘
#
#   Deploy all three for dev:
#   aws cloudformation create-stack --stack-name book-store-vpc-dev ...
#   # wait for CREATE_COMPLETE
#   aws cloudformation create-stack --stack-name book-store-s3-dev ...
#   aws cloudformation create-stack --stack-name book-store-ecs-dev ...
#
#   Deploy the same for prod (just change the parameter):
#   aws cloudformation create-stack --stack-name book-store-vpc-prod \
#       --parameters ParameterKey=Environment,ParameterValue=prod ...
#
#
# ══════════════════════════════════════════════════════════════════
# PART 6: STACK LIFECYCLE & TROUBLESHOOTING
# ══════════════════════════════════════════════════════════════════
#
# ── Stack States ─────────────────────────────────────────────
#
#   ┌────────────────────────┬─────────────────────────────────┐
#   │ Status                 │ Meaning                          │
#   ├────────────────────────┼─────────────────────────────────┤
#   │ CREATE_IN_PROGRESS     │ Creating resources...            │
#   │ CREATE_COMPLETE        │ All resources created ✓          │
#   │ CREATE_FAILED          │ Something broke → auto-rollback  │
#   │ UPDATE_IN_PROGRESS     │ Updating resources...            │
#   │ UPDATE_COMPLETE        │ Update applied ✓                 │
#   │ UPDATE_ROLLBACK_*      │ Update failed → rolling back     │
#   │ DELETE_IN_PROGRESS     │ Deleting resources...            │
#   │ DELETE_COMPLETE        │ Stack gone ✓                     │
#   │ DELETE_FAILED          │ Can't delete (resource in use)   │
#   │ ROLLBACK_COMPLETE      │ Create failed, rolled back ✓     │
#   └────────────────────────┴─────────────────────────────────┘
#
# ── Common Errors & Fixes ────────────────────────────────────
#
#   "No updates are to be performed"
#     → Template hasn't changed. Nothing to do.
#
#   "ROLLBACK_COMPLETE" state (stuck, can't update)
#     → The initial create failed. You must delete the stack
#       and create it again. Fix the template first.
#       aws cloudformation delete-stack --stack-name <name>
#
#   "DELETE_FAILED" (can't delete)
#     → A resource is in use or not empty (e.g., S3 bucket
#       with objects). Empty it first, then retry delete.
#       aws s3 rm s3://bucket-name --recursive
#       aws cloudformation delete-stack --stack-name <name>
#
#   "Export <name> cannot be deleted as it is in use"
#     → Another stack imports this output. Delete the
#       dependent stack first, then delete this one.
#
#   "Requires capabilities: [CAPABILITY_IAM]"
#     → Stack creates IAM resources. Add --capabilities flag:
#       aws cloudformation create-stack ... --capabilities CAPABILITY_IAM
#
# ── Drift Detection ──────────────────────────────────────────
#
#   Someone changed a resource manually in the console?
#   Drift detection shows what's different from the template.
#
#   aws cloudformation detect-stack-drift \
#       --stack-name book-store-s3-dev
#   aws cloudformation describe-stack-drift-detection-status \
#       --stack-drift-detection-id <id>
#   aws cloudformation describe-stack-resource-drifts \
#       --stack-name book-store-s3-dev
#
#   Console: select stack → "Stack actions" → "Detect drift"
#
#
# ══════════════════════════════════════════════════════════════════
# PART 7: CLOUDFORMATION vs ALTERNATIVES
# ══════════════════════════════════════════════════════════════════
#
#   ┌──────────────────┬──────────────────────────────────────────┐
#   │ Tool             │ When to use                              │
#   ├──────────────────┼──────────────────────────────────────────┤
#   │ CloudFormation   │ AWS-only, free, native. Used in this     │
#   │                  │ guide. Best if you're 100% on AWS.       │
#   ├──────────────────┼──────────────────────────────────────────┤
#   │ AWS CDK          │ Write infra in Python/TypeScript instead │
#   │                  │ of YAML. Generates CloudFormation under  │
#   │                  │ the hood. Better for complex logic.      │
#   │                  │ (The skills repo uses CDK — see          │
#   │                  │ sphinx_leon-assistant-skills/*/infra/)    │
#   ├──────────────────┼──────────────────────────────────────────┤
#   │ Terraform        │ Multi-cloud (AWS + GCP + Azure). Has its │
#   │                  │ own state file. Widely used in industry. │
#   ├──────────────────┼──────────────────────────────────────────┤
#   │ Pulumi           │ Like CDK but multi-cloud. Real           │
#   │                  │ programming languages, not YAML/HCL.     │
#   ├──────────────────┼──────────────────────────────────────────┤
#   │ Console (manual) │ Learning, one-off experiments, debugging.│
#   │                  │ Never for production — not reproducible. │
#   └──────────────────┴──────────────────────────────────────────┘
#
#   CloudFormation → CDK progression:
#     1. Learn CloudFormation YAML first (this file)
#     2. Graduate to CDK when templates get long or repetitive
#     3. CDK lets you write: Bucket("my-bucket") instead of
#        20 lines of YAML — but it compiles TO CloudFormation
#
#   The concepts (stacks, parameters, outputs, exports, drift)
#   are the SAME in all of these. Learn them once here.
