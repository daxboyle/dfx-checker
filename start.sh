#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
if ! aws sts get-caller-identity &> /dev/null 2>&1; then
    echo ""
    echo "WARNING: AWS credentials expired or missing."
    echo "Go to isengard.amazon.com -> 286507431165 -> Temporary Credentials -> bash/zsh"
    echo ""
fi
echo "Starting DFX Design Checker..."
streamlit run DFX_Design_Checker.py
