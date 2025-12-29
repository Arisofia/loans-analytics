#!/bin/bash
set -euo pipefail

echo "=== Consolidating Transformation Module ==="

# Update transformation imports
sed -i '' 's/from python\.transformation import DataTransformation/from python.pipeline.transformation import UnifiedTransformation/g' tests/test_pipeline_integration.py
sed -i '' 's/DataTransformation/UnifiedTransformation/g' tests/test_pipeline_integration.py

sed -i '' 's/from python\.transformation import DataTransformation/from python.pipeline.transformation import UnifiedTransformation/g' tests/test_transformation.py
sed -i '' 's/DataTransformation/UnifiedTransformation/g' tests/test_transformation.py

sed -i '' 's/from python\.transformation import DataTransformation/from python.pipeline.transformation import UnifiedTransformation/g' tests/test_pipeline.py
sed -i '' 's/DataTransformation/UnifiedTransformation/g' tests/test_pipeline.py

sed -i '' 's/from python\.transformation import DataTransformation/from python.pipeline.transformation import UnifiedTransformation/g' scripts/run_data_pipeline.py
sed -i '' 's/DataTransformation/UnifiedTransformation/g' scripts/run_data_pipeline.py

echo "✓ Transformation consolidation complete"

