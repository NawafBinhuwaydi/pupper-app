"""
Unit tests for data schemas
"""

import os
import sys
from datetime import datetime

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from schemas import (
    DogSchema,
    UserSchema,
    VoteSchema,
    ShelterSchema,
    FilterSchema,
    EncryptionUtils,
    ResponseFormatter,
)


class TestDogSchema:
    """Test cases for DogSchema"""

    @pytest.fixture
    def valid_dog_data(self):
        """Valid dog data for testing"""
        return {
            "shelter_name": "Arlington Shelter",
            "city": "Arlington",
            "state": "VA",
            "dog_name": "Fido",
            "dog_species": "Labrador Retriever",
            "shelter_entry_date": "1/7/2019",
            "dog_description": "Good boy",
            "dog_birthday": "4/23/2014",
            "dog_weight": 32,
            "dog_color": "Brown",
        }

    def test_create_dog_record_success(self, valid_dog_data):
        """Test successful dog record creation"""
        record = DogSchema.create_dog_record(**valid_dog_data)

        # Check required fields
        assert record["shelter_name"] == "Arlington Shelter"
        assert record["state"] == "VA"  # Should be uppercase
        assert record["dog_color"] == "brown"  # Should be lowercase
        assert record["is_labrador"] is True
        assert record["wag_count"] == 0
        assert record["growl_count"] == 0
        assert record["status"] == "available"

        # Check generated fields
        assert "dog_id" in record
        assert "created_at" in record
        assert "updated_at" in record
        assert "dog_age_years" in record

        # Check age calculation
        assert isinstance(record["dog_age_years"], (int, float))
        assert record["dog_age_years"] > 0

    def test_validate_dog_data_success(self, valid_dog_data):
        """Test successful dog data validation"""
        is_valid, message = DogSchema.validate_dog_data(valid_dog_data)

        assert is_valid is True
        assert message == "Valid"

    def test_validate_dog_data_missing_field(self, valid_dog_data):
        """Test validation with missing required field"""
        del valid_dog_data["dog_name"]

        is_valid, message = DogSchema.validate_dog_data(valid_dog_data)

        assert is_valid is False
        assert "Missing required field: dog_name" in message

    def test_validate_dog_data_invalid_species(self, valid_dog_data):
        """Test validation with invalid species"""
        valid_dog_data["dog_species"] = "Golden Retriever"

        is_valid, message = DogSchema.validate_dog_data(valid_dog_data)

        assert is_valid is False
        assert "Only Labrador Retrievers are allowed" in message

    def test_validate_dog_data_invalid_weight(self, valid_dog_data):
        """Test validation with invalid weight"""
        valid_dog_data["dog_weight"] = "thirty pounds"

        is_valid, message = DogSchema.validate_dog_data(valid_dog_data)

        assert is_valid is False
        assert "weight must be a valid number" in message

    def test_validate_dog_data_invalid_date(self, valid_dog_data):
        """Test validation with invalid date format"""
        valid_dog_data["dog_birthday"] = "2014-04-23"

        is_valid, message = DogSchema.validate_dog_data(valid_dog_data)

        assert is_valid is False
        assert "MM/DD/YYYY format" in message


class TestUserSchema:
    """Test cases for UserSchema"""

    def test_create_user_record_success(self):
        """Test successful user record creation"""
        record = UserSchema.create_user_record(
            email="test@example.com",
            username="testuser",
            state_preference="va",
            max_weight_preference=50,
            color_preference="Brown",
        )

        # Check required fields
        assert record["email"] == "test@example.com"
        assert record["username"] == "testuser"
        assert record["state_preference"] == "VA"  # Should be uppercase
        assert record["color_preference"] == "brown"  # Should be lowercase
        assert record["is_active"] is True

        # Check generated fields
        assert "user_id" in record
        assert "created_at" in record
        assert "updated_at" in record

    def test_create_user_record_minimal(self):
        """Test user record creation with minimal data"""
        record = UserSchema.create_user_record(
            email="test@example.com", username="testuser"
        )

        assert record["email"] == "test@example.com"
        assert record["username"] == "testuser"
        assert record["state_preference"] is None
        assert record["max_weight_preference"] is None


class TestVoteSchema:
    """Test cases for VoteSchema"""

    def test_create_vote_record_wag(self):
        """Test creating a wag vote record"""
        record = VoteSchema.create_vote_record(
            user_id="user-123", dog_id="dog-456", vote_type="WAG"
        )

        assert record["user_id"] == "user-123"
        assert record["dog_id"] == "dog-456"
        assert record["vote_type"] == "wag"  # Should be lowercase
        assert "created_at" in record
        assert "updated_at" in record

    def test_create_vote_record_growl(self):
        """Test creating a growl vote record"""
        record = VoteSchema.create_vote_record(
            user_id="user-123", dog_id="dog-456", vote_type="GROWL"
        )

        assert record["vote_type"] == "growl"  # Should be lowercase

    def test_validate_vote_type_valid(self):
        """Test validation of valid vote types"""
        assert VoteSchema.validate_vote_type("wag") is True
        assert VoteSchema.validate_vote_type("WAG") is True
        assert VoteSchema.validate_vote_type("growl") is True
        assert VoteSchema.validate_vote_type("GROWL") is True

    def test_validate_vote_type_invalid(self):
        """Test validation of invalid vote types"""
        assert VoteSchema.validate_vote_type("like") is False
        assert VoteSchema.validate_vote_type("dislike") is False
        assert VoteSchema.validate_vote_type("") is False
        assert VoteSchema.validate_vote_type("invalid") is False


class TestShelterSchema:
    """Test cases for ShelterSchema"""

    def test_create_shelter_record_success(self):
        """Test successful shelter record creation"""
        record = ShelterSchema.create_shelter_record(
            shelter_name="Arlington Shelter",
            city="Arlington",
            state="va",
            contact_email="contact@arlington.shelter",
            contact_phone="555-1234",
        )

        assert record["shelter_name"] == "Arlington Shelter"
        assert record["city"] == "Arlington"
        assert record["state"] == "VA"  # Should be uppercase
        assert record["contact_email"] == "contact@arlington.shelter"
        assert record["contact_phone"] == "555-1234"
        assert record["is_active"] is True
        assert record["dogs_count"] == 0

        # Check generated fields
        assert "shelter_id" in record
        assert "created_at" in record
        assert "updated_at" in record

    def test_create_shelter_record_minimal(self):
        """Test shelter record creation with minimal data"""
        record = ShelterSchema.create_shelter_record(
            shelter_name="Test Shelter",
            city="Test City",
            state="TX",
            contact_email="test@shelter.com",
        )

        assert record["contact_phone"] is None


class TestFilterSchema:
    """Test cases for FilterSchema"""

    def test_parse_filters_all_valid(self):
        """Test parsing all valid filter parameters"""
        query_params = {
            "state": "va",
            "min_weight": "20",
            "max_weight": "50",
            "min_age": "1",
            "max_age": "10",
            "color": "Brown",
        }

        filters = FilterSchema.parse_filters(query_params)

        assert filters["state"] == "VA"  # Should be uppercase
        assert filters["min_weight"] == 20.0
        assert filters["max_weight"] == 50.0
        assert filters["min_age"] == 1.0
        assert filters["max_age"] == 10.0
        assert filters["color"] == "brown"  # Should be lowercase

    def test_parse_filters_invalid_numbers(self):
        """Test parsing with invalid numeric values"""
        query_params = {
            "min_weight": "invalid",
            "max_age": "not_a_number",
            "state": "CA",
        }

        filters = FilterSchema.parse_filters(query_params)

        # Invalid numbers should be ignored
        assert "min_weight" not in filters
        assert "max_age" not in filters
        # Valid filters should still work
        assert filters["state"] == "CA"

    def test_parse_filters_empty(self):
        """Test parsing empty filter parameters"""
        filters = FilterSchema.parse_filters({})

        assert filters == {}


class TestEncryptionUtils:
    """Test cases for EncryptionUtils"""

    def test_encrypt_decrypt_dog_name(self):
        """Test dog name encryption and decryption"""
        original_name = "Buddy"

        encrypted = EncryptionUtils.encrypt_dog_name(original_name)
        decrypted = EncryptionUtils.decrypt_dog_name(encrypted)

        assert encrypted != original_name
        assert decrypted == original_name

    def test_encrypt_dog_name_empty(self):
        """Test encryption of empty string"""
        encrypted = EncryptionUtils.encrypt_dog_name("")
        decrypted = EncryptionUtils.decrypt_dog_name(encrypted)

        assert decrypted == ""

    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data"""
        invalid_encrypted = "invalid_base64_data!"
        decrypted = EncryptionUtils.decrypt_dog_name(invalid_encrypted)

        assert decrypted == "Unknown"

    def test_encrypt_special_characters(self):
        """Test encryption with special characters"""
        special_name = "Fido-123 & Buddy!"

        encrypted = EncryptionUtils.encrypt_dog_name(special_name)
        decrypted = EncryptionUtils.decrypt_dog_name(encrypted)

        assert decrypted == special_name


class TestResponseFormatter:
    """Test cases for ResponseFormatter"""

    def test_success_response_default(self):
        """Test success response with default message"""
        data = {"test": "data"}
        response = ResponseFormatter.success_response(data)

        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" in response

        # Check headers
        headers = response["headers"]
        assert headers["Content-Type"] == "application/json"
        assert headers["Access-Control-Allow-Origin"] == "*"

        # Check body
        import json

        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["message"] == "Success"
        assert body["data"] == data

    def test_success_response_custom_message(self):
        """Test success response with custom message"""
        data = {"test": "data"}
        message = "Custom success message"
        response = ResponseFormatter.success_response(data, message)

        import json

        body = json.loads(response["body"])
        assert body["message"] == message

    def test_error_response_default(self):
        """Test error response with default status code"""
        error_message = "Something went wrong"
        response = ResponseFormatter.error_response(error_message)

        assert response["statusCode"] == 400
        assert "headers" in response
        assert "body" in response

        import json

        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == error_message

    def test_error_response_custom_status(self):
        """Test error response with custom status code"""
        error_message = "Not found"
        response = ResponseFormatter.error_response(error_message, 404)

        assert response["statusCode"] == 404

        import json

        body = json.loads(response["body"])
        assert body["error"] == error_message

    def test_response_cors_headers(self):
        """Test that responses include proper CORS headers"""
        response = ResponseFormatter.success_response({})
        headers = response["headers"]

        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
