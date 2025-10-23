#!/bin/bash

# Test script for product_discovery_agent
# This script creates a session and queries the agent

APP_URL="http://localhost:8080"
APP_NAME="product_discovery_agent"
USER_ID="user_123"
SESSION_ID="session_$(date +%s)"

echo "================================================"
echo "Testing Product Discovery Agent"
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

curl -X POST \
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
    }" \
    -w "\n"

echo ""
echo ""

# # Step 3: Query again with a different question
# echo "Step 3: Querying again with a different question..."
# echo "----------------------------------------"
# echo "Query: 'What products do you have?'"
# echo ""

# curl -X POST \
#     "$APP_URL/run_sse" \
#     -H "Content-Type: application/json" \
#     -d "{
#         \"app_name\": \"$APP_NAME\",
#         \"user_id\": \"$USER_ID\",
#         \"session_id\": \"$SESSION_ID\",
#         \"new_message\": {
#             \"role\": \"user\",
#             \"parts\": [{
#                 \"text\": \"What products do you have?\"
#             }]
#         },
#         \"streaming\": false
#     }" \
#     -w "\n"

# echo ""
# echo "================================================"
# echo "Test complete!"
# echo "================================================"

