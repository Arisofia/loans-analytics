#!/bin/bash
# Rename Python files to snake_case in python/ and apps/analytics/
find python/ apps/analytics/ -type f -name "*.py" | while read file; do
    newname=$(echo "$file" | sed -E 's/([a-z0-9])([A-Z])/_\1\L\2/g')
    if [ "$file" != "$newname" ]; then
        git mv "$file" "$newname"
    fi
done
git commit -m "Unify Python file naming to snake_case"
git push origin main
