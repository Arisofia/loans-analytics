#!/bin/bash

# Set logging for linting output
LOGFILE="linting_$(date +%Y-%m-%d_%H-%M-%S).log"

# Function to lint Python files
lint_python() {
  echo "Linting Python files..." | tee -a "$LOGFILE"
  for file in *.py; do
    if [[ -f "$file" ]]; then
      echo "Linting $file" | tee -a "$LOGFILE"
      python3 -m py_compile "$file" 2>>"$LOGFILE"
      if [ $? -ne 0 ]; then
        echo "Error linting $file" | tee -a "$LOGFILE"
      fi
    fi
  done
}

# Function to lint JS/TS/React files
lint_js() {
  echo "Linting JS/TS/React files..." | tee -a "$LOGFILE"
  npm run lint -- --fix --quiet 2>>"$LOGFILE"
  if [ $? -ne 0 ]; then
    echo "Error linting JS/TS/React files" | tee -a "$LOGFILE"
  fi
}

# Change to the directory of the script
cd "$(dirname "$0")"

# Lint files
lint_python
lint_js

echo "Linting completed. See $LOGFILE for details."
