"""
CSV File Upload Interface for ABACO Loans Analytics
Streamlit component for uploading and processing loan data files
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Import pipeline components
try:
    from python.config import load_business_rules, load_kpi_definitions
    from src.pipeline.calculation import CalculationPhase
    from src.pipeline.ingestion import IngestionPhase
    from src.pipeline.output import OutputPhase
    from src.pipeline.transformation import TransformationPhase
except ImportError:
    st.error("❌ Pipeline modules not found. Run from project root directory.")
    st.stop()


def render_csv_upload():
    """Render CSV upload interface with validation and processing."""

    st.header("📤 CSV Data Upload")
    st.markdown("""
    Upload loan data CSV files to process through the analytics pipeline.
    
    **Supported file types:** CSV, Excel (.xlsx, .xls)  
    **Max file size:** 200 MB  
    **Expected columns:** loan_id, customer_id, loan_amount, status, disbursement_date, etc.
    """)

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose CSV/Excel file(s)",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Select one or more loan data files to upload and process",
    )

    if not uploaded_files:
        st.info("👆 Upload a file to get started")
        return

    # Display uploaded files summary
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")

    for idx, uploaded_file in enumerate(uploaded_files, 1):
        with st.expander(
            f"📄 {uploaded_file.name} ({_format_file_size(uploaded_file.size)})",
            expanded=(idx == 1),
        ):
            _process_uploaded_file(uploaded_file)


def _process_uploaded_file(uploaded_file):
    """Process a single uploaded file through the pipeline."""

    try:
        # Read file into DataFrame
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:  # Excel
            df = pd.read_excel(uploaded_file)

        st.write(f"**Rows:** {len(df):,} | **Columns:** {len(df.columns)}")

        # Show preview
        st.subheader("📊 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # Show column info
        with st.expander("📋 Column Information"):
            col_info = pd.DataFrame(
                {
                    "Column": df.columns,
                    "Type": df.dtypes.astype(str),
                    "Non-Null": df.notna().sum(),
                    "Null": df.isna().sum(),
                    "Null %": (df.isna().sum() / len(df) * 100).round(2),
                }
            )
            st.dataframe(col_info, use_container_width=True)

        # Validation checks
        st.subheader("✅ Validation Checks")
        _run_validation_checks(df)

        # Process button
        if st.button(
            f"🚀 Process {uploaded_file.name}", key=f"process_{uploaded_file.name}", type="primary"
        ):
            _run_pipeline(df, uploaded_file.name)

    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")


def _run_validation_checks(df: pd.DataFrame):
    """Run validation checks on uploaded data."""

    checks = []

    # Check 1: Required columns
    required_cols = ["loan_id", "customer_id", "loan_amount", "status"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        checks.append(("❌", f"Missing required columns: {', '.join(missing_cols)}"))
    else:
        checks.append(("✅", "All required columns present"))

    # Check 2: Duplicate loan IDs
    if "loan_id" in df.columns:
        duplicates = df["loan_id"].duplicated().sum()
        if duplicates > 0:
            checks.append(("⚠️", f"Found {duplicates} duplicate loan IDs"))
        else:
            checks.append(("✅", "No duplicate loan IDs"))

    # Check 3: Null values in critical columns
    if "loan_amount" in df.columns:
        null_amounts = df["loan_amount"].isna().sum()
        if null_amounts > 0:
            checks.append(("⚠️", f"{null_amounts} loans with missing amounts"))
        else:
            checks.append(("✅", "No missing loan amounts"))

    # Check 4: Data types
    if "loan_amount" in df.columns and not pd.api.types.is_numeric_dtype(df["loan_amount"]):
        checks.append(("❌", "loan_amount is not numeric"))
    else:
        checks.append(("✅", "loan_amount has correct type"))

    # Display checks
    for icon, message in checks:
        if icon == "❌":
            st.error(f"{icon} {message}")
        elif icon == "⚠️":
            st.warning(f"{icon} {message}")
        else:
            st.success(f"{icon} {message}")


def _run_pipeline(df: pd.DataFrame, filename: str):
    """Execute the full data pipeline on uploaded data."""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Create run directory
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("logs/runs") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        input_path = run_dir / filename
        df.to_csv(input_path, index=False)

        # Phase 1: Ingestion
        status_text.text("Phase 1/4: Ingesting data...")
        progress_bar.progress(25)

        ingestion = IngestionPhase({})
        ingestion_result = ingestion.execute(input_path=input_path, run_dir=run_dir)

        if ingestion_result["status"] != "success":
            st.error(f"❌ Ingestion failed: {ingestion_result.get('error')}")
            return

        # Phase 2: Transformation
        status_text.text("Phase 2/4: Transforming data...")
        progress_bar.progress(50)

        business_rules = load_business_rules()
        transformation = TransformationPhase({}, business_rules)
        transform_result = transformation.execute(
            raw_data_path=run_dir / "raw_data.parquet", run_dir=run_dir
        )

        if transform_result["status"] != "success":
            st.error(f"❌ Transformation failed: {transform_result.get('error')}")
            return

        # Phase 3: Calculation
        status_text.text("Phase 3/4: Calculating KPIs...")
        progress_bar.progress(75)

        kpi_definitions = load_kpi_definitions()
        calculation = CalculationPhase({}, kpi_definitions)
        calc_result = calculation.execute(
            clean_data_path=run_dir / "clean_data.parquet", run_dir=run_dir
        )

        if calc_result["status"] != "success":
            st.error(f"❌ Calculation failed: {calc_result.get('error')}")
            return

        # Phase 4: Output
        status_text.text("Phase 4/4: Generating outputs...")
        progress_bar.progress(90)

        output = OutputPhase({})
        output_result = output.execute(kpi_results=calc_result["kpis"], run_dir=run_dir)

        if output_result["status"] != "success":
            st.error(f"❌ Output failed: {output_result.get('error')}")
            return

        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Pipeline completed successfully!")

        # Display results
        st.success(f"✅ Processing complete! Run ID: {run_id}")

        with st.expander("📊 Results Summary", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Rows Processed", f"{ingestion_result['row_count']:,}")
            with col2:
                st.metric("KPIs Calculated", calc_result["kpi_count"])
            with col3:
                st.metric("Data Quality", f"{transform_result.get('quality_score', 0.0):.1%}")

            st.subheader("Calculated KPIs")
            kpi_df = pd.DataFrame([calc_result["kpis"]]).T
            kpi_df.columns = ["Value"]
            st.dataframe(kpi_df, use_container_width=True)

        # Download results
        st.subheader("📥 Download Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv_path = run_dir / "kpis_output.csv"
            if csv_path.exists():
                with open(csv_path, "rb") as f:
                    st.download_button(
                        "📄 Download CSV", f, file_name=f"kpis_{run_id}.csv", mime="text/csv"
                    )

        with col2:
            json_path = run_dir / "kpis_output.json"
            if json_path.exists():
                with open(json_path, "rb") as f:
                    st.download_button(
                        "📄 Download JSON",
                        f,
                        file_name=f"kpis_{run_id}.json",
                        mime="application/json",
                    )

        with col3:
            parquet_path = run_dir / "kpis_output.parquet"
            if parquet_path.exists():
                with open(parquet_path, "rb") as f:
                    st.download_button(
                        "📄 Download Parquet",
                        f,
                        file_name=f"kpis_{run_id}.parquet",
                        mime="application/octet-stream",
                    )

    except Exception as e:
        st.error(f"❌ Pipeline execution failed: {str(e)}")
        st.exception(e)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    # For testing standalone
    st.set_page_config(page_title="CSV Upload - ABACO Analytics", page_icon="📤", layout="wide")
    render_csv_upload()
