#!/bin/bash

# publish-test.sh - Publish tonic-fabricate to TestPyPI
# Usage: ./publish-test.sh

set -e  # Exit on any error

echo "🚀 Publishing tonic-fabricate to TestPyPI..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the clients/python directory."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade build tools
echo "📥 Installing build tools..."
pip install --upgrade pip build twine

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info fabricate_client.egg-info/

# Build the package
echo "🔨 Building package..."
python -m build

# Check if build was successful
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "❌ Error: Build failed or no files generated in dist/"
    exit 1
fi

echo "✅ Build successful! Generated files:"
ls -la dist/

# Upload to TestPyPI
echo ""
echo "📤 Uploading to TestPyPI..."
echo "📝 You will be prompted for credentials:"
echo "   Username: __token__"
echo "   Password: your-testpypi-api-token (including pypi- prefix)"
echo ""

twine upload --repository testpypi dist/*

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Successfully published to TestPyPI!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Test installation with:"
    echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tonic-fabricate"
    echo ""
    echo "2. Test the package:"
    echo "   python -c \"from fabricate_client import generate; print('Package works!')\""
    echo ""
    echo "3. View on TestPyPI:"
    echo "   https://test.pypi.org/project/tonic-fabricate/"
    echo ""
    echo "4. If everything works, use 'twine upload dist/*' to publish to production PyPI"
else
    echo "❌ Upload failed!"
    exit 1
fi
