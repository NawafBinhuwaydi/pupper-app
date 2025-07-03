from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    RemovalPolicy,
    Duration,
    Size,
)
from constructs import Construct


class PupperCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for storing dog images
        self.images_bucket = s3.Bucket(
            self, "PupperImagesBucket",
            bucket_name=f"pupper-images-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # DynamoDB Tables
        
        # Dogs table - main table for dog data
        self.dogs_table = dynamodb.Table(
            self, "DogsTable",
            table_name="pupper-dogs",
            partition_key=dynamodb.Attribute(
                name="dog_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Add GSI for state-based queries
        self.dogs_table.add_global_secondary_index(
            index_name="StateIndex",
            partition_key=dynamodb.Attribute(
                name="state",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Add GSI for color-based queries
        self.dogs_table.add_global_secondary_index(
            index_name="ColorIndex",
            partition_key=dynamodb.Attribute(
                name="dog_color",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Users table - for user preferences and authentication
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="pupper-users",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Votes table - for tracking user votes on dogs
        self.votes_table = dynamodb.Table(
            self, "VotesTable",
            table_name="pupper-votes",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="dog_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add GSI for dog-based vote queries
        self.votes_table.add_global_secondary_index(
            index_name="DogVotesIndex",
            partition_key=dynamodb.Attribute(
                name="dog_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="vote_type",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Shelters table - for shelter authentication and data
        self.shelters_table = dynamodb.Table(
            self, "SheltersTable",
            table_name="pupper-shelters",
            partition_key=dynamodb.Attribute(
                name="shelter_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Images table - for image metadata and processing status
        self.images_table = dynamodb.Table(
            self, "ImagesTable",
            table_name="pupper-images",
            partition_key=dynamodb.Attribute(
                name="image_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add GSI for querying images by dog_id
        self.images_table.add_global_secondary_index(
            index_name="DogImagesIndex",
            partition_key=dynamodb.Attribute(
                name="dog_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Lambda execution role
        lambda_role = iam.Role(
            self, "PupperLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
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
                                "dynamodb:Scan"
                            ],
                            resources=[
                                f"arn:aws:dynamodb:{self.region}:{self.account}:table/pupper-*"
                            ]
                        )
                    ]
                ),
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject"
                            ],
                            resources=[f"arn:aws:s3:::pupper-images-{self.account}-{self.region}/*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["s3:ListBucket"],
                            resources=[f"arn:aws:s3:::pupper-images-{self.account}-{self.region}"]
                        )
                    ]
                )
            }
        )

        # Lambda Functions
        
        # Dogs CRUD operations
        self.create_dog_lambda = _lambda.Function(
            self, "CreateDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="create.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
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
            }
        )

        self.read_dog_lambda = _lambda.Function(
            self, "ReadDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="read.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
            }
        )

        self.update_dog_lambda = _lambda.Function(
            self, "UpdateDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="update.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "VOTES_TABLE": self.votes_table.table_name,
                "LOG_LEVEL": "INFO",
            }
        )

        self.delete_dog_lambda = _lambda.Function(
            self, "DeleteDogFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="delete.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/dogs"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
            }
        )

        # Image processing functions
        self.image_upload_lambda = _lambda.Function(
            self, "ImageUploadFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="upload.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/image_processing"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=1024,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_TABLE": self.images_table.table_name,
                "LOG_LEVEL": "INFO",
            }
        )

        self.image_processing_lambda = _lambda.Function(
            self, "ImageProcessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="resize.lambda_handler",
            code=_lambda.Code.from_asset("backend/lambda/image_processing"),
            role=lambda_role,
            timeout=Duration.seconds(300),  # 5 minutes for large images
            memory_size=3008,  # Maximum memory for large image processing
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "IMAGES_BUCKET": self.images_bucket.bucket_name,
                "DOGS_TABLE": self.dogs_table.table_name,
                "IMAGES_TABLE": self.images_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            ephemeral_storage_size=Size.mebibytes(2048)  # 2GB temp storage
        )

        # Grant Lambda invoke permissions (removed to avoid circular dependency)
        # self.image_upload_lambda.grant_invoke(lambda_role)

        # S3 event notification for automatic image processing
        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".jpg")
        )
        
        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".jpeg")
        )
        
        self.images_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.image_processing_lambda),
            s3.NotificationKeyFilter(prefix="uploads/", suffix=".png")
        )

        # API Gateway
        self.api = apigateway.RestApi(
            self, "PupperApi",
            rest_api_name="Pupper API",
            description="API for Pupper dog adoption app",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )

        # API Resources and Methods
        
        # /dogs resource
        dogs_resource = self.api.root.add_resource("dogs")
        
        # POST /dogs - Create dog
        dogs_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.create_dog_lambda)
        )
        
        # GET /dogs - List dogs
        dogs_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.read_dog_lambda)
        )

        # /dogs/{dog_id} resource
        dog_resource = dogs_resource.add_resource("{dog_id}")
        
        # GET /dogs/{dog_id} - Get specific dog
        dog_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.read_dog_lambda)
        )
        
        # PUT /dogs/{dog_id} - Update dog
        dog_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.update_dog_lambda)
        )
        
        # DELETE /dogs/{dog_id} - Delete dog
        dog_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(self.delete_dog_lambda)
        )

        # /dogs/{dog_id}/vote resource for voting
        vote_resource = dog_resource.add_resource("vote")
        vote_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.update_dog_lambda)
        )

        # /images resource for image upload
        images_resource = self.api.root.add_resource("images")
        
        # POST /images - Upload image
        images_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.image_upload_lambda)
        )
        
        # GET /images/{image_id} - Get image metadata
        image_resource = images_resource.add_resource("{image_id}")
        image_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.image_upload_lambda)
        )
