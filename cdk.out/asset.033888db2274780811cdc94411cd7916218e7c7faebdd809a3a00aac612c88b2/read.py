import json
import os
import boto3
import base64
from decimal import Decimal
from datetime import datetime, timedelta
import re

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def parse_date(date_str):
    """Parse MM/DD/YYYY date format"""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y")
    except:
        return None


def calculate_age_from_birthday(birthday_str):
    """Calculate age in years from birthday string"""
    try:
        birthday = parse_date(birthday_str)
        if birthday:
            today = datetime.now()
            age = today.year - birthday.year
            if today.month < birthday.month or (today.month == birthday.month and today.day < birthday.day):
                age -= 1
            return age
        return None
    except:
        return None


def matches_search_query(dog, search_query):
    """Check if dog matches search query (case-insensitive partial match)"""
    if not search_query:
        return True
    
    search_query = search_query.lower()
    searchable_fields = [
        dog.get("dog_name", ""),
        dog.get("dog_species", ""),
        dog.get("dog_description", ""),
        dog.get("shelter_name", ""),
        dog.get("city", ""),
        dog.get("state", ""),
        dog.get("dog_color", ""),
        str(dog.get("status", ""))
    ]
    
    # Search in all text fields
    for field in searchable_fields:
        if search_query in str(field).lower():
            return True
    
    # Search in tags if they exist
    tags = dog.get("tags", [])
    if isinstance(tags, list):
        for tag in tags:
            if search_query in str(tag).lower():
                return True
    
    return False


def apply_filters(dogs, filters):
    """Apply filters to the dogs list"""
    filtered_dogs = []
    
    for dog in dogs:
        # Skip if doesn't match search query
        if not matches_search_query(dog, filters.get("search")):
            continue
        
        # State filter
        if filters.get("state") and dog.get("state", "").upper() != filters["state"].upper():
            continue
        
        # City filter (partial match)
        if filters.get("city") and filters["city"].lower() not in dog.get("city", "").lower():
            continue
        
        # Weight filters
        dog_weight = dog.get("dog_weight")
        if dog_weight is not None:
            if filters.get("min_weight"):
                try:
                    if float(dog_weight) < float(filters["min_weight"]):
                        continue
                except (ValueError, TypeError):
                    pass
            
            if filters.get("max_weight"):
                try:
                    if float(dog_weight) > float(filters["max_weight"]):
                        continue
                except (ValueError, TypeError):
                    pass
        
        # Age filters
        dog_age = dog.get("dog_age_years")
        if dog_age is None and dog.get("dog_birthday"):
            dog_age = calculate_age_from_birthday(dog.get("dog_birthday"))
        
        if dog_age is not None:
            if filters.get("min_age"):
                try:
                    if float(dog_age) < float(filters["min_age"]):
                        continue
                except (ValueError, TypeError):
                    pass
            
            if filters.get("max_age"):
                try:
                    if float(dog_age) > float(filters["max_age"]):
                        continue
                except (ValueError, TypeError):
                    pass
        
        # Color filter (partial match)
        if filters.get("color") and filters["color"].lower() not in dog.get("dog_color", "").lower():
            continue
        
        # Status filter
        if filters.get("status") and dog.get("status", "").lower() != filters["status"].lower():
            continue
        
        # Species filter (partial match)
        if filters.get("species") and filters["species"].lower() not in dog.get("dog_species", "").lower():
            continue
        
        # Shelter filter (partial match)
        if filters.get("shelter") and filters["shelter"].lower() not in dog.get("shelter_name", "").lower():
            continue
        
        # Date range filters
        if filters.get("entry_date_from") or filters.get("entry_date_to"):
            entry_date = parse_date(dog.get("shelter_entry_date", ""))
            if entry_date:
                if filters.get("entry_date_from"):
                    from_date = parse_date(filters["entry_date_from"])
                    if from_date and entry_date < from_date:
                        continue
                
                if filters.get("entry_date_to"):
                    to_date = parse_date(filters["entry_date_to"])
                    if to_date and entry_date > to_date:
                        continue
        
        # Vote count filters
        if filters.get("min_wag_count"):
            try:
                if int(dog.get("wag_count", 0)) < int(filters["min_wag_count"]):
                    continue
            except (ValueError, TypeError):
                pass
        
        if filters.get("max_growl_count"):
            try:
                if int(dog.get("growl_count", 0)) > int(filters["max_growl_count"]):
                    continue
            except (ValueError, TypeError):
                pass
        
        # Boolean filters
        if filters.get("is_labrador") is not None:
            is_lab_filter = filters["is_labrador"].lower() in ["true", "1", "yes"]
            if dog.get("is_labrador", False) != is_lab_filter:
                continue
        
        # Tags filter (if dog has tags)
        if filters.get("tags"):
            filter_tags = [tag.strip().lower() for tag in filters["tags"].split(",")]
            dog_tags = [str(tag).lower() for tag in dog.get("tags", [])]
            if not any(tag in " ".join(dog_tags) for tag in filter_tags):
                continue
        
        filtered_dogs.append(dog)
    
    return filtered_dogs


def sort_dogs(dogs, sort_by, sort_order="asc"):
    """Sort dogs by specified field"""
    if not sort_by:
        return dogs
    
    reverse = sort_order.lower() == "desc"
    
    def get_sort_key(dog):
        value = dog.get(sort_by)
        
        # Handle different data types
        if sort_by in ["dog_weight", "dog_age_years", "wag_count", "growl_count"]:
            try:
                return float(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0
        
        elif sort_by in ["created_at", "updated_at", "shelter_entry_date", "dog_birthday"]:
            if sort_by in ["shelter_entry_date", "dog_birthday"]:
                date_obj = parse_date(str(value)) if value else None
                return date_obj if date_obj else datetime.min
            else:
                try:
                    return datetime.fromisoformat(str(value).replace('Z', '+00:00')) if value else datetime.min
                except:
                    return datetime.min
        
        else:
            return str(value).lower() if value else ""
    
    try:
        return sorted(dogs, key=get_sort_key, reverse=reverse)
    except Exception as e:
        print(f"Error sorting dogs: {e}")
        return dogs


def paginate_results(dogs, page=1, limit=20):
    """Paginate results"""
    try:
        page = max(1, int(page))
        limit = min(100, max(1, int(limit)))  # Max 100 items per page
    except (ValueError, TypeError):
        page = 1
        limit = 20
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    return {
        "dogs": dogs[start_idx:end_idx],
        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_items": len(dogs),
            "total_pages": (len(dogs) + limit - 1) // limit,
            "has_next": end_idx < len(dogs),
            "has_prev": page > 1
        }
    }


def lambda_handler(event, context):
    """Enhanced Lambda handler for reading dogs with advanced search and filtering"""
    
    try:
        print("Processing read dog request")
        
        # Check if this is a single dog request
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if dog_id:
            # Get single dog
            print(f"Getting single dog: {dog_id}")
            response = dogs_table.get_item(Key={"dog_id": dog_id})
            
            if "Item" not in response:
                return {
                    "statusCode": 404,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                        "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                    },
                    "body": json.dumps({
                        "success": False,
                        "error": "Dog not found"
                    })
                }
            
            dog = response["Item"]
            
            # Decrypt dog name
            if "dog_name_encrypted" in dog:
                try:
                    dog["dog_name"] = base64.b64decode(dog["dog_name_encrypted"]).decode()
                    del dog["dog_name_encrypted"]
                except:
                    dog["dog_name"] = "Unknown"
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                },
                "body": json.dumps({
                    "success": True,
                    "message": "Dog retrieved successfully",
                    "data": dog
                }, default=str)
            }
        
        else:
            # Get all dogs with advanced filtering
            print("Getting dogs with advanced filtering")
            
            # Get query parameters
            query_parameters = event.get("queryStringParameters") or {}
            
            # Scan all dogs
            response = dogs_table.scan()
            dogs = response.get("Items", [])
            
            # Decrypt dog names
            for dog in dogs:
                if "dog_name_encrypted" in dog:
                    try:
                        dog["dog_name"] = base64.b64decode(dog["dog_name_encrypted"]).decode()
                        del dog["dog_name_encrypted"]
                    except:
                        dog["dog_name"] = "Unknown"
            
            print(f"Found {len(dogs)} total dogs before filtering")
            
            # Apply filters
            filtered_dogs = apply_filters(dogs, query_parameters)
            print(f"Found {len(filtered_dogs)} dogs after filtering")
            
            # Sort results
            sort_by = query_parameters.get("sort_by", "created_at")
            sort_order = query_parameters.get("sort_order", "desc")
            sorted_dogs = sort_dogs(filtered_dogs, sort_by, sort_order)
            
            # Paginate results
            page = query_parameters.get("page", 1)
            limit = query_parameters.get("limit", 20)
            paginated_result = paginate_results(sorted_dogs, page, limit)
            
            # Prepare response
            applied_filters = {k: v for k, v in query_parameters.items() 
                             if k not in ["page", "limit", "sort_by", "sort_order"]}
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                },
                "body": json.dumps({
                    "success": True,
                    "message": "Dogs retrieved successfully",
                    "data": {
                        "dogs": paginated_result["dogs"],
                        "pagination": paginated_result["pagination"],
                        "filters_applied": applied_filters,
                        "sort": {
                            "sort_by": sort_by,
                            "sort_order": sort_order
                        }
                    }
                }, default=str)
            }

    except Exception as e:
        print(f"Error reading dogs: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
            },
            "body": json.dumps({
                "success": False,
                "error": "Internal server error"
            })
        }
