"""Standardized response formatting utilities."""
from flask import jsonify


def success_response(data=None, message='Success', status_code=200):
    """Create standardized success response."""
    response = {
        'success': True,
        'message': message,
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


def error_response(error, message='Error', status_code=400):
    """Create standardized error response."""
    response = {
        'success': False,
        'error': {
            'code': error,
            'message': message,
        }
    }
    return jsonify(response), status_code


def validation_error_response(errors, status_code=400):
    """Create standardized validation error response."""
    response = {
        'success': False,
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': errors,
        }
    }
    return jsonify(response), status_code