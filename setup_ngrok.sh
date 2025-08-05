#!/bin/bash

# Ngrok Setup Script for Global iPhone Access
# This script sets up ngrok tunnel for Buddy AI Agent

echo "🌍 Setting up ngrok tunnel for global iPhone access..."
echo ""

# Check if ngrok is installed
if ! command -v ~/bin/ngrok &> /dev/null; then
    echo "❌ ngrok not found. Please run the installation commands first."
    exit 1
fi

# Check if authtoken is configured
if ! ~/bin/ngrok config check &> /dev/null; then
    echo "⚠️  Authentication required!"
    echo ""
    echo "1. Sign up for free ngrok account: https://dashboard.ngrok.com/signup"
    echo "2. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. Run: ~/bin/ngrok config add-authtoken YOUR_TOKEN_HERE"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  Buddy AI server not running on localhost:8000"
    echo "Please start the server first:"
    echo "  python main.py"
    echo ""
    exit 1
fi

echo "✅ Server is running on localhost:8000"
echo "🚀 Starting ngrok tunnel..."
echo ""

# Start ngrok tunnel
~/bin/ngrok http 8000 --log stdout --log-level info &
NGROK_PID=$!

# Wait for ngrok to start and get the URL
sleep 3

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if tunnels:
        print(tunnels[0]['public_url'])
    else:
        print('No tunnels found')
except:
    print('Error getting tunnel URL')
")

if [[ $PUBLIC_URL == *"https://"* ]]; then
    echo "🎉 Ngrok tunnel created successfully!"
    echo ""
    echo "📱 iPhone Siri Shortcut Configuration:"
    echo "   URL: $PUBLIC_URL/siri-chat"
    echo "   Method: POST"
    echo "   Headers: Content-Type: application/json"
    echo "   Body: {\"message\": \"Your voice input\", \"user_id\": \"YourName\"}"
    echo ""
    echo "🌍 Global Access URLs:"
    echo "   Siri Endpoint: $PUBLIC_URL/siri-chat"
    echo "   Chat Endpoint: $PUBLIC_URL/chat"
    echo "   Health Check: $PUBLIC_URL/health"
    echo ""
    echo "⚡ Test the tunnel:"
    echo "   curl -X GET $PUBLIC_URL/health"
    echo ""
    echo "🛑 To stop tunnel: kill $NGROK_PID"
else
    echo "❌ Failed to get tunnel URL. Check ngrok status at http://localhost:4040"
    kill $NGROK_PID 2>/dev/null
fi