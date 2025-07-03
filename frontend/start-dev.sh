#!/bin/bash

# Pupper Frontend Development Startup Script

echo "🐕 Starting Pupper Frontend Development Server"
echo "=============================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ to continue."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Make sure you're in the frontend directory."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists, create if not
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << EOL
# Pupper Frontend Environment Variables
REACT_APP_API_URL=http://localhost:3001
REACT_APP_ENVIRONMENT=development

# Optional: Enable React Query DevTools
REACT_APP_ENABLE_DEVTOOLS=true
EOL
    echo "✅ .env file created with default values"
else
    echo "✅ .env file exists"
fi

# Display environment info
echo ""
echo "🔧 Environment Configuration:"
echo "   - API URL: ${REACT_APP_API_URL:-http://localhost:3001}"
echo "   - Environment: ${REACT_APP_ENVIRONMENT:-development}"
echo ""

# Check if backend is running (optional)
echo "🔍 Checking backend connectivity..."
if curl -s -f "${REACT_APP_API_URL:-http://localhost:3001}/health" > /dev/null 2>&1; then
    echo "✅ Backend is running and accessible"
else
    echo "⚠️  Backend may not be running at ${REACT_APP_API_URL:-http://localhost:3001}"
    echo "   Make sure to start the backend server for full functionality"
fi

echo ""
echo "🚀 Starting development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm start
