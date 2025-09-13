#!/bin/bash

# Development setup script

echo "Setting up Chess Analysis App..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f server/.env ]; then
    echo "Creating environment file..."
    cp server/.env.example server/.env
    echo "Please edit server/.env with your MongoDB connection string and API keys."
fi

# Start services
echo "Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Services are starting up. This may take a few minutes..."
echo ""
echo "Once ready, you can access:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"