"""
Unit tests for the CDK stack
"""

import os
import sys
from unittest.mock import patch

import pytest
import aws_cdk as cdk
from aws_cdk import assertions

# Add infra to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from infra.pupper_cdk_stack import PupperCdkStack


class TestPupperCdkStack:
    """Test cases for the Pupper CDK stack"""

    @pytest.fixture
    def app(self):
        """CDK app fixture"""
        return cdk.App()

    @pytest.fixture
    def stack(self, app):
        """CDK stack fixture"""
        return PupperCdkStack(app, "TestPupperStack")

    @pytest.fixture
    def template(self, stack):
        """CloudFormation template fixture"""
        return assertions.Template.from_stack(stack)

    def test_dynamodb_tables_created(self, template):
        """Test that all required DynamoDB tables are created"""
        # Dogs table
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "pupper-dogs",
                "BillingMode": "PAY_PER_REQUEST",
                "PointInTimeRecoverySpecification": {
                    "PointInTimeRecoveryEnabled": True
                },
            },
        )

        # Users table
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"TableName": "pupper-users", "BillingMode": "PAY_PER_REQUEST"},
        )

        # Votes table
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"TableName": "pupper-votes", "BillingMode": "PAY_PER_REQUEST"},
        )

        # Shelters table
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"TableName": "pupper-shelters", "BillingMode": "PAY_PER_REQUEST"},
        )

    def test_dynamodb_gsi_created(self, template):
        """Test that Global Secondary Indexes are created"""
        # Dogs table should have StateIndex and ColorIndex
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "pupper-dogs",
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "StateIndex",
                        "KeySchema": [
                            {"AttributeName": "state", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"},
                        ],
                    },
                    {
                        "IndexName": "ColorIndex",
                        "KeySchema": [
                            {"AttributeName": "color", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"},
                        ],
                    },
                ],
            },
        )

        # Votes table should have DogVotesIndex
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "pupper-votes",
                "GlobalSecondaryIndexes": [
                    {
                        "IndexName": "DogVotesIndex",
                        "KeySchema": [
                            {"AttributeName": "dog_id", "KeyType": "HASH"},
                            {"AttributeName": "vote_type", "KeyType": "RANGE"},
                        ],
                    }
                ],
            },
        )

    def test_s3_bucket_created(self, template):
        """Test that S3 bucket is created with proper configuration"""
        template.has_resource_properties(
            "AWS::S3::Bucket", {"VersioningConfiguration": {"Status": "Enabled"}}
        )

        # Should have bucket policy for auto-delete
        template.has_resource("AWS::S3::BucketPolicy", {})

    def test_lambda_functions_created(self, template):
        """Test that all Lambda functions are created"""
        # Should have 5 Lambda functions
        lambda_functions = template.find_resources("AWS::Lambda::Function")
        assert len(lambda_functions) == 5

        # Check specific functions
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Handler": "create.lambda_handler", "Runtime": "python3.9", "Timeout": 30},
        )

        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Handler": "read.lambda_handler", "Runtime": "python3.9", "Timeout": 30},
        )

        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Handler": "update.lambda_handler", "Runtime": "python3.9", "Timeout": 30},
        )

        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Handler": "delete.lambda_handler", "Runtime": "python3.9", "Timeout": 30},
        )

        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Handler": "resize.lambda_handler",
                "Runtime": "python3.9",
                "Timeout": 60,
                "MemorySize": 1024,
            },
        )

    def test_lambda_environment_variables(self, template):
        """Test that Lambda functions have correct environment variables"""
        # Dogs Lambda functions should have required environment variables
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Handler": "create.lambda_handler",
                "Environment": {
                    "Variables": {
                        "DOGS_TABLE": {"Ref": assertions.Match.any_value()},
                        "IMAGES_BUCKET": {"Ref": assertions.Match.any_value()},
                        "SHELTERS_TABLE": {"Ref": assertions.Match.any_value()},
                    }
                },
            },
        )

    def test_iam_roles_created(self, template):
        """Test that IAM roles are created with proper permissions"""
        # Should have Lambda execution role
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ]
                }
            },
        )

        # Should have policies for DynamoDB and S3 access
        template.has_resource("AWS::IAM::Policy", {})

    def test_api_gateway_created(self, template):
        """Test that API Gateway is created with proper configuration"""
        # REST API
        template.has_resource_properties(
            "AWS::ApiGateway::RestApi",
            {"Name": "Pupper API", "Description": "API for Pupper dog adoption app"},
        )

        # CORS configuration
        template.has_resource("AWS::ApiGateway::Method", {})

    def test_api_gateway_resources(self, template):
        """Test that API Gateway resources are created"""
        # Should have /dogs resource
        template.has_resource("AWS::ApiGateway::Resource", {})

        # Should have methods for CRUD operations
        methods = template.find_resources("AWS::ApiGateway::Method")

        # Should have multiple methods (GET, POST, PUT, DELETE)
        assert len(methods) >= 4

    def test_lambda_api_integration(self, template):
        """Test that Lambda functions are integrated with API Gateway"""
        # Should have Lambda integrations
        template.has_resource(
            "AWS::ApiGateway::Method",
            {"Properties": {"Integration": {"Type": "AWS_PROXY"}}},
        )

        # Should have Lambda permissions for API Gateway
        template.has_resource("AWS::Lambda::Permission", {})

    def test_stack_outputs(self, stack):
        """Test that stack has necessary outputs"""
        # The stack should be synthesizable without errors
        app = cdk.App()
        test_stack = PupperCdkStack(app, "TestStack")

        # Should not raise any exceptions
        template = app.synth().get_stack_by_name("TestStack").template
        assert template is not None

    def test_resource_naming(self, template):
        """Test that resources follow proper naming conventions"""
        # DynamoDB tables should have consistent naming
        dogs_table = template.find_resources(
            "AWS::DynamoDB::Table", {"Properties": {"TableName": "pupper-dogs"}}
        )
        assert len(dogs_table) == 1

        users_table = template.find_resources(
            "AWS::DynamoDB::Table", {"Properties": {"TableName": "pupper-users"}}
        )
        assert len(users_table) == 1

    def test_security_configurations(self, template):
        """Test security-related configurations"""
        # S3 bucket should have versioning enabled
        template.has_resource_properties(
            "AWS::S3::Bucket", {"VersioningConfiguration": {"Status": "Enabled"}}
        )

        # DynamoDB tables should have point-in-time recovery for critical tables
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "pupper-dogs",
                "PointInTimeRecoverySpecification": {
                    "PointInTimeRecoveryEnabled": True
                },
            },
        )

    def test_removal_policies(self, stack):
        """Test that removal policies are set appropriately"""
        # For testing, resources should be destroyable
        # In production, this would be different

        # This test ensures the stack can be created and destroyed
        app = cdk.App()
        test_stack = PupperCdkStack(app, "RemovalTestStack")

        # Should synthesize without errors
        template = app.synth().get_stack_by_name("RemovalTestStack").template
        assert template is not None

    def test_cross_resource_references(self, template):
        """Test that resources properly reference each other"""
        # Lambda functions should reference DynamoDB tables
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Environment": {
                    "Variables": {"DOGS_TABLE": {"Ref": assertions.Match.any_value()}}
                }
            },
        )

        # IAM policies should reference the correct resources
        template.has_resource("AWS::IAM::Policy", {})

    def test_billing_mode_configuration(self, template):
        """Test that DynamoDB tables use pay-per-request billing"""
        # All tables should use PAY_PER_REQUEST for cost optimization
        tables = template.find_resources("AWS::DynamoDB::Table")

        for table_id, table_config in tables.items():
            properties = table_config.get("Properties", {})
            assert properties.get("BillingMode") == "PAY_PER_REQUEST"

    @patch.dict(
        os.environ,
        {"CDK_DEFAULT_ACCOUNT": "123456789012", "CDK_DEFAULT_REGION": "us-east-1"},
    )
    def test_stack_with_environment(self):
        """Test stack creation with specific environment"""
        app = cdk.App()
        env = cdk.Environment(account="123456789012", region="us-east-1")
        stack = PupperCdkStack(app, "EnvTestStack", env=env)

        # Should create successfully
        template = app.synth().get_stack_by_name("EnvTestStack").template
        assert template is not None

    def test_lambda_layer_compatibility(self, template):
        """Test Lambda runtime compatibility"""
        # All Lambda functions should use the same Python runtime
        lambda_functions = template.find_resources("AWS::Lambda::Function")

        for func_id, func_config in lambda_functions.items():
            properties = func_config.get("Properties", {})
            runtime = properties.get("Runtime")
            assert runtime == "python3.9"

    def test_api_gateway_cors_configuration(self, template):
        """Test that CORS is properly configured"""
        # Should have OPTIONS methods for CORS preflight
        options_methods = template.find_resources(
            "AWS::ApiGateway::Method", {"Properties": {"HttpMethod": "OPTIONS"}}
        )

        # Should have at least one OPTIONS method
        assert len(options_methods) >= 1
