#!/bin/bash

# Test script for product_discovery_agent and cart_agent
# This script creates sessions, queries the product discovery agent,
# extracts a product ID, adds it to cart, and retrieves cart contents

APP_URL="http://localhost:8080"
APP_NAME="product_discovery_agent"
USER_ID="user_123"
SESSION_ID="session_$(date +%s)"

echo "================================================"
echo "Testing Product Discovery Agent & Cart Agent"
echo "================================================"
echo "App URL: $APP_URL"
echo "App Name: $APP_NAME"
echo "User ID: $USER_ID"
echo "Session ID: $SESSION_ID"
echo ""

# Step 1: Create or update a session
echo "Step 1: Creating session..."
echo "----------------------------------------"
curl -X POST \
    "$APP_URL/apps/$APP_NAME/users/$USER_ID/sessions/$SESSION_ID" \
    -H "Content-Type: application/json" \
    -d '{"state": {"preferred_language": "English"}}' \
    -w "\n"

echo ""
echo ""

# Step 2: Query the agent
echo "Step 2: Querying the agent..."
echo "----------------------------------------"
echo "Query: 'Find me some running shoes'"
echo ""

RESPONSE=$(curl -s -X POST \
    "$APP_URL/run_sse" \
    -H "Content-Type: application/json" \
    -d "{
        \"app_name\": \"$APP_NAME\",
        \"user_id\": \"$USER_ID\",
        \"session_id\": \"$SESSION_ID\",
        \"new_message\": {
            \"role\": \"user\",
            \"parts\": [{
                \"text\": \"Find me some running shoes\"
            }]
        },
        \"streaming\": false
    }")

echo "$RESPONSE"

# Extract a product ID from the response (look for "id" field in the JSON)
PRODUCT_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

echo ""
echo "Extracted Product ID: $PRODUCT_ID"
echo ""
echo ""

# Step 3: Add product to cart
if [ -n "$PRODUCT_ID" ]; then
    echo "Step 3: Adding product to cart..."
    echo "----------------------------------------"
    echo "Adding product: $PRODUCT_ID"
    echo ""
    
    CART_APP_NAME="cart_agent"
    
    # Create session for cart agent
    echo "Creating session for cart agent..."
    curl -X POST \
        "$APP_URL/apps/$CART_APP_NAME/users/$USER_ID/sessions/$SESSION_ID" \
        -H "Content-Type: application/json" \
        -d '{"state": {"preferred_language": "English"}}' \
        -w "\n"
    
    echo ""
    echo ""
    curl -X POST \
        "$APP_URL/run_sse" \
        -H "Content-Type: application/json" \
        -d "{
            \"app_name\": \"$CART_APP_NAME\",
            \"user_id\": \"$USER_ID\",
            \"session_id\": \"$SESSION_ID\",
            \"new_message\": {
                \"role\": \"user\",
                \"parts\": [{
                    \"text\": \"Add product $PRODUCT_ID to my cart with quantity 1\"
                }]
            },
            \"streaming\": false
        }" \
        -w "\n"
    
    echo ""
    echo ""
    
    # Step 4: Get cart contents
    echo "Step 4: Retrieving cart contents..."
    echo "----------------------------------------"
    echo ""
    
    curl -X POST \
        "$APP_URL/run_sse" \
        -H "Content-Type: application/json" \
        -d "{
            \"app_name\": \"$CART_APP_NAME\",
            \"user_id\": \"$USER_ID\",
            \"session_id\": \"$SESSION_ID\",
            \"new_message\": {
                \"role\": \"user\",
                \"parts\": [{
                    \"text\": \"Show me my cart\"
                }]
            },
            \"streaming\": false
        }" \
        -w "\n"
    
    echo ""
    echo ""
else
    echo "No product ID found, skipping cart operations"
    echo ""
fi

echo "================================================"
echo "Test complete!"
echo "================================================"