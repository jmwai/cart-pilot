"""
Constants for agent executor functionality.

This module contains shared constants used across the agent executor,
including tool status message mappings.
"""

# Tool name -> Status message mapping for dynamic status updates
# Maps function names to user-friendly status messages sent via A2A TaskStatusUpdateEvent
TOOL_STATUS_MESSAGES = {
    # Product Discovery
    'text_vector_search': 'Searching for products...',
    'image_vector_search': 'Finding visually similar products...',

    # Cart Operations
    'add_to_cart': 'Adding item to cart...',
    'get_cart': 'Loading your cart...',
    'update_cart_item': 'Updating cart...',
    'remove_from_cart': 'Removing item from cart...',
    'clear_cart': 'Clearing cart...',
    'get_cart_total': 'Calculating cart total...',

    # Checkout
    'create_order': 'Processing your order...',
    'get_order_status': 'Checking order status...',
    'cancel_order': 'Canceling order...',
    'validate_cart_for_checkout': 'Validating cart...',
    'prepare_order_summary': 'Preparing order summary...',

    # Customer Service
    'create_inquiry': 'Creating your inquiry...',
    'get_inquiry_status': 'Checking inquiry status...',
    'search_faq': 'Searching FAQ...',
    'initiate_return': 'Initiating return...',
    'get_order_inquiries': 'Retrieving order inquiries...',
}
