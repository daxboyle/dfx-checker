#!/bin/bash
echo "================================"
echo "  DFX Design Checker - Setup"
echo "================================"
echo ""
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi
echo "Python 3 found: $(python3 --version)"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "Installing dependencies..."
pip install -q ezdxf streamlit matplotlib fpdf2 boto3 Pillow PyMuPDF requests
pip install -q cadquery 2>/dev/null && echo "cadquery installed" || echo "cadquery not available (STEP files wont work)"
mkdir -p reference_images ci_uploads
echo ""
echo "Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "AWS credentials active"
else
    echo "WARNING: No AWS credentials. AI features need credentials."
    echo "Go to isengard.amazon.com -> 286507431165 -> Temporary Credentials -> bash/zsh"
fi
echo ""
echo "Setup complete! Run ./start.sh to launch."
