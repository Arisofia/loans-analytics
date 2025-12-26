#!/bin/bash
set -euo pipefail

echo "=== CONSOLIDATION: Legacy Module Cleanup ==="
echo ""

# Step 1: Update imports in test files
echo "Step 1: Updating imports to use python.pipeline.ingestion..."

# tests/test_pipeline_integration.py
sed -i '' 's/from python\.ingestion import CascadeIngestion/from python.pipeline.ingestion import UnifiedIngestion/g' tests/test_pipeline_integration.py
sed -i '' 's/CascadeIngestion/UnifiedIngestion/g' tests/test_pipeline_integration.py

# tests/test_ingestion.py  
sed -i '' 's/from python\.ingestion import CascadeIngestion/from python.pipeline.ingestion import UnifiedIngestion/g' tests/test_ingestion.py
sed -i '' 's/CascadeIngestion/UnifiedIngestion/g' tests/test_ingestion.py

# tests/test_pipeline.py
sed -i '' 's/from python\.ingestion import CascadeIngestion/from python.pipeline.ingestion import UnifiedIngestion/g' tests/test_pipeline.py
sed -i '' 's/CascadeIngestion/UnifiedIngestion/g' tests/test_pipeline.py

# scripts/run_data_pipeline.py
sed -i '' 's/from python\.ingestion import CascadeIngestion/from python.pipeline.ingestion import UnifiedIngestion/g' scripts/run_data_pipeline.py
sed -i '' 's/CascadeIngestion/UnifiedIngestion/g' scripts/run_data_pipeline.py

echo "✓ Import updates complete"
echo ""

# Step 2: Check for transformation imports
echo "Step 2: Checking for transformation imports..."
grep -r "from python.transformation import\|from python import transformation" --include="*.py" --exclude-dir=.venv --exclude-dir=node_modules 2>/dev/null || echo "No imports found"
echo ""

# Step 3: Delete legacy modules
echo "Step 3: Deleting legacy modules..."
rm -f python/ingestion.py && echo "✓ Deleted python/ingestion.py"
rm -f python/transformation.py && echo "✓ Deleted python/transformation.py"
rm -f python/pipeline/calculation.py && echo "✓ Deleted python/pipeline/calculation.py"

# Rename calculation_v2 to calculation
mv python/pipeline/calculation_v2.py python/pipeline/calculation.py && echo "✓ Renamed calculation_v2.py → calculation.py"

echo ""
echo "=== CONSOLIDATION COMPLETE ==="
echo "Next: Run tests to validate changes"

