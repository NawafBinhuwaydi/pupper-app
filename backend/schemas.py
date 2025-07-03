"""
Data schemas and structures for the Pupper application
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json


class DogSchema:
    """
    Schema for dog data structure
    """

    @staticmethod
    def create_dog_record(
        shelter_name: str,
        city: str,
        state: str,
        dog_name: str,  # Will be encrypted before storage
        dog_species: str,
        shelter_entry_date: str,
        dog_description: str,
        dog_birthday: str,
        dog_weight: float,
        dog_color: str,
        dog_photo_url: Optional[str] = None,
        shelter_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized dog record
        """
        import uuid
        from datetime import datetime

        # Calculate age from birthday
        try:
            birth_date = datetime.strptime(dog_birthday, "%m/%d/%Y")
            age_years = (datetime.now() - birth_date).days / 365.25
        except:
            age_years = 0

        dog_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()

        return {
            "dog_id": dog_id,
            "shelter_name": shelter_name,
            "city": city,
            "state": state.upper(),  # Standardize state format
            "dog_name_encrypted": "",  # Will be populated by encryption function
            "dog_species": dog_species,
            "shelter_entry_date": shelter_entry_date,
            "dog_description": dog_description,
            "dog_birthday": dog_birthday,
            "dog_weight": float(dog_weight),
            "dog_color": dog_color.lower(),  # Standardize color format
            "dog_age_years": round(age_years, 1),
            "dog_photo_url": dog_photo_url,
            "dog_photo_400x400_url": "",  # Will be populated after image processing
            "dog_photo_50x50_url": "",  # Will be populated after image processing
            "shelter_id": shelter_id,
            "created_at": current_time,
            "updated_at": current_time,
            "is_labrador": dog_species.lower() == "labrador retriever",
            "wag_count": 0,
            "growl_count": 0,
            "status": "available",  # available, adopted, pending
        }

    @staticmethod
    def validate_dog_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate dog data against requirements
        """
        required_fields = [
            "shelter_name",
            "city",
            "state",
            "dog_name",
            "dog_species",
            "shelter_entry_date",
            "dog_description",
            "dog_birthday",
            "dog_weight",
            "dog_color",
        ]

        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"

        # Validate species (only Labrador Retrievers allowed)
        if data["dog_species"].lower() != "labrador retriever":
            return False, "Only Labrador Retrievers are allowed in the Pupper app"

        # Validate weight is numeric
        try:
            float(data["dog_weight"])
        except (ValueError, TypeError):
            return False, "Dog weight must be a valid number"

        # Validate dates
        try:
            datetime.strptime(data["dog_birthday"], "%m/%d/%Y")
            datetime.strptime(data["shelter_entry_date"], "%m/%d/%Y")
        except ValueError:
            return False, "Dates must be in MM/DD/YYYY format"

        return True, "Valid"


class UserSchema:
    """
    Schema for user data structure
    """

    @staticmethod
    def create_user_record(
        email: str,
        username: str,
        state_preference: Optional[str] = None,
        max_weight_preference: Optional[float] = None,
        min_weight_preference: Optional[float] = None,
        color_preference: Optional[str] = None,
        max_age_preference: Optional[float] = None,
        min_age_preference: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized user record
        """
        import uuid
        from datetime import datetime

        user_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()

        return {
            "user_id": user_id,
            "email": email,
            "username": username,
            "state_preference": state_preference.upper() if state_preference else None,
            "max_weight_preference": max_weight_preference,
            "min_weight_preference": min_weight_preference,
            "color_preference": color_preference.lower() if color_preference else None,
            "max_age_preference": max_age_preference,
            "min_age_preference": min_age_preference,
            "created_at": current_time,
            "updated_at": current_time,
            "is_active": True,
        }


class VoteSchema:
    """
    Schema for user votes (wags and growls)
    """

    @staticmethod
    def create_vote_record(
        user_id: str, dog_id: str, vote_type: str  # "wag" or "growl"
    ) -> Dict[str, Any]:
        """
        Create a standardized vote record
        """
        from datetime import datetime

        current_time = datetime.utcnow().isoformat()

        return {
            "user_id": user_id,
            "dog_id": dog_id,
            "vote_type": vote_type.lower(),
            "created_at": current_time,
            "updated_at": current_time,
        }

    @staticmethod
    def validate_vote_type(vote_type: str) -> bool:
        """
        Validate vote type
        """
        return vote_type.lower() in ["wag", "growl"]


class ShelterSchema:
    """
    Schema for shelter data structure
    """

    @staticmethod
    def create_shelter_record(
        shelter_name: str,
        city: str,
        state: str,
        contact_email: str,
        contact_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized shelter record
        """
        import uuid
        from datetime import datetime

        shelter_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()

        return {
            "shelter_id": shelter_id,
            "shelter_name": shelter_name,
            "city": city,
            "state": state.upper(),
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "created_at": current_time,
            "updated_at": current_time,
            "is_active": True,
            "dogs_count": 0,
        }


class FilterSchema:
    """
    Schema for filtering dogs
    """

    @staticmethod
    def parse_filters(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate filter parameters
        """
        filters = {}

        # State filter
        if "state" in query_params:
            filters["state"] = query_params["state"].upper()

        # Weight filters
        if "min_weight" in query_params:
            try:
                filters["min_weight"] = float(query_params["min_weight"])
            except (ValueError, TypeError):
                pass

        if "max_weight" in query_params:
            try:
                filters["max_weight"] = float(query_params["max_weight"])
            except (ValueError, TypeError):
                pass

        # Age filters
        if "min_age" in query_params:
            try:
                filters["min_age"] = float(query_params["min_age"])
            except (ValueError, TypeError):
                pass

        if "max_age" in query_params:
            try:
                filters["max_age"] = float(query_params["max_age"])
            except (ValueError, TypeError):
                pass

        # Color filter
        if "color" in query_params:
            filters["color"] = query_params["color"].lower()

        return filters


# Encryption utilities for dog names
class EncryptionUtils:
    """
    Utilities for encrypting/decrypting dog names
    """

    @staticmethod
    def encrypt_dog_name(dog_name: str, key: Optional[str] = None) -> str:
        """
        Encrypt dog name before storing in database
        Note: In production, use AWS KMS or proper encryption library
        """
        import base64

        # Simple base64 encoding for POC - replace with proper encryption
        encoded = base64.b64encode(dog_name.encode()).decode()
        return encoded

    @staticmethod
    def decrypt_dog_name(encrypted_name: str, key: Optional[str] = None) -> str:
        """
        Decrypt dog name for display
        """
        import base64

        try:
            decoded = base64.b64decode(encrypted_name.encode()).decode()
            return decoded
        except:
            return "Unknown"


class ImageSchema:
    """
    Schema for image data structure
    """

    @staticmethod
    def create_image_record(
        image_id: str,
        original_key: str,
        content_type: str,
        size_bytes: int,
        dog_id: Optional[str] = None,
        description: str = "",
        tags: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized image record
        """
        from datetime import datetime

        current_time = datetime.utcnow().isoformat()

        return {
            "image_id": image_id,
            "original_key": original_key,
            "original_url": f"https://s3.amazonaws.com/{original_key}",
            "content_type": content_type,
            "size_bytes": size_bytes,
            "status": "uploaded",
            "processing_status": "pending",
            "dog_id": dog_id,
            "description": description,
            "tags": tags or [],
            "resized_urls": {},
            "dimensions": {},
            "created_at": current_time,
            "updated_at": current_time,
            "error_message": None,
        }

    @staticmethod
    def validate_image_upload(data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate image upload data
        """
        required_fields = ["image_data", "content_type"]

        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"

        # Validate content type
        supported_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if data["content_type"].lower() not in supported_types:
            return (
                False,
                f"Unsupported content type. Supported: {', '.join(supported_types)}",
            )

        # Validate base64 image data
        try:
            import base64

            base64.b64decode(data["image_data"])
        except Exception:
            return False, "Invalid base64 image data"

        return True, "Valid"

    @staticmethod
    def get_supported_formats() -> list:
        """
        Get list of supported image formats
        """
        return ["image/jpeg", "image/jpg", "image/png", "image/webp"]

    @staticmethod
    def get_max_file_size() -> int:
        """
        Get maximum file size in bytes (50MB)
        """
        return 50 * 1024 * 1024

    @staticmethod
    def get_resize_configurations() -> list:
        """
        Get standard resize configurations
        """
        return [
            {"name": "400x400", "size": (400, 400), "format": "PNG"},
            {"name": "50x50", "size": (50, 50), "format": "PNG"},
            {"name": "800x600", "size": (800, 600), "format": "JPEG"},
            {"name": "200x150", "size": (200, 150), "format": "JPEG"},
        ]


# Response formatting utilities
class ResponseFormatter:
    """
    Utilities for formatting API responses
    """

    @staticmethod
    def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """
        Format successful API response
        """
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
            "body": json.dumps({"success": True, "message": message, "data": data}),
        }

    @staticmethod
    def error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
        """
        Format error API response
        """
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
            "body": json.dumps({"success": False, "error": error_message}),
        }
