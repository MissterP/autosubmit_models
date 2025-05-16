"""
Context variables for request tracking and contextual logging.
"""

from contextvars import ContextVar

request_id_context = ContextVar("request_id", default=None)


def get_current_request_id():
    """
    Get the current request ID from the context variable.

    Returns:
        str or one: Thecurrent request ID if set, None otherwise.
    """
    return request_id_context.get()


def set_request_id(request_id):
    """
    Set the current request ID in the context variable.

    Args:
        request_id (str): The request ID to set.

    Return:
        Token: Context token for resseting
    """
    request_id_context.set(request_id)


def reset_request_id(token):
    """
    Reset the current request ID in the context variable.

    Args:
        token (Token): The token to reset the context variable.
    """
    request_id_context.reset(token)
