#!/bin/bash
# Clean environment script to avoid zsh dump_zsh_state error

# Set up clean environment
export SHELL=/bin/bash
export TERM=xterm-256color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to project directory (parent of amazon folder)
cd "$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
source venv/bin/activate

# Change to amazon directory for running amazon scripts
cd amazon

# Run the command passed as argument
if [ "$1" = "pip" ]; then
    exec pip3 "${@:2}"
else
    exec "$@"
fi
