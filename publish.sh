#!/bin/bash

# publish.sh - Publish tonic-fabricate to production PyPI
# Usage: ./publish.sh

set -e  # Exit on any error

echo "🚀 Publishing tonic-fabricate to PRODUCTION PyPI..."
echo "⚠️  WARNING: This will publish to the live PyPI registry!"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the clients/python directory."
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📦 Current version: $CURRENT_VERSION"

# Safety check for version 0.0.0
if [ "$CURRENT_VERSION" = "0.0.0" ]; then
    echo "⚠️  WARNING: You're about to publish version 0.0.0!"
    echo "   This is typically a development version."
    echo "   Consider updating to a proper version (e.g., 1.0.0) before publishing."
    echo ""
    read -p "Do you want to continue with version 0.0.0? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled. Please update the version in pyproject.toml and fabricate_client/__init__.py"
        exit 1
    fi
fi

# Confirmation prompt
echo ""
echo "🔍 Pre-flight checklist:"
echo "   ✅ Version: $CURRENT_VERSION"
echo "   ✅ Target: Production PyPI (https://pypi.org/)"
echo "   ✅ Package: tonic-fabricate"
echo ""
echo "⚠️  IMPORTANT: Once published, you CANNOT:"
echo "   - Delete or modify this version"
echo "   - Re-upload the same version number"
echo ""
read -p "Are you sure you want to publish to PRODUCTION PyPI? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled. Use ./publish-test.sh for testing first."
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

# Verify package integrity
echo "🔍 Checking package integrity..."
twine check dist/*

if [ $? -ne 0 ]; then
    echo "❌ Package integrity check failed!"
    exit 1
fi

# Final confirmation
echo ""
echo "🚨 FINAL CONFIRMATION 🚨"
echo "You are about to publish tonic-fabricate v$CURRENT_VERSION to PRODUCTION PyPI"
echo ""
read -p "Type 'PUBLISH' to confirm: " CONFIRM

if [ "$CONFIRM" != "PUBLISH" ]; then
    echo "❌ Cancelled. Confirmation not received."
    exit 1
fi

# Upload to production PyPI
echo ""
echo "📤 Uploading to PRODUCTION PyPI..."
echo "📝 You will be prompted for credentials:"
echo "   Username: __token__"
echo "   Password: your-pypi-api-token (including pypi- prefix)"
echo ""

twine upload dist/*

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Successfully published to PRODUCTION PyPI!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Test installation with:"
    echo "   pip install tonic-fabricate"
    echo ""
    echo "2. Test the package:"
    echo "   python -c \"from fabricate_client import generate; print('Package works!')\""
    echo ""
    echo "3. View on PyPI:"
    echo "   https://pypi.org/project/tonic-fabricate/"
    echo ""
    echo "4. Update documentation and announce the release!"
    echo ""
    echo "🔖 Remember to tag this release in git:"
    echo "   git tag v$CURRENT_VERSION"
    echo "   git push origin v$CURRENT_VERSION"
else
    echo "❌ Upload failed!"
    exit 1
fi

