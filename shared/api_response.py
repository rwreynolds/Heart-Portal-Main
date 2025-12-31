"""
Standardized API response format for all Heart Portal components
Ensures consistent error handling and response structure
"""

from typing import Any, Dict, Optional, Tuple
from flask import jsonify, Response


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> Tuple[Response, int]:
    """
    Standard success response

    Args:
        data: Response payload (dict, list, or primitive)
        message: Success message
        status_code: HTTP status code (default: 200)

    Returns:
        Tuple of (JSON response, status code)

    Example:
        return success_response({"user": user_data}, "User created successfully", 201)
    """
    response = {
        "status": "success",
        "message": message
    }

    if data is not None:
        response["data"] = data

    return jsonify(response), status_code


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[Dict[str, Any]] = None
) -> Tuple[Response, int]:
    """
    Standard error response

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        errors: Additional error details (e.g., validation errors)

    Returns:
        Tuple of (JSON response, status code)

    Example:
        return error_response("Invalid email format", 400, {"email": ["Must be valid email"]})
    """
    response = {
        "status": "error",
        "message": message
    }

    if errors is not None:
        response["errors"] = errors

    return jsonify(response), status_code


def validation_error_response(
    errors: Dict[str, Any],
    message: str = "Validation failed"
) -> Tuple[Response, int]:
    """
    Specialized validation error response

    Args:
        errors: Dictionary of field-level validation errors
        message: General validation message

    Returns:
        Tuple of (JSON response, 422 status code)

    Example:
        return validation_error_response({
            "email": ["Email is required"],
            "password": ["Password must be at least 12 characters"]
        })
    """
    return error_response(message, 422, errors)


def not_found_response(
    resource: str = "Resource",
    resource_id: Any = None
) -> Tuple[Response, int]:
    """
    Standard 404 not found response

    Args:
        resource: Type of resource (e.g., "User", "Blog post")
        resource_id: ID of the resource that wasn't found

    Returns:
        Tuple of (JSON response, 404 status code)

    Example:
        return not_found_response("Blog post", post_id)
    """
    message = f"{resource} not found"
    if resource_id is not None:
        message += f" (ID: {resource_id})"

    return error_response(message, 404)


def unauthorized_response(
    message: str = "Authentication required"
) -> Tuple[Response, int]:
    """
    Standard 401 unauthorized response

    Args:
        message: Unauthorized message

    Returns:
        Tuple of (JSON response, 401 status code)
    """
    return error_response(message, 401)


def forbidden_response(
    message: str = "You don't have permission to access this resource"
) -> Tuple[Response, int]:
    """
    Standard 403 forbidden response

    Args:
        message: Forbidden message

    Returns:
        Tuple of (JSON response, 403 status code)
    """
    return error_response(message, 403)


def server_error_response(
    message: str = "An internal server error occurred",
    error_id: Optional[str] = None
) -> Tuple[Response, int]:
    """
    Standard 500 server error response

    Args:
        message: Error message (avoid exposing sensitive details)
        error_id: Optional error tracking ID for debugging

    Returns:
        Tuple of (JSON response, 500 status code)
    """
    response_data = {"error_id": error_id} if error_id else None
    return error_response(message, 500, response_data)
