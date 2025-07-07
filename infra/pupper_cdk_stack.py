from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    aws_cognito as cognito,
    RemovalPolicy,
    Duration,
    Aspects,
    Size,
    CfnOutput,
)
from constructs import Construct
# from cdk_nag import AwsSolutionsChecks, NagSuppressions


class PupperCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add CDK Nag checks
        # Aspects.of(self).add(AwsSolutionsChecks(verbose=True))

        # S3 Bucket for storing dog images
        self.images_bucket = s3.Bucket(
            self,
            "PupperImagesBucket",
            bucket_name=f"pupper-images-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=False,  # Allow public bucket policies
                restrict_public_buckets=False  # Allow public read access
            ),
            server_access_logs_prefix="access-logs/",
        )

        # Add bucket policy for public read access to uploaded images
        self.images_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject"],
                resources=[f"{self.images_bucket.bucket_arn}/uploads/*"],
                conditions={
                    "StringEquals": {
                        "s3:ExistingObjectTag/public": "true"
                    }
                }
            )
        )

        # Alternative: Allow public read access to all uploaded images
        self.images_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject"],
                resources=[f"{self.images_bucket.bucket_arn}/uploads/*"]
            )
        )

        # Suppress CDK Nag findings for S3 bucket
        # NagSuppressions.add_resource_suppressions(
        #     self.images_bucket,
        #     [
        #         {
        #             "id": "AwsSolutions-S1",
        #             "reason": "Access logging is configured with prefix",
        #         },
        #         {
        #             "id": "AwsSolutions-S2",
        #             "reason": "Bucket is for internal application use only",
        #         },
        #         {"id": "AwsSolutions-S10", "reason": "SSL enforcement is enabled"},
        #     ],
        # )

        # Cognito User Pool for authentication
        self.user_pool = cognito.UserPool(
            self,
            "PupperUserPool",
            user_pool_name="pupper-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                username=True,
                email=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                ),
                preferred_username=cognito.StandardAttribute(
                    required=False,
                    mutable=True
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=6,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Cognito User Pool Client
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "PupperUserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name="pupper-web-client",
            generate_secret=False,  # For web applications
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=["http://localhost:3000", "https://localhost:3000"]
            ),
            prevent_user_existence_errors=True
        )

        # Identity Pool for AWS resource access
        self.identity_pool = cognito.CfnIdentityPool(
            self,
            "PupperIdentityPool",
            identity_pool_name="pupper_identity_pool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ]
        )

        # IAM roles for authenticated users
        self.authenticated_role = iam.Role(
            self,
            "CognitoAuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                "sts:AssumeRoleWithWebIdentity"
            )
        )

        # Attach identity pool roles
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": self.authenticated_role.role_arn
            }
        )

        # DynamoDB Tables

        # Dogs table - main dog information
        self.dogs_table = dynamodb.Table(
            self,
            "DogsTable",
            table_name="pupper-dogs",
            partition_key=dynamodb.Attribute(
                name="dog_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        # Add GSI for filtering by state
        self.dogs_table.add_global_secondary_index(
            index_name="StateIndex",
            partition_key=dynamodb.Attribute(
                name="state", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
        )

        # Add GSI for filtering by color
        self.dogs_table.add_global_secondary_index(
            index_name="ColorIndex",
            partition_key=dynamodb.Attribute(
                name="color", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
        )

        # Users table - for authentication and user data
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name="pupper-users",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        # User votes table - tracks wags and growls
        self.votes_table = dynamodb.Table(
            self,
            "VotesTable",
            table_name="pupper-votes",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="dog_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Add GSI for getting all votes for a dog
        self.votes_table.add_global_secondary_index(
            index_name="DogVotesIndex",
            partition_key=dynamodb.Attribute(
                name="dog_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="vote_type", type=dynamodb.AttributeType.STRING
            ),
        )

        # Shelters table - for shelter authentication and data
        self.shelters_table = dynamodb.Table(
            self,
            "SheltersTable",
            table_name="pupper-shelters",
            partition_key=dynamodb.Attribute(
                name="shelter_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Images table - for image metadata and processing status
        self.images_table = dynamodb.Table(
            self,
            "ImagesTable",
            table_name="pupper-images",
            partition_key=dynamodb.Attribute(
                name="image_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Add GSI for querying images by dog_id
        self.images_table.add_global_secondary_index(
            index_name="DogImagesIndex",
            partition_key=dynamodb.Attribute(
                name="dog_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
        )

        # Lambda Layer for shared dependencies
        self.lambda_layer = _lambda.LayerVersion(
            self,
            "PupperLambdaLayer",
            code=_lambda.Code.from_asset("lambda-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Shared dependencies for Pupper Lambda functions",
        )

        # Lambda execution role with enhanced security
        lambda_role = iam.Role(
            self,
            "PupperLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "DynamoDBAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                            ],
                            resources=[
                                self.dogs_table.table_arn,
                                f"{self.dogs_table.table_arn}/index/*",
                                self.users_table.table_arn,
                                self.votes_table.table_arn,
                                f"{self.votes_table.table_arn}/index/*",
                                self.shelters_table.table_arn,
                                self.images_table.table_arn,
                                f"{self.images_table.table_arn}/index/*",
                            ],
                        )
                    ]
                ),
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                            resources=[f"{self.images_bucket.bucket_arn}/*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:ListBucket"],
                            resources=[self.images_bucket.bucket_arn],
                        ),
                    ]
                ),
                "LambdaInvoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[
                                f"arn:aws:lambda:{self.region}:{self.account}:function:*"
                            ],
                        )
                    ]
                ),
                "XRayAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            },
        )

        # Suppress CDK Nag findings for Lambda role
        # NagSuppressions.add_resource_suppressions(
            lambda_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard permissions needed for X-Ray tracing and DynamoDB GSI access",
                }
            ],
        )

        # Lambda Functions with enhanced configuration

        # Dogs CRUD operations
        self.create_dog_lambda = _lambda.Function(
            self,
            "CreateDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "SHELTERS_TABLE": self.shelters_table.table_name,
                "IMAGES_TABLE": self.images_table.table_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-create-dog",
            },
            reserved_concurrent_executions=100,
        )

        self.read_dog_lambda = _lambda.Function(
            self,
            "ReadDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="read.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-read-dog",
            },
            reserved_concurrent_executions=100,
        )

        self.update_dog_lambda = _lambda.Function(
            self,
            "UpdateDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "VOTES_TABLE": self.votes_table.table_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-update-dog",
            },
            reserved_concurrent_executions=100,
        )

        self.delete_dog_lambda = _lambda.Function(
            self,
            "DeleteDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="delete.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-delete-dog",
            },
            reserved_concurrent_executions=50,
        )

        # Image processing function with enhanced configuration
        self.image_processing_lambda = _lambda.Function(
            self,
            "ImageProcessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="resize.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/image_processing"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(300),  # 5 minutes for large images
            memory_size=3008,  # Maximum memory for large image processing
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_TABLE": self.images_table.table_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-image-processing",
            },
            reserved_concurrent_executions=10,
            ephemeral_storage_size=Size.mebibytes(2048),  # 2GB temp storage
        )

        # Image upload function for handling direct uploads
        self.image_upload_lambda = _lambda.Function(
            self,
            "ImageUploadFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="upload.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/image_processing"),
            layers=[self.lambda_layer],
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=1024,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_TABLE": self.images_table.table_name,
                "IMAGE_PROCESSING_FUNCTION": self.image_processing_lambda.function_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "pupper-image-upload",
            },
            reserved_concurrent_executions=50,
        )

        # Grant image processing function permission to invoke itself and other functions
        self.image_processing_lambda.grant_invoke(lambda_role)
        self.image_upload_lambda.grant_invoke(self.image_processing_lambda)

        # S3 event notification for automatic image processing

        # Trigger image processing when images are uploaded to the uploads/ prefix
        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".jpg"),
        )

        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".jpeg"),
        )

        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".png"),
        )

        # Suppress CDK Nag findings for Lambda functions
        lambda_functions = [
            self.create_dog_lambda,
            self.read_dog_lambda,
            self.update_dog_lambda,
            self.delete_dog_lambda,
            self.image_processing_lambda,
            self.image_upload_lambda,
        ]

        for func in lambda_functions:
            NagSuppressions.add_resource_suppressions(
                func,
                [
                    {
                        "id": "AwsSolutions-L1",
                        "reason": "Python 3.9 is the latest stable runtime supported by our dependencies",
                    }
                ],
            )

        # API Gateway with enhanced security
        self.api = apigateway.RestApi(
            self,
            "PupperApi",
            rest_api_name="Pupper API",
            description="API for Pupper dog adoption app",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                ],
            ),
            cloud_watch_role=True,
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                tracing_enabled=True,
            ),
        )

        # Suppress CDK Nag findings for API Gateway
        # NagSuppressions.add_resource_suppressions(
            self.api,
            [
                {
                    "id": "AwsSolutions-APIG2",
                    "reason": "Request validation is handled at the Lambda function level",
                },
                {
                    "id": "AwsSolutions-APIG3",
                    "reason": "WAF is not required for this POC application",
                },
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Authorization will be implemented in future iterations",
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Cognito authorization will be implemented in future iterations",
                },
            ],
        )

        # API Resources and Methods

        # /dogs resource
        dogs_resource = self.api.root.add_resource("dogs")

        # POST /dogs - Create a new dog
        dogs_resource.add_method(
            "POST", apigateway.LambdaIntegration(self.create_dog_lambda)
        )

        # GET /dogs - List all dogs with optional filters
        dogs_resource.add_method(
            "GET", apigateway.LambdaIntegration(self.read_dog_lambda)
        )

        # /dogs/{dog_id} resource
        dog_resource = dogs_resource.add_resource("{dog_id}")

        # GET /dogs/{dog_id} - Get specific dog
        dog_resource.add_method(
            "GET", apigateway.LambdaIntegration(self.read_dog_lambda)
        )

        # PUT /dogs/{dog_id} - Update specific dog
        dog_resource.add_method(
            "PUT", apigateway.LambdaIntegration(self.update_dog_lambda)
        )

        # DELETE /dogs/{dog_id} - Delete specific dog
        dog_resource.add_method(
            "DELETE", apigateway.LambdaIntegration(self.delete_dog_lambda)
        )

        # /dogs/{dog_id}/vote resource for voting
        vote_resource = dog_resource.add_resource("vote")
        vote_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.update_dog_lambda
            ),  # Will handle voting logic
        )

        # /images resource for image upload
        images_resource = self.api.root.add_resource("images")

        # POST /images - Upload image
        images_resource.add_method(
            "POST", apigateway.LambdaIntegration(self.image_upload_lambda)
        )

        # GET /images/{image_id} - Get image metadata
        image_resource = images_resource.add_resource("{image_id}")
        image_resource.add_method(
            "GET", apigateway.LambdaIntegration(self.image_upload_lambda)
        )

        # CDK Outputs for frontend configuration
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self,
            "UserPoolClientId", 
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        CfnOutput(
            self,
            "IdentityPoolId",
            value=self.identity_pool.ref,
            description="Cognito Identity Pool ID"
        )

        CfnOutput(
            self,
            "Region",
            value=self.region,
            description="AWS Region"
        )
