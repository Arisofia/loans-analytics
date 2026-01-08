# CI Workflow Failure Diagnosis Report

**Generated**: Wed Jan 7 03:08:52 CET 2026
**Repository**: /Users/jenineferderas/Documents/abaco-loans-analytics

## 1. ENVIRONMENT CHECK

### Python Version

Python 3.9.6

### Critical Dependencies

✓ pandas 2.3.3
✓ pytest 8.4.2
✗ mypy MISSING

## 2. WORKFLOW SYNTAX CHECK

### YAML Validation

✗ ci.yml: INVALID

## 3. TEST EXECUTION

### Running Tests...

/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/**init**.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
warnings.warn(
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: /Users/jenineferderas/Documents/abaco-loans-analytics
configfile: pytest.ini
plugins: mock-3.15.1, anyio-4.12.0, hypothesis-6.141.1, timeout-2.4.0, typeguard-4.4.4, Faker-37.12.0, requests-mock-1.12.1, cov-7.0.0
collecting ... collected 380 items / 3 skipped

tests/data_tests/test_kpi_contracts.py::test_par_90_from_sample_data PASSED [ 0%]
tests/data_tests/test_kpi_contracts.py::test_collection_rate_calculation PASSED [ 0%]
tests/data_tests/test_kpi_contracts.py::test_segment_level_contracts PASSED [ 0%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_normality PASSED [ 1%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_heteroscedasticity PASSED [ 1%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_multicollinearity PASSED [ 1%]
tests/data_tests/test_kpi_stat_advanced.py::test_par_90_is_weighted_by_segment PASSED [ 1%]
tests/data_tests/test_kpi_stat_advanced.py::test_collection_rate_remains_above_thresholds PASSED [ 2%]
tests/data_tests/test_kpi_stat_advanced.py::test_no_missing_segments_or_dates PASSED [ 2%]
tests/data_tests/test_kpi_stat_extra.py::test_kpi_chi2_contingency PASSED [ 2%]
tests/data_tests/test_kpi_stat_extra.py::test_kpi_mannwhitney PASSED [ 2%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_classification_metrics PASSED [ 3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_threshold_validation SKIPPED [ 3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_financial_metrics_structure SKIPPED [ 3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_model_stability_metrics SKIPPED [ 3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_fairness_compliance_metrics SKIPPED [ 4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_business_kpis_structure SKIPPED [ 4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[accuracy-expected_range0] PASSED [ 4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[precision-expected_range1] PASSED [ 5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[recall-expected_range2] PASSED [ 5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[f1_score-expected_range3] PASSED [ 5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[roc_auc-expected_range4] PASSED [ 5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_evaluation_pipeline_integration PASSED [ 6%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_config_file_exists PASSED [ 6%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_config_yaml_valid SKIPPED [ 6%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_threshold_values_reasonable SKIPPED [ 6%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_c01_figma_sync_success PASSED [ 7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_d01_otlp_span_generation PASSED [ 7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_f01_secret_masking PASSED [ 7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_c04_notion_timeout_simulation PASSED [ 7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_f02_unauthorized_access PASSED [ 8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b01_kpi_baseline_match PASSED [ 8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b01_no_nan_or_inf_values PASSED [ 8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_null_and_zero_handling PASSED [ 8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_division_by_zero_safety PASSED [ 9%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_negative_value_handling PASSED [ 9%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_large_value_handling PASSED [ 9%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_b03_performance_sla PASSED [ 10%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_g01_idempotency PASSED [ 10%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_e01_retry_placeholder PASSED [ 10%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_i01_e2e_acceptance PASSED [ 10%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a01_pipeline_smoke_execution PASSED [ 11%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_artifact_existence_and_schema PASSED [ 11%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_json_required_fields PASSED [ 11%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_csv_valid_structure PASSED [ 11%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_unit_test_execution SKIPPED [ 12%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_coverage_threshold SKIPPED [ 12%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_no_import_errors PASSED [ 12%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_regression_baseline PASSED [ 12%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_mypy_validation_smoke PASSED [ 13%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_module_type_hints_present PASSED [ 13%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_docstrings_present PASSED [ 13%]
tests/integration/test_figma_sync_requests_mock.py::test_figma_sync_with_requests_mock PASSED [ 13%]
tests/integration/test_figma_sync_requests_mock.py::test_figma_sync_handles_rate_limit PASSED [ 14%]
tests/test_analytics_metrics.py::test_standardize_numeric_handles_symbols PASSED [ 14%]
tests/test_analytics_metrics.py::test_standardize_numeric_passes_through_numeric_series PASSED [ 14%]
tests/test_analytics_metrics.py::test_standardize_numeric_handles_negative_symbols_and_commas PASSED [ 15%]
tests/test_analytics_metrics.py::test_project_growth_requires_minimum_periods PASSED [ 15%]
tests/test_analytics_metrics.py::test_project_growth_builds_monotonic_path PASSED [ 15%]
tests/test_analytics_metrics.py::test_project_growth_uses_default_periods PASSED [ 15%]
tests/test_analytics_metrics.py::test_project_growth_supports_decreasing_targets PASSED [ 16%]
tests/test_analytics_metrics.py::test_calculate_quality_score_handles_empty_df PASSED [ 16%]
tests/test_analytics_metrics.py::test_calculate_quality_score_rewards_complete_data PASSED [ 16%]
tests/test_analytics_metrics.py::test_calculate_quality_score_counts_completeness PASSED [ 16%]
tests/test_analytics_metrics.py::test_portfolio_kpis_returns_expected_metrics PASSED [ 17%]
tests/test_analytics_metrics.py::test_portfolio_kpis_missing_column_raises PASSED [ 17%]
tests/test_analytics_metrics.py::test_portfolio_kpis_handles_empty_frame PASSED [ 17%]
tests/test_analytics_metrics.py::test_portfolio_kpis_zero_principal_yield_is_zero PASSED [ 17%]
tests/test_analytics_metrics.py::test_portfolio_kpis_dti_nan_when_income_non_positive PASSED [ 18%]
tests/test_analytics_metrics.py::test_portfolio_kpis_ltv_nan_when_appraisal_non_positive PASSED [ 18%]
tests/test_api_kpis.py::test_get_latest_kpis PASSED [ 18%]
tests/test_aum_growth.py::test_calculate_growth_positive PASSED [ 18%]
tests/test_aum_growth.py::test_calculate_growth_negative PASSED [ 19%]
tests/test_aum_growth.py::test_calculate_growth_zero_previous PASSED [ 19%]
tests/test_azure_blob_exporter.py::test_upload_metrics_uses_blob_service_client PASSED [ 19%]
tests/test_azure_blob_exporter.py::test_upload_metrics_requires_payload PASSED [ 20%]
tests/test_azure_blob_exporter.py::test_upload_metrics_rejects_non_numeric_payloads PASSED [ 20%]
tests/test_azure_blob_exporter.py::test_upload_metrics_rejects_non_string_blob_name PASSED [ 20%]
tests/test_azure_blob_exporter.py::test_exporter_requires_valid_container_name PASSED [ 20%]
tests/test_azure_blob_exporter.py::test_engine_exports_to_blob PASSED [ 21%]
tests/test_azure_blob_exporter.py::test_engine_rejects_non_string_blob_name PASSED [ 21%]
tests/test_azure_blob_exporter_extended.py::test_exporter_requires_non_empty_container PASSED [ 21%]
tests/test_azure_blob_exporter_extended.py::test_exporter_requires_connection_or_url PASSED [ 21%]
tests/test_azure_blob_exporter_extended.py::test_exporter_initialization_with_connection_string PASSED [ 22%]
tests/test_azure_blob_exporter_extended.py::test_exporter_initialization_with_account_url PASSED [ 22%]
tests/test_azure_blob_exporter_extended.py::test_exporter_uses_provided_blob_service_client PASSED [ 22%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_requires_dict PASSED [ 22%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_requires_non_empty_dict PASSED [ 23%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_blob_name_must_be_string PASSED [ 23%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_keys_must_be_strings PASSED [ 23%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_values_must_be_numeric PASSED [ 23%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_rejects_boolean_values PASSED [ 24%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_rejects_empty_key PASSED [ 24%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_successful_upload PASSED [ 24%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_creates_blob_path_with_timestamp PASSED [ 25%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_handles_container_already_exists PASSED [ 25%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_payload_structure PASSED [ 25%]
tests/test_azure_blob_exporter_extended.py::test_upload_metrics_int_values_converted_to_float PASSED [ 25%]
tests/test_azure_blob_exporter_extended.py::test_container_name_whitespace_stripped PASSED [ 26%]
tests/test_clients.py::TestGrokClient::test_generate_text_calls_api PASSED [ 26%]
tests/test_clients.py::TestGrokClient::test_generate_text_raises_without_api_key PASSED [ 26%]
tests/test_clients.py::TestGrokClient::test_init_defaults PASSED [ 26%]
tests/test_clients.py::TestGrokClient::test_session_configuration PASSED [ 27%]
tests/test_clients.py::TestGeminiClient::test_generate_text_calls_model PASSED [ 27%]
tests/test_clients.py::TestGeminiClient::test_init_configures_genai PASSED [ 27%]
tests/test_clients.py::TestGeminiClient::test_init_raises_without_api_key PASSED [ 27%]
tests/test_collection_rate.py::test_calculate_collection_rate_standard PASSED [ 28%]
tests/test_collection_rate.py::test_calculate_collection_rate_zero_eligible PASSED [ 28%]
tests/test_collection_rate.py::test_calculate_collection_rate_missing_columns PASSED [ 28%]
tests/test_collection_rate.py::test_calculate_collection_rate_empty_df PASSED [ 28%]
tests/test_compliance.py::test_mask_pii_columns_by_keywords PASSED [ 29%]
tests/test_compliance.py::test_mask_pii_columns_override PASSED [ 29%]
tests/test_compliance.py::test_access_log_entry_contains_context PASSED [ 29%]
tests/test_compliance.py::test_build_compliance_report_includes_metadata PASSED [ 30%]
tests/test_dashboard_utils.py::test_compute_cat_agg_missing_value_col PASSED [ 30%]
tests/test_dashboard_utils.py::test_compute_cat_agg_with_values PASSED [ 30%]
tests/test_dataframe_assertions.py::test_assert_dataframe_schema_detects_missing_columns PASSED [ 30%]
tests/test_dataframe_assertions.py::test_assert_dataframe_schema_detects_non_numeric_columns PASSED [ 31%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_runs PASSED [ 31%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_skips_plots_if_columns_missing PASSED [ 31%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_with_file PASSED [ 31%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_kpi_calculation_produces_valid_output PASSED [ 32%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_metrics_csv_generation PASSED [ 32%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_main_pipeline_success PASSED [ 32%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_empty_dataset_handling PASSED [ 32%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_missing_dataset_error PASSED [ 33%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_kpi_value_ranges PASSED [ 33%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_segment_analysis PASSED [ 33%]
tests/test_enterprise_analytics_engine.py::test_initialization_requires_data PASSED [ 33%]
tests/test_enterprise_analytics_engine.py::test_validates_missing_columns PASSED [ 34%]
tests/test_enterprise_analytics_engine.py::test_ltv_handles_zero_appraised_value PASSED [ 34%]
tests/test_enterprise_analytics_engine.py::test_dti_returns_series_with_index PASSED [ 34%]
tests/test_enterprise_analytics_engine.py::test_risk_alerts_surface_high_risk_loans PASSED [ 35%]
tests/test_enterprise_analytics_engine.py::test_run_full_analysis_includes_quality PASSED [ 35%]
tests/test_enterprise_analytics_engine.py::test_coerces_invalid_numeric_values_and_reports_quality PASSED [ 35%]
tests/test_enterprise_analytics_engine.py::test_source_dataframe_remains_unchanged_after_analysis PASSED [ 35%]
tests/test_enterprise_analytics_engine.py::test_compute_delinquency_rate PASSED [ 36%]
tests/test_enterprise_analytics_engine.py::test_compute_portfolio_yield PASSED [ 36%]
tests/test_enterprise_analytics_engine.py::test_dti_excludes_nan_from_average PASSED [ 36%]
tests/test_enterprise_analytics_engine.py::test_check_data_sanity_warns_on_high_interest_rate PASSED [ 36%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_from_dict PASSED [ 37%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_coercion_report_tracking PASSED [ 37%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_empty_dataframe PASSED [ 37%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_non_dataframe_input PASSED [ 37%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_ltv_with_infinity PASSED [ 38%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_dti_with_negative_income PASSED [ 38%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_with_duplicates PASSED [ 38%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_with_null_values PASSED [ 38%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_score_calculation PASSED [ 39%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_empty_result PASSED [ 39%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_risk_score_calculation PASSED [ 39%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_with_nan_values PASSED [ 40%]
tests/test_enterprise_analytics_engine_extended.py::test_export_kpis_to_blob_invalid_blob_name_type PASSED [ 40%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_export_kpis_to_blob_valid PASSED [ 40%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_source_df_not_modified PASSED [ 40%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_coercion_preserves_all_nan_columns PASSED [ 41%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_run_full_analysis_returns_all_keys PASSED [ 41%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_handles_all_nan_numeric_columns FAILED [ 41%]
tests/test_export_scripts.py::TestExportScripts::test_export_copilot_slide_payload PASSED [ 41%]
tests/test_feedback_and_tracing.py::test_feedback_store_skips_malformed_files PASSED [ 42%]
tests/test_feedback_and_tracing.py::test_trace_analytics_job_wraps_and_logs PASSED [ 42%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_hhi PASSED [ 42%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_hhi_fuzzy PASSED [ 42%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_line_utilization PASSED [ 43%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_weighted_stats PASSED [ 43%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_client_type PASSED [ 43%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_dpd_buckets PASSED [ 43%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_dpd_buckets_fuzzy PASSED [ 44%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_enrich_master_dataframe PASSED [ 44%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_segment_clients_by_exposure PASSED [ 44%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_segment_clients_by_exposure_fuzzy PASSED [ 45%]
tests/test_generate_markdown_report.py::TestGenerateMarkdownReport::test_generate_report_creates_file PASSED [ 45%]
tests/test_generate_markdown_report.py::TestGenerateMarkdownReport::test_generate_report_handles_missing_files PASSED [ 45%]
tests/test_ingestion.py::test_ingest_csv PASSED [ 45%]
tests/test_ingestion.py::test_ingest_csv_error PASSED [ 46%]
tests/test_ingestion.py::test_ingest_csv_empty_file PASSED [ 46%]
tests/test_ingestion.py::test_ingest_csv_strict_schema_failure PASSED [ 46%]
tests/test_ingestion.py::test_ingest_csv_success PASSED [ 46%]
tests/test_ingestion.py::test_ingest_http PASSED [ 47%]
tests/test_ingestion.py::test_run_id_generation PASSED [ 47%]
tests/test_ingestion.py::test_audit_log_creation PASSED [ 47%]
tests/test_ingestion.py::test_looker_par_balances_to_loan_tape PASSED [ 47%]
tests/test_ingestion.py::test_looker_dpd_to_loan_tape PASSED [ 48%]
tests/test_ingestion.py::test_ingest_looker_with_par_balances PASSED [ 48%]
tests/test_ingestion.py::test_ingest_looker_with_dpd_data PASSED [ 48%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_valid PASSED [ 48%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_with_nulls PASSED [ 49%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_with_custom_fill PASSED [ 49%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_coercion PASSED [ 49%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_basic PASSED [ 50%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_with_nulls PASSED [ 50%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_with_extra PASSED [ 50%]
tests/test_kpi_base.py::TestKPIMetadata::test_metadata_creation PASSED [ 50%]
tests/test_kpi_base.py::TestKPIMetadata::test_metadata_to_dict PASSED [ 51%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_valid_calculation PASSED [ 51%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_zero_receivable PASSED [ 51%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_empty_dataframe PASSED [ 51%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_missing_columns PASSED [ 52%]
tests/test_kpi_calculators_v2.py::TestPAR90Calculator::test_par90_valid_calculation PASSED [ 52%]
tests/test_kpi_calculators_v2.py::TestPAR90Calculator::test_par90_zero_receivable PASSED [ 52%]
tests/test_kpi_calculators_v2.py::TestCollectionRateCalculator::test_collection_rate_valid PASSED [ 52%]
tests/test_kpi_calculators_v2.py::TestCollectionRateCalculator::test_collection_rate_with_nulls PASSED [ 53%]
tests/test_kpi_calculators_v2.py::TestPortfolioHealthCalculator::test_portfolio_health_valid PASSED [ 53%]
tests/test_kpi_calculators_v2.py::TestPortfolioHealthCalculator::test_portfolio_health_bounds PASSED [ 53%]
tests/test_kpi_edge_cases.py::test_empty_dataset PASSED [ 53%]
tests/test_kpi_edge_cases.py::test_single_value_dataset PASSED [ 54%]
tests/test_kpi_edge_cases.py::test_mannwhitneyu_identical PASSED [ 54%]
tests/test_kpi_edge_cases.py::test_chi2_contingency_perfect PASSED [ 54%]
tests/test_kpi_engine.py::test_calculate_par_30 PASSED [ 55%]
tests/test_kpi_engine.py::test_calculate_par_90 PASSED [ 55%]
tests/test_kpi_engine.py::test_calculate_collection_rate PASSED [ 55%]
tests/test_kpi_engine.py::test_calculate_all PASSED [ 55%]
tests/test_kpi_engine.py::test_get_audit_trail PASSED [ 56%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_kpi_engine_initialization PASSED [ 56%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_calculate_all PASSED [ 56%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_individual_calculations PASSED [ 56%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_audit_trail PASSED [ 57%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_empty_dataframe PASSED [ 57%]
tests/test_kpis_integration.py::test_par_and_aum_growth_integration PASSED [ 57%]
tests/test_manifest_segmentation.py::test_manifest_contains_segmentation_data PASSED [ 57%]
tests/test_metrics_utils.py::TestMetricsUtils::test_engine_uses_metric_utilities PASSED [ 58%]
tests/test_metrics_utils.py::TestMetricsUtils::test_kpis_match_expected_values PASSED [ 58%]
tests/test_metrics_utils.py::TestMetricsUtils::test_metric_helpers_handle_edge_cases PASSED [ 58%]
tests/test_metrics_utils.py::TestMetricsUtils::test_numeric_coercion_and_defaults PASSED [ 58%]
tests/test_metrics_utils_extended.py::test_coerce_numeric_all_nan PASSED [ 59%]
tests/test_metrics_utils_extended.py::test_validate_kpi_columns_empty_dataframe PASSED [ 59%]
tests/test_metrics_utils_extended.py::test_validate_kpi_columns_missing_multiple PASSED [ 59%]
tests/test_metrics_utils_extended.py::test_loan_to_value_all_zeros PASSED [ 60%]
tests/test_metrics_utils_extended.py::test_portfolio_delinquency_rate_no_delinquent PASSED [ 60%]
tests/test_metrics_utils_extended.py::test_portfolio_delinquency_rate_all_delinquent PASSED [ 60%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_zero_principal PASSED [ 60%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_nan_values PASSED [ 61%]
tests/test_metrics_utils_extended.py::test_portfolio_kpis_with_precalculated_ratios PASSED [ 61%]
tests/test_metrics_utils_extended.py::test_portfolio_kpis_handles_nan_in_ratios PASSED [ 61%]
tests/test_metrics_utils_extended.py::test_coerce_numeric_mixed_valid_invalid PASSED [ 61%]
tests/test_metrics_utils_extended.py::test_loan_to_value_with_negative_values PASSED [ 62%]
tests/test_metrics_utils_extended.py::test_debt_to_income_ratio_negative_income PASSED [ 62%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_string_conversion PASSED [ 62%]
tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json PASSED [ 62%]
tests/test_metrics_validation.py::test_load_dashboard_metrics_invalid_json PASSED [ 63%]
tests/test_output_triggers.py::test_dashboard_trigger_on_persist PASSED [ 63%]
tests/test_par_30.py::test_calculate_par_30_standard PASSED [ 63%]
tests/test_par_30.py::test_calculate_par_30_zero_receivable PASSED [ 63%]
tests/test_par_30.py::test_calculate_par_30_missing_columns PASSED [ 64%]
tests/test_par_30.py::test_calculate_par_30_empty_df PASSED [ 64%]
tests/test_par_90.py::test_calculate_par_90_standard PASSED [ 64%]
tests/test_par_90.py::test_calculate_par_90_zero_receivable PASSED [ 65%]
tests/test_par_90.py::test_calculate_par_90_missing_columns PASSED [ 65%]
tests/test_par_90.py::test_calculate_par_90_empty_df PASSED [ 65%]
tests/test_paths.py::TestProjectRoot::test_get_project_root_exists PASSED [ 65%]
tests/test_paths.py::TestProjectRoot::test_project_root_contains_config PASSED [ 66%]
tests/test_paths.py::TestResolvePath::test_resolve_absolute_path PASSED [ 66%]
tests/test_paths.py::TestResolvePath::test_resolve_home_relative_path PASSED [ 66%]
tests/test_paths.py::TestResolvePath::test_resolve_with_environment_variable_precedence PASSED [ 66%]
tests/test_paths.py::TestResolvePath::test_resolve_creates_directories_when_requested PASSED [ 67%]
tests/test_paths.py::TestResolvePath::test_resolve_does_not_create_by_default PASSED [ 67%]
tests/test_paths.py::TestResolvePath::test_resolve_empty_path_raises_error PASSED [ 67%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_default PASSED [ 67%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_respects_env_var PASSED [ 68%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_respects_data_metrics_path_var PASSED [ 68%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_creates_when_requested PASSED [ 68%]
tests/test_paths.py::TestPathsLogsDir::test_logs_dir_default PASSED [ 68%]
tests/test_paths.py::TestPathsLogsDir::test_logs_dir_respects_env_var PASSED [ 69%]
tests/test_paths.py::TestPathsMonitoringLogsDir::test_monitoring_logs_dir_under_logs PASSED [ 69%]
tests/test_paths.py::TestPathsMonitoringLogsDir::test_monitoring_logs_dir_creates_nested_structure PASSED [ 69%]
tests/test_paths.py::TestPathsEnvironment::test_get_environment_defaults_to_development PASSED [ 70%]
tests/test_paths.py::TestPathsEnvironment::test_get_environment_respects_python_env PASSED [ 70%]
tests/test_pipeline.py::test_ingest_data PASSED [ 70%]
tests/test_pipeline.py::test_transform_data PASSED [ 70%]
tests/test_pipeline.py::test_pipeline_ingestion_and_transformation PASSED [ 71%]
tests/test_pipeline.py::test_ingest_with_custom_run_id PASSED [ 71%]
tests/test_pipeline_integration.py::test_pipeline_with_valid_data PASSED [ 71%]
tests/test_pipeline_integration.py::test_pipeline_ingestion_with_invalid_numeric_column PASSED [ 71%]
tests/test_pipeline_integration.py::test_pipeline_transformation_with_valid_columns PASSED [ 72%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_defaults PASSED [ 72%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_validation PASSED [ 72%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_get_method PASSED [ 72%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_initialization PASSED [ 73%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_execute PASSED [ 73%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_execute_with_looker_source PASSED [ 73%]
tests/test_pr_status.py::TestPRStatus::test_list_open_prs PASSED [ 73%]
tests/test_pr_status.py::TestPRStatus::test_render_report_auth_failure PASSED [ 74%]
tests/test_pr_status.py::TestPRStatus::test_render_report_success PASSED [ 74%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_0_empty_repo PASSED [ 74%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_1_readme_only PASSED [ 75%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_2_basic_structure PASSED [ 75%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_3_docs_and_workflows PASSED [ 75%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_4_full_maturity PASSED [ 75%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_failure PASSED [ 76%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_success PASSED [ 76%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_with_custom_config PASSED [ 76%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_with_error PASSED [ 76%]
tests/test_run_scoring.py::test_parse_args_minimal_required PASSED [ 77%]
tests/test_run_scoring.py::test_parse_args_all_options PASSED [ 77%]
tests/test_run_scoring.py::test_parse_args_requires_data PASSED [ 77%]
tests/test_run_scoring.py::test_load_portfolio_file_exists PASSED [ 77%]
tests/test_run_scoring.py::test_load_portfolio_file_not_found PASSED [ 78%]
tests/test_run_scoring.py::test_load_portfolio_expands_user_path PASSED [ 78%]
tests/test_run_scoring.py::test_summarize_results_prints_output PASSED [ 78%]
tests/test_run_scoring.py::test_summarize_results_formats_numbers PASSED [ 78%]
tests/test_run_scoring.py::test_summarize_results_handles_strings PASSED [ 79%]
tests/test_run_scoring.py::test_main_full_flow_no_export PASSED [ 79%]
tests/test_run_scoring.py::test_main_output_to_file PASSED [ 79%]
tests/test_run_scoring.py::test_main_blob_export_requires_credentials PASSED [ 80%]
tests/test_run_scoring.py::test_main_blob_export_with_connection_string PASSED [ 80%]
tests/test_run_scoring.py::test_main_parses_custom_thresholds PASSED [ 80%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_existing_secret PASSED [ 80%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_nonexistent_secret_returns_none PASSED [ 81%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_required_missing_secret_raises_error PASSED [ 81%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_with_default_value PASSED [ 81%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_required_only_missing PASSED [ 81%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_with_all_required_set PASSED [ 82%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_raises_on_missing_required PASSED [ 82%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_optional_keys PASSED [ 82%]
tests/test_secrets_manager.py::TestSecretsManagerGetAll::test_get_all_required_only PASSED [ 82%]
tests/test_secrets_manager.py::TestSecretsManagerGetAll::test_get_all_includes_optional PASSED [ 83%]
tests/test_secrets_manager.py::TestSecretsManagerFactory::test_get_secrets_manager_default PASSED [ 83%]
tests/test_secrets_manager.py::TestSecretsManagerFactory::test_get_secrets_manager_with_vault PASSED [ 83%]
tests/test_secrets_manager.py::TestSecretsManagerLogging::test_log_status_does_not_expose_values PASSED [ 83%]
tests/test_segmentation_summary.py::test_segmentation_summary_calculation PASSED [ 84%]
tests/test_segmentation_summary.py::test_segmentation_summary_empty PASSED [ 84%]
tests/test_standalone_ai.py::TestStandaloneAI::test_generate_response_offline PASSED [ 84%]
tests/test_standalone_ai.py::TestStandaloneAI::test_generate_response_online PASSED [ 85%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_routes_large_payload_to_gemini PASSED [ 85%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_routes_small_payload_to_grok PASSED [ 85%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_truncates_oversized_payload PASSED [ 85%]
tests/test_sync_kpi_table_to_figma.py::test_sync_success PASSED [ 86%]
tests/test_sync_kpi_table_to_figma.py::test_page_not_found PASSED [ 86%]
tests/test_sync_kpi_table_to_figma.py::test_get_request_failure PASSED [ 86%]
tests/test_sync_kpi_table_to_figma.py::test_put_request_failure PASSED [ 86%]
tests/test_tracing_setup.py::TestTracingSetup::test_enable_auto_instrumentation_does_not_raise PASSED [ 87%]
tests/test_tracing_setup.py::TestTracingSetup::test_get_tracer_returns_tracer PASSED [ 87%]
tests/test_tracing_setup.py::TestTracingSetup::test_init_tracing_returns_provider PASSED [ 87%]
tests/test_tracing_setup.py::TestTracingSetup::test_init_tracing_uses_env_endpoint PASSED [ 87%]
tests/test_transformation.py::test_transform_basic PASSED [ 88%]
tests/test_transformation.py::test_transform_adds_tracking_columns PASSED [ 88%]
tests/test_transformation.py::test_transform_normalization PASSED [ 88%]
tests/test_transformation.py::test_transform_preserves_row_count PASSED [ 88%]
tests/test_transformation.py::test_transform_generates_lineage PASSED [ 89%]
tests/test_transformation.py::test_transform_quality_checks PASSED [ 89%]
tests/test_transformation.py::test_run_id_generation PASSED [ 89%]
tests/test_transformation.py::test_custom_run_id PASSED [ 90%]
tests/test_transformation.py::test_transform_with_null_values PASSED [ 90%]
tests/test_transformation.py::test_transform_error_handling PASSED [ 90%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_ensure_token PASSED [ 90%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_ensure_token_missing PASSED [ 91%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_fetch_workflows PASSED [ 91%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_fetch_workflows_error PASSED [ 91%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_resolve_workflow_targets PASSED [ 91%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_trigger_workflow_failure PASSED [ 92%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_trigger_workflow_success PASSED [ 92%]
tests/test_update_playwright.py::test_update_playwright_invokes_gh_api_and_writes_fixed_file PASSED [ 92%]
tests/test_update_playwright_idempotency.py::test_safe_replace_on_key_is_idempotent PASSED [ 92%]
tests/test_update_playwright_idempotency.py::test_fix_content_returns_replacements_count PASSED [ 93%]
tests/test_update_playwright_integration.py::test_integration_replaces_only_top_level_key_and_invokes_gh PASSED [ 93%]
tests/test_update_playwright_integration.py::test_integration_no_top_level_change_does_not_call_gh PASSED [ 93%]
tests/test_update_playwright_safe.py::test_safe_replace_on_key_replaces_top_level_key PASSED [ 93%]
tests/test_update_playwright_safe.py::test_safe_replace_on_key_ignores_values_and_strings PASSED [ 94%]
tests/test_validation.py::test_validate_dataframe_valid PASSED [ 94%]
tests/test_validation.py::test_validate_dataframe_missing_amount_column PASSED [ 94%]
tests/test_validation.py::test_validate_dataframe_non_float_amount PASSED [ 95%]
tests/test_validation.py::test_validate_dataframe_string_amount PASSED [ 95%]
tests/test_validation.py::test_validate_dataframe_empty PASSED [ 95%]
tests/test_validation.py::test_validate_dataframe_with_nan PASSED [ 95%]
tests/test_validation.py::test_validation_constants_integrity PASSED [ 96%]
tests/test_validation.py::test_analytics_numeric_columns_subset PASSED [ 96%]
tests/test_validation.py::test_validate_numeric_bounds PASSED [ 96%]
tests/test_validation.py::test_find_column_logic PASSED [ 96%]
tests/test_validation.py::test_validate_dataframe_missing_multiple_columns PASSED [ 97%]
tests/test_validation.py::test_find_column_edge_cases PASSED [ 97%]
tests/test_validation.py::test_safe_numeric_empty PASSED [ 97%]
tests/test_validation.py::test_validate_percentage_bounds PASSED [ 97%]
tests/test_validation.py::test_validate_iso8601_dates PASSED [ 98%]
tests/unit/test_abaco_pipeline_cli_write_audit.py::test_write_audit_dry_run_prints_enriched_payload PASSED [ 98%]
tests/unit/test_abaco_pipeline_cli_write_audit.py::test_write_audit_writes_to_supabase PASSED [ 98%]
tests/unit/test_abaco_pipeline_output.py::test_write_manifest_writes_json PASSED [ 98%]
tests/unit/test_abaco_pipeline_quality.py::test_compute_freshness_hours_zero_when_same_time PASSED [ 99%]
tests/unit/test_abaco_pipeline_quality.py::test_compute_freshness_hours_positive_delta PASSED [ 99%]
tests/unit/test_abaco_pipeline_supabase_writer.py::test_upsert_pipeline_run_posts_expected_url_headers_and_body PASSED [ 99%]
tests/unit/test_abaco_pipeline_supabase_writer.py::test_insert_kpi_values_noop_on_empty PASSED [100%]03:10:06.529 | ERROR | opencensus.ext.azure.common.transport - Non-retryable server side error 400: {"itemsReceived":100,"itemsAccepted":0,"appId":null,"errors":[{"index":0,"statusCode":400,"message":"Invalid instrumentation key"},{"index":1,"statusCode":400,"message":"Invalid instrumentation key"},{"index":2,"statusCode":400,"message":"Invalid instrumentation key"},{"index":3,"statusCode":400,"message":"Invalid instrumentation key"},{"index":4,"statusCode":400,"message":"Invalid instrumentation key"},{"index":5,"statusCode":400,"message":"Invalid instrumentation key"},{"index":6,"statusCode":400,"message":"Invalid instrumentation key"},{"index":7,"statusCode":400,"message":"Invalid instrumentation key"},{"index":8,"statusCode":400,"message":"Invalid instrumentation key"},{"index":9,"statusCode":400,"message":"Invalid instrumentation key"},{"index":10,"statusCode":400,"message":"Invalid instrumentation key"},{"index":11,"statusCode":400,"message":"Invalid instrumentation key"},{"index":12,"statusCode":400,"message":"Invalid instrumentation key"},{"index":13,"statusCode":400,"message":"Invalid instrumentation key"},{"index":14,"statusCode":400,"message":"Invalid instrumentation key"},{"index":15,"statusCode":400,"message":"Invalid instrumentation key"},{"index":16,"statusCode":400,"message":"Invalid instrumentation key"},{"index":17,"statusCode":400,"message":"Invalid instrumentation key"},{"index":18,"statusCode":400,"message":"Invalid instrumentation key"},{"index":19,"statusCode":400,"message":"Invalid instrumentation key"},{"index":20,"statusCode":400,"message":"Invalid instrumentation key"},{"index":21,"statusCode":400,"message":"Invalid instrumentation key"},{"index":22,"statusCode":400,"message":"Invalid instrumentation key"},{"index":23,"statusCode":400,"message":"Invalid instrumentation key"},{"index":24,"statusCode":400,"message":"Invalid instrumentation key"},{"index":25,"statusCode":400,"message":"Invalid instrumentation key"},{"index":26,"statusCode":400,"message":"Invalid instrumentation key"},{"index":27,"statusCode":400,"message":"Invalid instrumentation key"},{"index":28,"statusCode":400,"message":"Invalid instrumentation key"},{"index":29,"statusCode":400,"message":"Invalid instrumentation key"},{"index":30,"statusCode":400,"message":"Invalid instrumentation key"},{"index":31,"statusCode":400,"message":"Invalid instrumentation key"},{"index":32,"statusCode":400,"message":"Invalid instrumentation key"},{"index":33,"statusCode":400,"message":"Invalid instrumentation key"},{"index":34,"statusCode":400,"message":"Invalid instrumentation key"},{"index":35,"statusCode":400,"message":"Invalid instrumentation key"},{"index":36,"statusCode":400,"message":"Invalid instrumentation key"},{"index":37,"statusCode":400,"message":"Invalid instrumentation key"},{"index":38,"statusCode":400,"message":"Invalid instrumentation key"},{"index":39,"statusCode":400,"message":"Invalid instrumentation key"},{"index":40,"statusCode":400,"message":"Invalid instrumentation key"},{"index":41,"statusCode":400,"message":"Invalid instrumentation key"},{"index":42,"statusCode":400,"message":"Invalid instrumentation key"},{"index":43,"statusCode":400,"message":"Invalid instrumentation key"},{"index":44,"statusCode":400,"message":"Invalid instrumentation key"},{"index":45,"statusCode":400,"message":"Invalid instrumentation key"},{"index":46,"statusCode":400,"message":"Invalid instrumentation key"},{"index":47,"statusCode":400,"message":"Invalid instrumentation key"},{"index":48,"statusCode":400,"message":"Invalid instrumentation key"},{"index":49,"statusCode":400,"message":"Invalid instrumentation key"},{"index":50,"statusCode":400,"message":"Invalid instrumentation key"},{"index":51,"statusCode":400,"message":"Invalid instrumentation key"},{"index":52,"statusCode":400,"message":"Invalid instrumentation key"},{"index":53,"statusCode":400,"message":"Invalid instrumentation key"},{"index":54,"statusCode":400,"message":"Invalid instrumentation key"},{"index":55,"statusCode":400,"message":"Invalid instrumentation key"},{"index":56,"statusCode":400,"message":"Invalid instrumentation key"},{"index":57,"statusCode":400,"message":"Invalid instrumentation key"},{"index":58,"statusCode":400,"message":"Invalid instrumentation key"},{"index":59,"statusCode":400,"message":"Invalid instrumentation key"},{"index":60,"statusCode":400,"message":"Invalid instrumentation key"},{"index":61,"statusCode":400,"message":"Invalid instrumentation key"},{"index":62,"statusCode":400,"message":"Invalid instrumentation key"},{"index":63,"statusCode":400,"message":"Invalid instrumentation key"},{"index":64,"statusCode":400,"message":"Invalid instrumentation key"},{"index":65,"statusCode":400,"message":"Invalid instrumentation key"},{"index":66,"statusCode":400,"message":"Invalid instrumentation key"},{"index":67,"statusCode":400,"message":"Invalid instrumentation key"},{"index":68,"statusCode":400,"message":"Invalid instrumentation key"},{"index":69,"statusCode":400,"message":"Invalid instrumentation key"},{"index":70,"statusCode":400,"message":"Invalid instrumentation key"},{"index":71,"statusCode":400,"message":"Invalid instrumentation key"},{"index":72,"statusCode":400,"message":"Invalid instrumentation key"},{"index":73,"statusCode":400,"message":"Invalid instrumentation key"},{"index":74,"statusCode":400,"message":"Invalid instrumentation key"},{"index":75,"statusCode":400,"message":"Invalid instrumentation key"},{"index":76,"statusCode":400,"message":"Invalid instrumentation key"},{"index":77,"statusCode":400,"message":"Invalid instrumentation key"},{"index":78,"statusCode":400,"message":"Invalid instrumentation key"},{"index":79,"statusCode":400,"message":"Invalid instrumentation key"},{"index":80,"statusCode":400,"message":"Invalid instrumentation key"},{"index":81,"statusCode":400,"message":"Invalid instrumentation key"},{"index":82,"statusCode":400,"message":"Invalid instrumentation key"},{"index":83,"statusCode":400,"message":"Invalid instrumentation key"},{"index":84,"statusCode":400,"message":"Invalid instrumentation key"},{"index":85,"statusCode":400,"message":"Invalid instrumentation key"},{"index":86,"statusCode":400,"message":"Invalid instrumentation key"},{"index":87,"statusCode":400,"message":"Invalid instrumentation key"},{"index":88,"statusCode":400,"message":"Invalid instrumentation key"},{"index":89,"statusCode":400,"message":"Invalid instrumentation key"},{"index":90,"statusCode":400,"message":"Invalid instrumentation key"},{"index":91,"statusCode":400,"message":"Invalid instrumentation key"},{"index":92,"statusCode":400,"message":"Invalid instrumentation key"},{"index":93,"statusCode":400,"message":"Invalid instrumentation key"},{"index":94,"statusCode":400,"message":"Invalid instrumentation key"},{"index":95,"statusCode":400,"message":"Invalid instrumentation key"},{"index":96,"statusCode":400,"message":"Invalid instrumentation key"},{"index":97,"statusCode":400,"message":"Invalid instrumentation key"},{"index":98,"statusCode":400,"message":"Invalid instrumentation key"},{"index":99,"statusCode":400,"message":"Invalid instrumentation key"}]}.

=================================== FAILURES ===================================
********\_******** test_engine_handles_all_nan_numeric_columns ********\_\_********
tests/test_enterprise_analytics_engine_extended.py:353: in test_engine_handles_all_nan_numeric_columns
kpis = engine.run_full_analysis()
src/analytics/enterprise_analytics_engine.py:240: in run_full_analysis
dashboard = portfolio_kpis(self.loan_data)
src/analytics/metrics_utils.py:209: in portfolio_kpis
else loan_to_value(sanitized_data["loan_amount"], sanitized_data["appraised_value"])
src/analytics/metrics_utils.py:80: in loan_to_value
sanitized_amounts = \_coerce_numeric(loan_amounts, "loan_amount")
src/analytics/metrics_utils.py:36: in \_coerce_numeric
raise ValueError(f"Field '{field_name}' must contain at least one numeric value")
E ValueError: Field 'loan_amount' must contain at least one numeric value
----------------------------- Captured stderr call -----------------------------
03:10:02.825 | INFO | src.kpi_engine_v2 - [KPI:calculate_all] started | {'kpi_count': 11}
03:10:02.826 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculated] success | {'kpi': 'PAR30', 'value': 0.0}
03:10:02.827 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculated] success | {'kpi': 'PAR90', 'value': 0.0}
03:10:02.827 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculated] success | {'kpi': 'CollectionRate', 'value': 0.0}
03:10:02.827 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'AUM', 'error': 'Missing required columns for AUM: outstanding_balance_usd'}
03:10:02.827 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'WeightedAPR', 'error': 'Missing columns for WeightedAPR: interest_rate, Disbursement Amount'}
03:10:02.828 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'ActualYield', 'error': 'Missing columns for ActualYield: cash_interest_usd, outstanding_balance_usd'}
03:10:02.828 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'Recurrence', 'error': 'Missing columns for Recurrence: cash_interest_usd'}
03:10:02.828 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'ConcentrationTop10', 'error': 'Missing columns for Concentration: client_id, Disbursement Amount'}
03:10:02.829 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculated] success | {'kpi': 'DefaultRate', 'value': 0.0}
03:10:02.829 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'ActiveClients', 'error': 'Missing columns for ActiveClients: loan_status, client_id'}
03:10:02.829 | INFO | src.kpi_engine_v2 - [KPI:kpi_calculation_failed] error | {'kpi': 'ChurnRate', 'error': 'Missing columns for ChurnRate: Disbursement Date, Customer ID'}
03:10:02.829 | INFO | src.kpi_engine_v2 - [KPI:composite_kpi_calculated] success | {'kpi': 'PortfolioHealth'}
03:10:02.830 | INFO | src.kpi_engine_v2 - [KPI:calculate_all] completed | {'kpi_count': 12}
------------------------------ Captured log call -------------------------------
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:calculate_all] started | {'kpi_count': 11}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculated] success | {'kpi': 'PAR30', 'value': 0.0}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculated] success | {'kpi': 'PAR90', 'value': 0.0}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculated] success | {'kpi': 'CollectionRate', 'value': 0.0}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'AUM', 'error': 'Missing required columns for AUM: outstanding_balance_usd'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'WeightedAPR', 'error': 'Missing columns for WeightedAPR: interest_rate, Disbursement Amount'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'ActualYield', 'error': 'Missing columns for ActualYield: cash_interest_usd, outstanding_balance_usd'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'Recurrence', 'error': 'Missing columns for Recurrence: cash_interest_usd'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'ConcentrationTop10', 'error': 'Missing columns for Concentration: client_id, Disbursement Amount'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculated] success | {'kpi': 'DefaultRate', 'value': 0.0}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'ActiveClients', 'error': 'Missing columns for ActiveClients: loan_status, client_id'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:kpi_calculation_failed] error | {'kpi': 'ChurnRate', 'error': 'Missing columns for ChurnRate: Disbursement Date, Customer ID'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:composite_kpi_calculated] success | {'kpi': 'PortfolioHealth'}
INFO src.kpi_engine_v2:kpi_engine_v2.py:220 [KPI:calculate_all] completed | {'kpi_count': 12}
=============================== warnings summary ===============================
../../Library/Python/3.9/lib/python/site-packages/pandera/\_pandas_deprecated.py:160
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pandera/\_pandas_deprecated.py:160: FutureWarning: Importing pandas-specific classes and functions from the
top-level pandera module will be **removed in a future version of pandera**.
If you're using pandera to validate pandas objects, we highly recommend updating
your import:

```
# old import
import pandera as pa

# new import
import pandera.pandas as pa
```

If you're using pandera to validate objects from other compatible libraries
like pyspark or polars, see the supported libraries section of the documentation
for more information on how to import pandera:

https://pandera.readthedocs.io/en/stable/supported_libraries.html

To disable this warning, set the environment variable:

```
export DISABLE_PANDERA_IMPORT_WARNING=True
```

    warnings.warn(_future_warning, FutureWarning)

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:19
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:19: DeprecationWarning: 'setName' deprecated - use 'set_name'
token = pp.Word(tchar).setName("token")

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20: DeprecationWarning: 'leaveWhitespace' deprecated - use 'leave*whitespace'
token68 = pp.Combine(pp.Word("-.*~+/" + pp.nums + pp.alphas) + pp.Optional(pp.Word("=").leaveWhitespace())).setName(

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20: DeprecationWarning: 'setName' deprecated - use 'set*name'
token68 = pp.Combine(pp.Word("-.*~+/" + pp.nums + pp.alphas) + pp.Optional(pp.Word("=").leaveWhitespace())).setName(

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:24
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:24: DeprecationWarning: 'setName' deprecated - use 'set_name'
quoted_string = pp.dblQuotedString.copy().setName("quoted-string").setParseAction(unquote)

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:24
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:24: DeprecationWarning: 'setParseAction' deprecated - use 'set_parse_action'
quoted_string = pp.dblQuotedString.copy().setName("quoted-string").setParseAction(unquote)

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:25
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:25: DeprecationWarning: 'setName' deprecated - use 'set_name'
auth_param_name = token.copy().setName("auth-param-name").addParseAction(downcaseTokens)

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:25
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:25: DeprecationWarning: 'addParseAction' deprecated - use 'add_parse_action'
auth_param_name = token.copy().setName("auth-param-name").addParseAction(downcaseTokens)

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:27
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:27: DeprecationWarning: 'delimitedList' deprecated - use 'DelimitedList'
params = pp.Dict(pp.delimitedList(pp.Group(auth_param)))

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:33
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:33: DeprecationWarning: 'delimitedList' deprecated - use 'DelimitedList'
www_authenticate = pp.delimitedList(pp.Group(challenge))

../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:64
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:64: DeprecationWarning: 'oneOf' deprecated - use 'one_of'
prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(\_CONSTANTS))

../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:85: DeprecationWarning: 'parseString' deprecated - use 'parse_string'
parse = parser.parseString(pattern)

../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/\_fontconfig_pattern.py:89: DeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
parser.resetCache()

../../Library/Python/3.9/lib/python/site-packages/matplotlib/\_mathtext.py:45
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/\_mathtext.py:45: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
ParserElement.enablePackrat()

python/pipeline/ingestion.py:28
/Users/jenineferderas/Documents/abaco-loans-analytics/python/pipeline/ingestion.py:28: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
class LoanRecord(BaseModel):

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:72: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
ParserElement.enablePackrat()

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85: DeprecationWarning: 'escChar' argument is deprecated, use 'esc_char'
quoted_identifier = QuotedString('"', escChar="\\", unquoteResults=True)

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85: DeprecationWarning: 'unquoteResults' argument is deprecated, use 'unquote_results'
quoted_identifier = QuotedString('"', escChar="\\", unquoteResults=True)

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:366: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def construct_refs(cls, data: TableMetadataV1) -> TableMetadataV1:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:495: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_schemas(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:499: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_partition_specs(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:503: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_sort_orders(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:507: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def construct_refs(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:539: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_schemas(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:543: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_partition_specs(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:547: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def check_sort_orders(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json
/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:551: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
def construct_refs(cls, table_metadata: TableMetadata) -> TableMetadata:

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_enterprise_analytics_engine_extended.py::test_engine_handles_all_nan_numeric_columns
====== 1 failed, 370 passed, 12 skipped, 37 warnings in 68.78s (0:01:08) =======
--- Logging error ---
Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 204, in \_new_conn
sock = connection.create_connection(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/connection.py", line 85, in create_connection
raise err
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/connection.py", line 73, in create_connection
sock.connect(sa)
ConnectionRefusedError: [Errno 61] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 787, in urlopen
response = self.\_make_request(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 493, in \_make_request
conn.request(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 500, in request
self.endheaders()
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 1252, in endheaders
self.\_send_output(message_body, encode_chunked=encode_chunked)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 1012, in \_send_output
self.send(msg)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 952, in send
self.connect()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 331, in connect
self.sock = self.\_new_conn()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 219, in \_new_conn
raise NewConnectionError(
urllib3.exceptions.NewConnectionError: HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/adapters.py", line 644, in send
resp = conn.urlopen(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 841, in urlopen
retries = retries.increment(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/retry.py", line 519, in increment
raise MaxRetryError(\_pool, url, reason) from reason # type: ignore[arg-type]
urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: / (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/exporter/otlp/proto/http/trace_exporter/**init**.py", line 157, in \_export
resp = self.\_session.post(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 637, in post
return self.request("POST", url, data=data, json=json, **kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 589, in request
resp = self.send(prep, **send_kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 703, in send
r = adapter.send(request, \*\*kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/adapters.py", line 677, in send
raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: / (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 204, in \_new_conn
sock = connection.create_connection(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/connection.py", line 85, in create_connection
raise err
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/connection.py", line 73, in create_connection
sock.connect(sa)
ConnectionRefusedError: [Errno 61] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 787, in urlopen
response = self.\_make_request(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 493, in \_make_request
conn.request(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 500, in request
self.endheaders()
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 1252, in endheaders
self.\_send_output(message_body, encode_chunked=encode_chunked)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 1012, in \_send_output
self.send(msg)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/http/client.py", line 952, in send
self.connect()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 331, in connect
self.sock = self.\_new_conn()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connection.py", line 219, in \_new_conn
raise NewConnectionError(
urllib3.exceptions.NewConnectionError: HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/adapters.py", line 644, in send
resp = conn.urlopen(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/connectionpool.py", line 841, in urlopen
retries = retries.increment(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/util/retry.py", line 519, in increment
raise MaxRetryError(\_pool, url, reason) from reason # type: ignore[arg-type]
urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: / (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/sdk/\_shared_internal/**init**.py", line 179, in \_export
self.\_exporter.export(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/exporter/otlp/proto/http/trace_exporter/**init**.py", line 182, in export
resp = self.\_export(serialized_data, deadline_sec - time())
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/exporter/otlp/proto/http/trace_exporter/**init**.py", line 165, in \_export
resp = self.\_session.post(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 637, in post
return self.request("POST", url, data=data, json=json, **kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 589, in request
resp = self.send(prep, **send_kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/sessions.py", line 703, in send
r = adapter.send(request, \*\*kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/requests/adapters.py", line 677, in send
raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=4318): Max retries exceeded with url: / (Caused by NewConnectionError("HTTPConnection(host='localhost', port=4318): Failed to establish a new connection: [Errno 61] Connection refused"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/prefect/logging/handlers.py", line 355, in emit
self.console.print(message, soft_wrap=True)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 1745, in print
self.\_buffer.extend(new_segments)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 870, in **exit**
self.\_exit_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 826, in \_exit_buffer
self.\_check_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 2038, in \_check_buffer
self.\_write_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 2107, in \_write_buffer
self.file.write(text)
ValueError: I/O operation on closed file.
Call stack:
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/threading.py", line 930, in \_bootstrap
self.\_bootstrap_inner()
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/threading.py", line 973, in \_bootstrap_inner
self.run()
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/threading.py", line 910, in run
self.\_target(*self.\_args, \*\*self.\_kwargs)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/sdk/\_shared_internal/**init**.py", line 162, in worker
self.\_export(
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opentelemetry/sdk/\_shared_internal/**init**.py", line 192, in \_export
self.\_logger.exception(
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1481, in exception
self.error(msg, *args, exc_info=exc_info, **kwargs)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1475, in error
self.\_log(ERROR, msg, args, **kwargs)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1589, in \_log
self.handle(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1599, in handle
self.callHandlers(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1661, in callHandlers
hdlr.handle(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 952, in handle
self.emit(record)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/prefect/logging/handlers.py", line 361, in emit
self.handleError(record)
Message: 'Exception while exporting %s.'
Arguments: ('Span',)
--- Logging error ---
Traceback (most recent call last):
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/prefect/logging/handlers.py", line 355, in emit
self.console.print(message, soft_wrap=True)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 1745, in print
self.\_buffer.extend(new_segments)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 870, in **exit**
self.\_exit_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 826, in \_exit_buffer
self.\_check_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 2038, in \_check_buffer
self.\_write_buffer()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/rich/console.py", line 2107, in \_write_buffer
self.file.write(text)
ValueError: I/O operation on closed file.
Call stack:
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/threading.py", line 930, in \_bootstrap
self.\_bootstrap_inner()
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/threading.py", line 973, in \_bootstrap_inner
self.run()
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opencensus/ext/azure/log_exporter/**init**.py", line 154, in run
dst.\_export(batch[:-1], event=batch[-1])
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opencensus/ext/azure/log_exporter/**init**.py", line 76, in \_export
result = self.\_transmit(envelopes)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/opencensus/ext/azure/common/transport.py", line 311, in \_transmit
logger.error(
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1475, in error
self.\_log(ERROR, msg, args, \*\*kwargs)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1589, in \_log
self.handle(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1599, in handle
self.callHandlers(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 1661, in callHandlers
hdlr.handle(record)
File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/logging/**init**.py", line 952, in handle
self.emit(record)
File "/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/prefect/logging/handlers.py", line 361, in emit
self.handleError(record)
Message: 'Non-retryable server side error %s: %s.'
Arguments: (400, '{"itemsReceived":28,"itemsAccepted":0,"appId":null,"errors":[{"index":0,"statusCode":400,"message":"Invalid instrumentation key"},{"index":1,"statusCode":400,"message":"Invalid instrumentation key"},{"index":2,"statusCode":400,"message":"Invalid instrumentation key"},{"index":3,"statusCode":400,"message":"Invalid instrumentation key"},{"index":4,"statusCode":400,"message":"Invalid instrumentation key"},{"index":5,"statusCode":400,"message":"Invalid instrumentation key"},{"index":6,"statusCode":400,"message":"Invalid instrumentation key"},{"index":7,"statusCode":400,"message":"Invalid instrumentation key"},{"index":8,"statusCode":400,"message":"Invalid instrumentation key"},{"index":9,"statusCode":400,"message":"Invalid instrumentation key"},{"index":10,"statusCode":400,"message":"Invalid instrumentation key"},{"index":11,"statusCode":400,"message":"Invalid instrumentation key"},{"index":12,"statusCode":400,"message":"Invalid instrumentation key"},{"index":13,"statusCode":400,"message":"Invalid instrumentation key"},{"index":14,"statusCode":400,"message":"Invalid instrumentation key"},{"index":15,"statusCode":400,"message":"Invalid instrumentation key"},{"index":16,"statusCode":400,"message":"Invalid instrumentation key"},{"index":17,"statusCode":400,"message":"Invalid instrumentation key"},{"index":18,"statusCode":400,"message":"Invalid instrumentation key"},{"index":19,"statusCode":400,"message":"Invalid instrumentation key"},{"index":20,"statusCode":400,"message":"Invalid instrumentation key"},{"index":21,"statusCode":400,"message":"Invalid instrumentation key"},{"index":22,"statusCode":400,"message":"Invalid instrumentation key"},{"index":23,"statusCode":400,"message":"Invalid instrumentation key"},{"index":24,"statusCode":400,"message":"Invalid instrumentation key"},{"index":25,"statusCode":400,"message":"Invalid instrumentation key"},{"index":26,"statusCode":400,"message":"Invalid instrumentation key"},{"index":27,"statusCode":400,"message":"Invalid instrumentation key"}]}')

**Result**: ✓ PASSED

## 4. LINTING CHECKS

### Pylint

******\******* Module src.pipeline.data_ingestion
src/pipeline/data_ingestion.py:159:12: W0101: Unreachable code (unreachable)
******\******* Module src.pipeline.kpi_calculation
src/pipeline/kpi_calculation.py:88:16: W0707: Consider explicitly re-raising using 'raise ValueError(f'Missing function for metric {name} and engine fallback failed: {exc}') from exc' (raise-missing-from)
******\******* Module src.kpis.par_30
src/kpis/par_30.py:35:8: R1705: Unnecessary "elif" after "return", remove the leading "el" from "elif" (no-else-return)
******\******* Module src.integrations.batch_export_runner
src/integrations/batch_export_runner.py:182:12: R1705: Unnecessary "elif" after "return", remove the leading "el" from "elif" (no-else-return)

---

Your code has been rated at 9.99/10 (previous run: 9.99/10, +0.00)

### Flake8

### Ruff

All checks passed!

## 5. TYPE CHECKING

### mypy

Success: no issues found in 121 source files

## 6. CI WORKFLOW VALIDATION

### Workflow Jobs Analysis

**Detected Jobs in ci.yml**:

- contents
- pull-requests
- push
- schedule
- changes
- assignee-check
- repo-health
- run-demos
- web
- analytics
- update-figma-slides
- notify-on-failure

### Key Failure Points

- Secret handling (FIGMA_TOKEN, SLACK_WEBHOOK_URL, Vercel tokens)
- External API integrations (HubSpot, Supabase)
- Artifact uploads and caching
- Dependency installation (pnpm, pip)

## 7. SUMMARY

**Report saved to**: CI_DIAGNOSIS_REPORT.md
