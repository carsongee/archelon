"""
Classic utility module for removing repetitive tasks and such
"""


from flask import jsonify


def jsonify_code(src_object, status_code):
    """Wrap jsonify with a status code option for jsonifying non-200
    responses.

    Args:
        src_object (serializable object): data structure to jsonify
        status_code (int): Status code to send

    Returns:
        werkzug response object with json MIME-type
    """
    response = jsonify(src_object)
    response.status_code = status_code
    return response
