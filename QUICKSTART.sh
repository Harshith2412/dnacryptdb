#!/bin/bash
# DNACryptDB - Quick Start Setup Script

echo "=========================================================================="
echo "                    DNACryptDB - Quick Start Setup"
echo "=========================================================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found: Python $python_version"

# Check MySQL
echo ""
echo "[2/6] Checking MySQL..."
if command -v mysql &> /dev/null; then
    mysql_version=$(mysql --version | awk '{print $5}' | sed 's/,$//')
    echo "  ✓ MySQL found: $mysql_version"
else
    echo "  ✗ MySQL not found. Please install MySQL first."
    exit 1
fi

# Check MongoDB
echo ""
echo "[3/6] Checking MongoDB..."
if command -v mongod &> /dev/null; then
    mongo_version=$(mongod --version | head -1 | awk '{print $3}')
    echo "  ✓ MongoDB found: $mongo_version"
else
    echo "  ✗ MongoDB not found. Please install MongoDB first."
    exit 1
fi

# Install Python package
echo ""
echo "[4/6] Installing DNACryptDB..."
pip install -e . --quiet
if [ $? -eq 0 ]; then
    echo "  ✓ DNACryptDB installed successfully"
else
    echo "  ✗ Installation failed"
    exit 1
fi

# Verify installation
echo ""
echo "[5/6] Verifying installation..."
if command -v dnacryptdb &> /dev/null; then
    echo "  ✓ dnacryptdb command available"
else
    echo "  ✗ dnacryptdb command not found"
    exit 1
fi

# Initialize configuration
echo ""
echo "[6/6] Initialize configuration..."
echo ""
echo "Please enter your database credentials:"
echo ""

dnacryptdb init

echo ""
echo "=========================================================================="
echo "                         Setup Complete! 🎉"
echo "=========================================================================="
echo ""
echo "Next steps:"
echo "  1. Test with example: dnacryptdb run examples/example.dnacdb"
echo "  2. Try interactive mode: dnacryptdb interactive"
echo "  3. Read the README.md for more information"
echo ""
echo "=========================================================================="