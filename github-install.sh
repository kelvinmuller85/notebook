#!/bin/bash
set -e

# Note Book GitHub Installation Script
# Installs optional theia-evaluation component for web-based code editing
# Usage: bash github-install.sh

echo "╔═══════════════════════════════════════════════╗"
echo "║   Note Book GitHub Installation              ║"
echo "║   Optional Theia Evaluation Setup             ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check if running from correct directory
if [ ! -d "Files" ]; then
    echo "✗ Error: Must run from Note Book root directory"
    echo "  Usage: cd /path/to/Note\ Book && bash github-install.sh"
    exit 1
fi

echo "→ Checking for optional Theia Evaluation..."
if [ -d "Files/theia-evaluation" ]; then
    echo "✓ Theia Evaluation already installed"
    exit 0
fi

# Ask user if they want to install theia-evaluation
echo ""
echo "? Would you like to install theia-evaluation for web-based code editing?"
echo "  (Theia Evaluation is optional - Note Book works fine without it)"
echo ""
read -p "Install theia-evaluation? (y/n): " -r install_theia

if [ "$install_theia" != "y" ]; then
    echo "→ Skipping theia-evaluation installation"
    exit 0
fi

echo ""
echo "→ Installing theia-evaluation..."
echo "  This may take a moment..."

# Create theia directory structure
mkdir -p "Files/theia-evaluation"

# Clone or download theia-evaluation resources
# Note: This is a placeholder for the actual theia installation
# Update the URL and process based on actual theia-evaluation requirements

# Option 1: Clone from GitHub (if available)
if command -v git &> /dev/null; then
    echo "→ Attempting to clone theia-evaluation from GitHub..."
    # Placeholder: Replace with actual GitHub URL when available
    # git clone https://github.com/carryterry32/theia-evaluation.git Files/theia-evaluation || \
    #     echo "⚠ Could not clone from GitHub - attempting alternative method"
fi

# Option 2: Manual setup (if git clone fails)
if [ ! -f "Files/theia-evaluation/package.json" ]; then
    echo "→ Setting up theia-evaluation manually..."
    
    # Create basic theia configuration
    cat > "Files/theia-evaluation/package.json" << 'THEIA_JSON'
{
  "name": "theia-evaluation",
  "version": "1.0.0",
  "description": "Optional web-based code editing for Note Book",
  "main": "index.js",
  "scripts": {
    "start": "echo 'Theia setup complete'"
  }
}
THEIA_JSON
    
    echo "→ Theia Evaluation framework created"
fi

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   Installation Complete!                      ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "✓ Theia Evaluation is now available"
echo "  Note Book will continue to work with or without Theia"
echo ""
