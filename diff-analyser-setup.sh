#!/bin/bash

# create-diff-service-structure.sh
# Script to create the complete file and folder structure for diff-service project
# Run this script from outside the diff-service folder

set -e  # Exit on any error

PROJECT_DIR="diff-analyser"

echo "🚀 Creating diff-service project structure..."

# Check if diff-service directory exists, if not create it
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Creating diff-service directory..."
    mkdir "$PROJECT_DIR"
fi

echo "📁 Creating directory structure..."

# Create main directories
mkdir -p "$PROJECT_DIR/app"
mkdir -p "$PROJECT_DIR/tests"
mkdir -p "$PROJECT_DIR/scripts"
mkdir -p "$PROJECT_DIR/logs"

echo "📄 Creating root level files..."

# Root level files (empty with basic comments)
cat > "$PROJECT_DIR/README.md" << 'EOF'
# Diff Service

GitHub PR webhook processor for AI code analysis pipeline.
EOF

touch "$PROJECT_DIR/requirements.txt"
echo "# Python dependencies" > "$PROJECT_DIR/requirements.txt"

touch "$PROJECT_DIR/.env.example"
echo "# Environment variables template" > "$PROJECT_DIR/.env.example"

touch "$PROJECT_DIR/.gitignore"
echo "# Git ignore patterns" > "$PROJECT_DIR/.gitignore"

touch "$PROJECT_DIR/Dockerfile"
echo "# Docker configuration" > "$PROJECT_DIR/Dockerfile"

touch "$PROJECT_DIR/docker-compose.yml"
echo "# Docker compose configuration" > "$PROJECT_DIR/docker-compose.yml"

echo "📝 Creating app module files..."

# App module files
cat > "$PROJECT_DIR/app/__init__.py" << 'EOF'
"""
Diff Service

A Python service for processing GitHub PR webhooks and extracting code diffs
for AI analysis pipeline.
"""
EOF

cat > "$PROJECT_DIR/app/main.py" << 'EOF'
"""
FastAPI application entry point for diff service.
"""
# TODO: Implement FastAPI app and entry point
EOF

cat > "$PROJECT_DIR/app/config.py" << 'EOF'
"""
Configuration management for diff service.
"""
# TODO: Implement configuration management
EOF

cat > "$PROJECT_DIR/app/models.py" << 'EOF'
"""
All data models for diff service.
"""
# TODO: Implement all data models (PR, FileDiff, ParsedDiff, etc.)
EOF

cat > "$PROJECT_DIR/app/github_client.py" << 'EOF'
"""
GitHub API client for diff service.
"""
# TODO: Implement GitHub API client with authentication and rate limiting
EOF

cat > "$PROJECT_DIR/app/diff_parser.py" << 'EOF'
"""
Core diff parsing logic for diff service.
"""
# TODO: Implement core diff parsing logic
EOF

cat > "$PROJECT_DIR/app/webhook_handler.py" << 'EOF'
"""
Webhook processing for diff service.
"""
# TODO: Implement webhook processing logic
EOF

cat > "$PROJECT_DIR/app/utils.py" << 'EOF'
"""
Utility functions for diff service.
"""
# TODO: Implement utility functions
EOF

echo "🧪 Creating test files..."

# Test files
cat > "$PROJECT_DIR/tests/__init__.py" << 'EOF'
"""
Test package for diff service.
"""
EOF

cat > "$PROJECT_DIR/tests/test_diff_parser.py" << 'EOF'
"""
Tests for diff parser functionality.
"""
# TODO: Implement tests for diff parser
EOF

cat > "$PROJECT_DIR/tests/sample_data.json" << 'EOF'
{
  "comment": "Sample test data for diff service tests"
}
EOF

echo "🔧 Creating script files..."

# Script files
cat > "$PROJECT_DIR/scripts/run_dev.py" << 'EOF'
"""
Development runner for diff service.
"""
# TODO: Implement development runner script
EOF

echo "✅ Project structure created successfully!"
echo ""
echo "📂 Created structure:"
echo "diff-service/"
echo "├── README.md"
echo "├── requirements.txt"
echo "├── .env.example"
echo "├── .gitignore"
echo "├── Dockerfile"
echo "├── docker-compose.yml"
echo "├── app/"
echo "│   ├── __init__.py"
echo "│   ├── main.py"
echo "│   ├── config.py"
echo "│   ├── models.py"
echo "│   ├── github_client.py"
echo "│   ├── diff_parser.py"
echo "│   ├── webhook_handler.py"
echo "│   └── utils.py"
echo "├── tests/"
echo "│   ├── __init__.py"
echo "│   ├── test_diff_parser.py"
echo "│   └── sample_data.json"
echo "└── scripts/"
echo "    └── run_dev.py"
echo ""
echo "🎉 Ready to start development!"
echo "Next steps:"
echo "1. cd diff-service"
echo "2. Start implementing the TODO items in each file"
echo "3. Add your dependencies to requirements.txt"
echo "4. Configure your .env file based on .env.example"
EOF

# Make the script executable
chmod +x create-diff-service-structure.sh

echo "🎯 Script created: create-diff-service-structure.sh"
echo "Run with: ./create-diff-service-structure.sh"
