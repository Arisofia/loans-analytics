# CI Workflow Failure Diagnosis Report
**Generated**: Fri Jan  9 16:06:18 CET 2026
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
✓ ci.yml: VALID

## 3. TEST EXECUTION
### Running Tests...

/Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: /Users/jenineferderas/Documents/abaco-loans-analytics
configfile: pytest.ini
plugins: mock-3.15.1, anyio-4.12.0, hypothesis-6.141.1, timeout-2.4.0, typeguard-4.4.4, Faker-37.12.0, requests-mock-1.12.1, cov-7.0.0
collecting ... collected 459 items / 3 skipped

tests/api/test_path_safety.py::test_sanitize_and_resolve_valid PASSED    [  0%]
tests/api/test_path_safety.py::test_sanitize_and_resolve_rejects_absolute PASSED [  0%]
tests/api/test_path_safety.py::test_sanitize_and_resolve_rejects_parent_traversal PASSED [  0%]
tests/api/test_path_safety.py::test_sanitize_and_resolve_outside PASSED  [  0%]
tests/data_tests/test_kpi_contracts.py::test_par_90_from_sample_data PASSED [  1%]
tests/data_tests/test_kpi_contracts.py::test_collection_rate_calculation PASSED [  1%]
tests/data_tests/test_kpi_contracts.py::test_segment_level_contracts PASSED [  1%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_normality PASSED [  1%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_heteroscedasticity PASSED [  1%]
tests/data_tests/test_kpi_regression_robust.py::test_kpi_multicollinearity PASSED [  2%]
tests/data_tests/test_kpi_stat_advanced.py::test_par_90_is_weighted_by_segment PASSED [  2%]
tests/data_tests/test_kpi_stat_advanced.py::test_collection_rate_remains_above_thresholds PASSED [  2%]
tests/data_tests/test_kpi_stat_advanced.py::test_no_missing_segments_or_dates PASSED [  2%]
tests/data_tests/test_kpi_stat_extra.py::test_kpi_chi2_contingency PASSED [  3%]
tests/data_tests/test_kpi_stat_extra.py::test_kpi_mannwhitney PASSED     [  3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_classification_metrics PASSED [  3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_threshold_validation SKIPPED [  3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_financial_metrics_structure SKIPPED [  3%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_model_stability_metrics SKIPPED [  4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_fairness_compliance_metrics SKIPPED [  4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_business_kpis_structure SKIPPED [  4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[accuracy-expected_range0] PASSED [  4%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[precision-expected_range1] PASSED [  5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[recall-expected_range2] PASSED [  5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[f1_score-expected_range3] PASSED [  5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_metric_ranges[roc_auc-expected_range4] PASSED [  5%]
tests/evaluation/test_model_evaluation.py::TestModelEvaluation::test_evaluation_pipeline_integration PASSED [  5%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_config_file_exists PASSED [  6%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_config_yaml_valid SKIPPED [  6%]
tests/evaluation/test_model_evaluation.py::TestThresholdConfiguration::test_threshold_values_reasonable SKIPPED [  6%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_c01_figma_sync_success PASSED [  6%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_d01_otlp_span_generation PASSED [  6%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_f01_secret_masking PASSED [  7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_c04_notion_timeout_simulation PASSED [  7%]
tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_f02_unauthorized_access PASSED [  7%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b01_kpi_baseline_match SKIPPED [  7%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b01_no_nan_or_inf_values PASSED [  8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_null_and_zero_handling PASSED [  8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_division_by_zero_safety PASSED [  8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_negative_value_handling PASSED [  8%]
tests/fi-analytics/test_analytics_kpi_correctness.py::TestKPICorrectness::test_b02_large_value_handling PASSED [  8%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_b03_performance_sla PASSED [  9%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_g01_idempotency PASSED [  9%]
tests/fi-analytics/test_analytics_performance.py::TestAnalyticsPerformanceRobustness::test_i01_e2e_acceptance PASSED [  9%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a01_pipeline_smoke_execution PASSED [  9%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_artifact_existence_and_schema PASSED [ 10%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_json_required_fields PASSED [ 10%]
tests/fi-analytics/test_analytics_smoke.py::TestAnalyticsSmoke::test_a02_csv_valid_structure PASSED [ 10%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_unit_test_execution SKIPPED [ 10%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_coverage_threshold SKIPPED [ 10%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_no_import_errors PASSED [ 11%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsUnitCoverage::test_h01_regression_baseline PASSED [ 11%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_mypy_validation_smoke PASSED [ 11%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_module_type_hints_present PASSED [ 11%]
tests/fi-analytics/test_analytics_unit_coverage.py::TestAnalyticsTypeCheck::test_h02_docstrings_present PASSED [ 11%]
tests/ingestion/test_archive.py::test_archive_failure_records_error PASSED [ 12%]
tests/ingestion/test_basics.py::test_archive_raw_and_log PASSED          [ 12%]
tests/ingestion/test_basics.py::test_apply_deduplication_config PASSED   [ 12%]
tests/ingestion/test_basics.py::test_validation_strict_raises PASSED     [ 12%]
tests/ingestion/test_behavior.py::test_ingest_http_retries_and_success PASSED [ 13%]
tests/ingestion/test_behavior.py::test_circuit_breaker_opens_after_failure PASSED [ 13%]
tests/ingestion/test_behavior.py::test_rate_limiter_wait_called PASSED   [ 13%]
tests/ingestion/test_behavior.py::test_ingest_looker_missing_columns_raises PASSED [ 13%]
tests/ingestion/test_formats.py::test_ingest_file_xlsx PASSED            [ 13%]
tests/ingestion/test_formats.py::test_ingest_file_json PASSED            [ 14%]
tests/ingestion/test_formats.py::test_ingest_file_strict_raises PASSED   [ 14%]
tests/ingestion/test_looker.py::test_measurement_strategy_max_disburse_date PASSED [ 14%]
tests/ingestion/test_looker.py::test_load_looker_financials_selects_latest PASSED [ 14%]
tests/ingestion/test_looker.py::test_looker_par_balances_to_loan_tape PASSED [ 15%]
tests/ingestion/test_looker.py::test_looker_dpd_to_loan_tape PASSED      [ 15%]
tests/ingestion/test_looker.py::test_ingest_looker_missing_columns_raises PASSED [ 15%]
tests/ingestion/test_quality.py::test_data_quality_report_passed PASSED  [ 15%]
tests/ingestion/test_quality.py::test_data_quality_report_failed_missing_column PASSED [ 15%]
tests/ingestion/test_quality.py::test_data_quality_report_type_error PASSED [ 16%]
tests/integration/test_figma_sync_requests_mock.py::test_figma_sync_with_requests_mock PASSED [ 16%]
tests/integration/test_figma_sync_requests_mock.py::test_figma_sync_handles_rate_limit PASSED [ 16%]
tests/scripts/test_load_secrets.py::test_redact_dict_masks_keys PASSED   [ 16%]
tests/test_analytics_metrics.py::test_standardize_numeric_handles_symbols PASSED [ 16%]
tests/test_analytics_metrics.py::test_standardize_numeric_passes_through_numeric_series PASSED [ 17%]
tests/test_analytics_metrics.py::test_standardize_numeric_handles_negative_symbols_and_commas PASSED [ 17%]
tests/test_analytics_metrics.py::test_project_growth_requires_minimum_periods PASSED [ 17%]
tests/test_analytics_metrics.py::test_project_growth_builds_monotonic_path PASSED [ 17%]
tests/test_analytics_metrics.py::test_project_growth_uses_default_periods PASSED [ 18%]
tests/test_analytics_metrics.py::test_project_growth_supports_decreasing_targets PASSED [ 18%]
tests/test_analytics_metrics.py::test_calculate_quality_score_handles_empty_df PASSED [ 18%]
tests/test_analytics_metrics.py::test_calculate_quality_score_rewards_complete_data PASSED [ 18%]
tests/test_analytics_metrics.py::test_calculate_quality_score_counts_completeness PASSED [ 18%]
tests/test_analytics_metrics.py::test_portfolio_kpis_returns_expected_metrics PASSED [ 19%]
tests/test_analytics_metrics.py::test_portfolio_kpis_missing_column_raises PASSED [ 19%]
tests/test_analytics_metrics.py::test_portfolio_kpis_handles_empty_frame PASSED [ 19%]
tests/test_analytics_metrics.py::test_portfolio_kpis_zero_principal_yield_is_zero PASSED [ 19%]
tests/test_analytics_metrics.py::test_portfolio_kpis_dti_nan_when_income_non_positive PASSED [ 20%]
tests/test_analytics_metrics.py::test_portfolio_kpis_ltv_nan_when_appraisal_non_positive PASSED [ 20%]
tests/test_api_kpis.py::test_get_latest_kpis PASSED                      [ 20%]
tests/test_aum_growth.py::test_calculate_growth_positive PASSED          [ 20%]
tests/test_aum_growth.py::test_calculate_growth_negative PASSED          [ 20%]
tests/test_aum_growth.py::test_calculate_growth_zero_previous PASSED     [ 21%]
tests/test_clients.py::TestGrokClient::test_generate_text_calls_api PASSED [ 21%]
tests/test_clients.py::TestGrokClient::test_generate_text_raises_without_api_key PASSED [ 21%]
tests/test_clients.py::TestGrokClient::test_init_defaults PASSED         [ 21%]
tests/test_clients.py::TestGrokClient::test_session_configuration PASSED [ 22%]
tests/test_clients.py::TestGeminiClient::test_generate_text_calls_model PASSED [ 22%]
tests/test_clients.py::TestGeminiClient::test_init_configures_genai PASSED [ 22%]
tests/test_clients.py::TestGeminiClient::test_init_raises_without_api_key PASSED [ 22%]
tests/test_collection_rate.py::test_calculate_collection_rate_standard PASSED [ 22%]
tests/test_collection_rate.py::test_calculate_collection_rate_zero_eligible PASSED [ 23%]
tests/test_collection_rate.py::test_calculate_collection_rate_missing_columns PASSED [ 23%]
tests/test_collection_rate.py::test_calculate_collection_rate_empty_df PASSED [ 23%]
tests/test_compliance.py::test_mask_pii_columns_by_keywords PASSED       [ 23%]
tests/test_compliance.py::test_mask_pii_columns_override PASSED          [ 23%]
tests/test_compliance.py::test_access_log_entry_contains_context PASSED  [ 24%]
tests/test_compliance.py::test_build_compliance_report_includes_metadata PASSED [ 24%]
tests/test_dashboard_utils.py::test_compute_cat_agg_missing_value_col PASSED [ 24%]
tests/test_dashboard_utils.py::test_compute_cat_agg_with_values PASSED   [ 24%]
tests/test_dataframe_assertions.py::test_assert_dataframe_schema_detects_missing_columns PASSED [ 25%]
tests/test_dataframe_assertions.py::test_assert_dataframe_schema_detects_non_numeric_columns PASSED [ 25%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_runs PASSED [ 25%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_skips_plots_if_columns_missing PASSED [ 25%]
tests/test_demo_scripts.py::TestDemoScripts::test_demo_financial_analysis_with_file PASSED [ 25%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_pipeline_execution_produces_valid_output PASSED [ 26%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_main_script_success PASSED [ 26%]
tests/test_deployment_e2e.py::TestDeploymentE2E::test_e2e_missing_dataset_error PASSED [ 26%]
tests/test_enterprise_analytics_engine.py::test_initialization_requires_data PASSED [ 26%]
tests/test_enterprise_analytics_engine.py::test_validates_missing_columns PASSED [ 27%]
tests/test_enterprise_analytics_engine.py::test_ltv_handles_zero_appraised_value PASSED [ 27%]
tests/test_enterprise_analytics_engine.py::test_dti_returns_series_with_index PASSED [ 27%]
tests/test_enterprise_analytics_engine.py::test_risk_alerts_surface_high_risk_loans PASSED [ 27%]
tests/test_enterprise_analytics_engine.py::test_run_full_analysis_includes_quality PASSED [ 27%]
tests/test_enterprise_analytics_engine.py::test_coerces_invalid_numeric_values_and_reports_quality PASSED [ 28%]
tests/test_enterprise_analytics_engine.py::test_source_dataframe_remains_unchanged_after_analysis PASSED [ 28%]
tests/test_enterprise_analytics_engine.py::test_compute_delinquency_rate PASSED [ 28%]
tests/test_enterprise_analytics_engine.py::test_compute_portfolio_yield PASSED [ 28%]
tests/test_enterprise_analytics_engine.py::test_dti_excludes_nan_from_average PASSED [ 28%]
tests/test_enterprise_analytics_engine.py::test_check_data_sanity_warns_on_high_interest_rate PASSED [ 29%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_from_dict PASSED [ 29%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_coercion_report_tracking PASSED [ 29%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_empty_dataframe PASSED [ 29%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_non_dataframe_input PASSED [ 30%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_ltv_with_infinity PASSED [ 30%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_dti_with_negative_income PASSED [ 30%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_with_duplicates PASSED [ 30%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_with_null_values PASSED [ 30%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_data_quality_score_calculation PASSED [ 31%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_empty_result PASSED [ 31%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_risk_score_calculation PASSED [ 31%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_risk_alerts_with_nan_values PASSED [ 31%]
tests/test_enterprise_analytics_engine_extended.py::test_export_kpis_to_blob_invalid_blob_name_type PASSED [ 32%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_export_kpis_to_blob_valid PASSED [ 32%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_source_df_not_modified PASSED [ 32%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_coercion_preserves_all_nan_columns PASSED [ 32%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_run_full_analysis_returns_all_keys PASSED [ 32%]
tests/test_enterprise_analytics_engine_extended.py::test_engine_handles_all_nan_numeric_columns PASSED [ 33%]
tests/test_export_scripts.py::TestExportScripts::test_export_copilot_slide_payload PASSED [ 33%]
tests/test_feedback_and_tracing.py::test_feedback_store_skips_malformed_files PASSED [ 33%]
tests/test_feedback_and_tracing.py::test_trace_analytics_job_wraps_and_logs PASSED [ 33%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_hhi PASSED [ 33%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_hhi_fuzzy PASSED [ 34%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_line_utilization PASSED [ 34%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_calculate_weighted_stats PASSED [ 34%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_client_type PASSED [ 34%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_dpd_buckets PASSED [ 35%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_classify_dpd_buckets_fuzzy PASSED [ 35%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_enrich_master_dataframe PASSED [ 35%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_segment_clients_by_exposure PASSED [ 35%]
tests/test_financial_analysis.py::TestFinancialAnalyzer::test_segment_clients_by_exposure_fuzzy PASSED [ 35%]
tests/test_generate_markdown_report.py::TestGenerateMarkdownReport::test_generate_report_creates_file PASSED [ 36%]
tests/test_generate_markdown_report.py::TestGenerateMarkdownReport::test_generate_report_handles_missing_files PASSED [ 36%]
tests/test_ingestion.py::test_ingest_csv PASSED                          [ 36%]
tests/test_ingestion.py::test_ingest_csv_error PASSED                    [ 36%]
tests/test_ingestion.py::test_ingest_csv_empty_file PASSED               [ 37%]
tests/test_ingestion.py::test_ingest_csv_strict_schema_failure PASSED    [ 37%]
tests/test_ingestion.py::test_ingest_csv_success PASSED                  [ 37%]
tests/test_ingestion.py::test_ingest_http PASSED                         [ 37%]
tests/test_ingestion.py::test_run_id_generation PASSED                   [ 37%]
tests/test_ingestion.py::test_audit_log_creation PASSED                  [ 38%]
tests/test_ingestion.py::test_looker_par_balances_to_loan_tape PASSED    [ 38%]
tests/test_ingestion.py::test_looker_dpd_to_loan_tape PASSED             [ 38%]
tests/test_ingestion.py::test_ingest_looker_with_par_balances PASSED     [ 38%]
tests/test_ingestion.py::test_ingest_looker_with_dpd_data PASSED         [ 38%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_valid PASSED  [ 39%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_with_nulls PASSED [ 39%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_with_custom_fill PASSED [ 39%]
tests/test_kpi_base.py::TestSafeNumeric::test_safe_numeric_coercion PASSED [ 39%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_basic PASSED [ 40%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_with_nulls PASSED [ 40%]
tests/test_kpi_base.py::TestCreateContext::test_create_context_with_extra PASSED [ 40%]
tests/test_kpi_base.py::TestKPIMetadata::test_metadata_creation PASSED   [ 40%]
tests/test_kpi_base.py::TestKPIMetadata::test_metadata_to_dict PASSED    [ 40%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_valid_calculation PASSED [ 41%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_zero_receivable PASSED [ 41%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_empty_dataframe PASSED [ 41%]
tests/test_kpi_calculators_v2.py::TestPAR30Calculator::test_par30_missing_columns PASSED [ 41%]
tests/test_kpi_calculators_v2.py::TestPAR90Calculator::test_par90_valid_calculation PASSED [ 42%]
tests/test_kpi_calculators_v2.py::TestPAR90Calculator::test_par90_zero_receivable PASSED [ 42%]
tests/test_kpi_calculators_v2.py::TestCollectionRateCalculator::test_collection_rate_valid PASSED [ 42%]
tests/test_kpi_calculators_v2.py::TestCollectionRateCalculator::test_collection_rate_with_nulls PASSED [ 42%]
tests/test_kpi_calculators_v2.py::TestPortfolioHealthCalculator::test_portfolio_health_valid PASSED [ 42%]
tests/test_kpi_calculators_v2.py::TestPortfolioHealthCalculator::test_portfolio_health_bounds PASSED [ 43%]
tests/test_kpi_edge_cases.py::test_empty_dataset PASSED                  [ 43%]
tests/test_kpi_edge_cases.py::test_single_value_dataset PASSED           [ 43%]
tests/test_kpi_edge_cases.py::test_mannwhitneyu_identical PASSED         [ 43%]
tests/test_kpi_edge_cases.py::test_chi2_contingency_perfect PASSED       [ 44%]
tests/test_kpi_engine.py::test_calculate_par_30 PASSED                   [ 44%]
tests/test_kpi_engine.py::test_calculate_par_90 PASSED                   [ 44%]
tests/test_kpi_engine.py::test_calculate_collection_rate PASSED          [ 44%]
tests/test_kpi_engine.py::test_calculate_all PASSED                      [ 44%]
tests/test_kpi_engine.py::test_get_audit_trail PASSED                    [ 45%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_kpi_engine_initialization PASSED [ 45%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_calculate_all PASSED  [ 45%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_individual_calculations PASSED [ 45%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_audit_trail PASSED    [ 45%]
tests/test_kpi_engine_v2.py::TestKPIEngineV2::test_empty_dataframe PASSED [ 46%]
tests/test_kpis_integration.py::test_par_and_aum_growth_integration PASSED [ 46%]
tests/test_manifest_segmentation.py::test_manifest_contains_segmentation_data PASSED [ 46%]
tests/test_metrics_utils.py::TestMetricsUtils::test_engine_uses_metric_utilities PASSED [ 46%]
tests/test_metrics_utils.py::TestMetricsUtils::test_kpis_match_expected_values PASSED [ 47%]
tests/test_metrics_utils.py::TestMetricsUtils::test_metric_helpers_handle_edge_cases PASSED [ 47%]
tests/test_metrics_utils.py::TestMetricsUtils::test_numeric_coercion_and_defaults PASSED [ 47%]
tests/test_metrics_utils_extended.py::test_coerce_numeric_all_nan PASSED [ 47%]
tests/test_metrics_utils_extended.py::test_validate_kpi_columns_empty_dataframe PASSED [ 47%]
tests/test_metrics_utils_extended.py::test_validate_kpi_columns_missing_multiple PASSED [ 48%]
tests/test_metrics_utils_extended.py::test_loan_to_value_all_zeros PASSED [ 48%]
tests/test_metrics_utils_extended.py::test_portfolio_delinquency_rate_no_delinquent PASSED [ 48%]
tests/test_metrics_utils_extended.py::test_portfolio_delinquency_rate_all_delinquent PASSED [ 48%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_zero_principal PASSED [ 49%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_nan_values PASSED [ 49%]
tests/test_metrics_utils_extended.py::test_portfolio_kpis_with_precalculated_ratios PASSED [ 49%]
tests/test_metrics_utils_extended.py::test_portfolio_kpis_handles_nan_in_ratios PASSED [ 49%]
tests/test_metrics_utils_extended.py::test_coerce_numeric_mixed_valid_invalid PASSED [ 49%]
tests/test_metrics_utils_extended.py::test_loan_to_value_with_negative_values PASSED [ 50%]
tests/test_metrics_utils_extended.py::test_debt_to_income_ratio_negative_income PASSED [ 50%]
tests/test_metrics_utils_extended.py::test_weighted_portfolio_yield_string_conversion PASSED [ 50%]
tests/test_metrics_validation.py::test_batch_export_load_latest_metrics_invalid_json PASSED [ 50%]
tests/test_metrics_validation.py::test_load_dashboard_metrics_invalid_json PASSED [ 50%]
tests/test_output_triggers.py::test_dashboard_trigger_on_persist PASSED  [ 51%]
tests/test_par_30.py::test_calculate_par_30_standard PASSED              [ 51%]
tests/test_par_30.py::test_calculate_par_30_zero_receivable PASSED       [ 51%]
tests/test_par_30.py::test_calculate_par_30_missing_columns PASSED       [ 51%]
tests/test_par_30.py::test_calculate_par_30_empty_df PASSED              [ 52%]
tests/test_par_90.py::test_calculate_par_90_standard PASSED              [ 52%]
tests/test_par_90.py::test_calculate_par_90_zero_receivable PASSED       [ 52%]
tests/test_par_90.py::test_calculate_par_90_missing_columns PASSED       [ 52%]
tests/test_par_90.py::test_calculate_par_90_empty_df PASSED              [ 52%]
tests/test_paths.py::TestProjectRoot::test_get_project_root_exists PASSED [ 53%]
tests/test_paths.py::TestProjectRoot::test_project_root_contains_config PASSED [ 53%]
tests/test_paths.py::TestResolvePath::test_resolve_absolute_path PASSED  [ 53%]
tests/test_paths.py::TestResolvePath::test_resolve_home_relative_path PASSED [ 53%]
tests/test_paths.py::TestResolvePath::test_resolve_with_environment_variable_precedence PASSED [ 54%]
tests/test_paths.py::TestResolvePath::test_resolve_creates_directories_when_requested PASSED [ 54%]
tests/test_paths.py::TestResolvePath::test_resolve_does_not_create_by_default PASSED [ 54%]
tests/test_paths.py::TestResolvePath::test_resolve_empty_path_raises_error PASSED [ 54%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_default PASSED [ 54%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_respects_env_var PASSED [ 55%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_respects_data_metrics_path_var PASSED [ 55%]
tests/test_paths.py::TestPathsMetricsDir::test_metrics_dir_creates_when_requested PASSED [ 55%]
tests/test_paths.py::TestPathsLogsDir::test_logs_dir_default PASSED      [ 55%]
tests/test_paths.py::TestPathsLogsDir::test_logs_dir_respects_env_var PASSED [ 55%]
tests/test_paths.py::TestPathsMonitoringLogsDir::test_monitoring_logs_dir_under_logs PASSED [ 56%]
tests/test_paths.py::TestPathsMonitoringLogsDir::test_monitoring_logs_dir_creates_nested_structure PASSED [ 56%]
tests/test_paths.py::TestPathsEnvironment::test_get_environment_defaults_to_development PASSED [ 56%]
tests/test_paths.py::TestPathsEnvironment::test_get_environment_respects_python_env PASSED [ 56%]
tests/test_pipeline.py::test_ingest_data PASSED                          [ 57%]
tests/test_pipeline.py::test_transform_data PASSED                       [ 57%]
tests/test_pipeline.py::test_pipeline_ingestion_and_transformation PASSED [ 57%]
tests/test_pipeline.py::test_ingest_with_custom_run_id PASSED            [ 57%]
tests/test_pipeline_integration.py::test_pipeline_with_valid_data PASSED [ 57%]
tests/test_pipeline_integration.py::test_pipeline_ingestion_with_invalid_numeric_column PASSED [ 58%]
tests/test_pipeline_integration.py::test_pipeline_transformation_with_valid_columns PASSED [ 58%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_defaults PASSED [ 58%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_validation PASSED [ 58%]
tests/test_pipeline_orchestrator.py::TestPipelineConfig::test_config_get_method PASSED [ 59%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_initialization PASSED [ 59%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_execute PASSED [ 59%]
tests/test_pipeline_orchestrator.py::TestUnifiedPipeline::test_pipeline_execute_with_looker_source PASSED [ 59%]
tests/test_pr_status.py::TestPRStatus::test_list_open_prs PASSED         [ 59%]
tests/test_pr_status.py::TestPRStatus::test_render_report_auth_failure PASSED [ 60%]
tests/test_pr_status.py::TestPRStatus::test_render_report_success PASSED [ 60%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_0_empty_repo PASSED [ 60%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_1_readme_only PASSED [ 60%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_2_basic_structure PASSED [ 61%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_3_docs_and_workflows PASSED [ 61%]
tests/test_repo_maturity_summary.py::TestRepoMaturitySummary::test_level_4_full_maturity PASSED [ 61%]
tests/test_requests_compat.py::test_check_cryptography_prerelease_and_none PASSED [ 61%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_failure PASSED [ 61%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_success PASSED [ 62%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_with_custom_config PASSED [ 62%]
tests/test_run_data_pipeline.py::TestRunDataPipeline::test_run_pipeline_with_error PASSED [ 62%]
tests/test_run_scoring.py::test_parse_args_minimal_required PASSED       [ 62%]
tests/test_run_scoring.py::test_parse_args_all_options PASSED            [ 62%]
tests/test_run_scoring.py::test_parse_args_requires_data PASSED          [ 63%]
tests/test_run_scoring.py::test_load_portfolio_file_exists PASSED        [ 63%]
tests/test_run_scoring.py::test_load_portfolio_file_not_found PASSED     [ 63%]
tests/test_run_scoring.py::test_load_portfolio_expands_user_path PASSED  [ 63%]
tests/test_run_scoring.py::test_summarize_results_prints_output PASSED   [ 64%]
tests/test_run_scoring.py::test_summarize_results_formats_numbers PASSED [ 64%]
tests/test_run_scoring.py::test_summarize_results_handles_strings PASSED [ 64%]
tests/test_run_scoring.py::test_main_full_flow_no_export PASSED          [ 64%]
tests/test_run_scoring.py::test_main_output_to_file PASSED               [ 64%]
tests/test_run_scoring.py::test_main_blob_export_requires_credentials PASSED [ 65%]
tests/test_run_scoring.py::test_main_blob_export_with_connection_string PASSED [ 65%]
tests/test_run_scoring.py::test_main_parses_custom_thresholds PASSED     [ 65%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_existing_secret PASSED [ 65%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_nonexistent_secret_returns_none PASSED [ 66%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_required_missing_secret_raises_error PASSED [ 66%]
tests/test_secrets_manager.py::TestSecretsManagerGet::test_get_with_default_value PASSED [ 66%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_required_only_missing PASSED [ 66%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_with_all_required_set PASSED [ 66%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_raises_on_missing_required PASSED [ 67%]
tests/test_secrets_manager.py::TestSecretsManagerValidate::test_validate_optional_keys PASSED [ 67%]
tests/test_secrets_manager.py::TestSecretsManagerGetAll::test_get_all_required_only PASSED [ 67%]
tests/test_secrets_manager.py::TestSecretsManagerGetAll::test_get_all_includes_optional PASSED [ 67%]
tests/test_secrets_manager.py::TestSecretsManagerFactory::test_get_secrets_manager_default PASSED [ 67%]
tests/test_secrets_manager.py::TestSecretsManagerFactory::test_get_secrets_manager_with_vault PASSED [ 68%]
tests/test_secrets_manager.py::TestSecretsManagerLogging::test_log_status_does_not_expose_values PASSED [ 68%]
tests/test_segmentation_summary.py::test_segmentation_summary_calculation PASSED [ 68%]
tests/test_segmentation_summary.py::test_segmentation_summary_empty PASSED [ 68%]
tests/test_standalone_ai.py::TestStandaloneAI::test_generate_response_offline PASSED [ 69%]
tests/test_standalone_ai.py::TestStandaloneAI::test_generate_response_online PASSED [ 69%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_routes_large_payload_to_gemini PASSED [ 69%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_routes_small_payload_to_grok PASSED [ 69%]
tests/test_standalone_ai_engine.py::TestStandaloneAIEngine::test_truncates_oversized_payload PASSED [ 69%]
tests/test_sync_kpi_table_to_figma.py::test_sync_success PASSED          [ 70%]
tests/test_sync_kpi_table_to_figma.py::test_page_not_found PASSED        [ 70%]
tests/test_sync_kpi_table_to_figma.py::test_get_request_failure PASSED   [ 70%]
tests/test_sync_kpi_table_to_figma.py::test_put_request_failure PASSED   [ 70%]
tests/test_tracing_setup.py::TestTracingSetup::test_enable_auto_instrumentation_does_not_raise PASSED [ 71%]
tests/test_tracing_setup.py::TestTracingSetup::test_get_tracer_returns_tracer PASSED [ 71%]
tests/test_tracing_setup.py::TestTracingSetup::test_init_tracing_returns_provider PASSED [ 71%]
tests/test_tracing_setup.py::TestTracingSetup::test_init_tracing_uses_env_endpoint PASSED [ 71%]
tests/test_transformation.py::test_transform_basic PASSED                [ 71%]
tests/test_transformation.py::test_transform_adds_tracking_columns PASSED [ 72%]
tests/test_transformation.py::test_transform_normalization PASSED        [ 72%]
tests/test_transformation.py::test_transform_preserves_row_count PASSED  [ 72%]
tests/test_transformation.py::test_transform_generates_lineage PASSED    [ 72%]
tests/test_transformation.py::test_transform_quality_checks PASSED       [ 72%]
tests/test_transformation.py::test_run_id_generation PASSED              [ 73%]
tests/test_transformation.py::test_custom_run_id PASSED                  [ 73%]
tests/test_transformation.py::test_transform_with_null_values PASSED     [ 73%]
tests/test_transformation.py::test_transform_error_handling PASSED       [ 73%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_ensure_token PASSED [ 74%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_ensure_token_missing PASSED [ 74%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_fetch_workflows PASSED [ 74%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_fetch_workflows_error PASSED [ 74%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_resolve_workflow_targets PASSED [ 74%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_trigger_workflow_failure PASSED [ 75%]
tests/test_trigger_workflows.py::TestTriggerWorkflows::test_trigger_workflow_success PASSED [ 75%]
tests/test_update_playwright.py::test_update_playwright_invokes_gh_api_and_writes_fixed_file PASSED [ 75%]
tests/test_update_playwright_idempotency.py::test_safe_replace_on_key_is_idempotent PASSED [ 75%]
tests/test_update_playwright_idempotency.py::test_fix_content_returns_replacements_count PASSED [ 76%]
tests/test_update_playwright_integration.py::test_integration_replaces_only_top_level_key_and_invokes_gh PASSED [ 76%]
tests/test_update_playwright_integration.py::test_integration_no_top_level_change_does_not_call_gh PASSED [ 76%]
tests/test_update_playwright_safe.py::test_safe_replace_on_key_replaces_top_level_key PASSED [ 76%]
tests/test_update_playwright_safe.py::test_safe_replace_on_key_ignores_values_and_strings PASSED [ 76%]
tests/test_validation.py::test_validate_dataframe_valid PASSED           [ 77%]
tests/test_validation.py::test_validate_dataframe_missing_amount_column PASSED [ 77%]
tests/test_validation.py::test_validate_dataframe_non_float_amount PASSED [ 77%]
tests/test_validation.py::test_validate_dataframe_string_amount PASSED   [ 77%]
tests/test_validation.py::test_validate_dataframe_empty PASSED           [ 77%]
tests/test_validation.py::test_validate_dataframe_with_nan PASSED        [ 78%]
tests/test_validation.py::test_validation_constants_integrity PASSED     [ 78%]
tests/test_validation.py::test_analytics_numeric_columns_subset PASSED   [ 78%]
tests/test_validation.py::test_validate_numeric_bounds PASSED            [ 78%]
tests/test_validation.py::test_find_column_logic PASSED                  [ 79%]
tests/test_validation.py::test_validate_dataframe_missing_multiple_columns PASSED [ 79%]
tests/test_validation.py::test_find_column_edge_cases PASSED             [ 79%]
tests/test_validation.py::test_safe_numeric_empty PASSED                 [ 79%]
tests/test_validation.py::test_validate_percentage_bounds PASSED         [ 79%]
tests/test_validation.py::test_validate_iso8601_dates PASSED             [ 80%]
tests/test_validation.py::test_data_quality_report_passed PASSED         [ 80%]
tests/test_validation.py::test_data_quality_report_failed_missing_column PASSED [ 80%]
tests/test_validation.py::test_data_quality_report_type_error PASSED     [ 80%]
tests/test_validation.py::test_iban_validation PASSED                    [ 81%]
tests/test_validation.py::test_iban_validation_cleaning PASSED           [ 81%]
tests/unit/test___init___stub.py::test_placeholder PASSED                [ 81%]
tests/unit/test__is_valid_iso8601_stub.py::test_placeholder PASSED       [ 81%]
tests/unit/test_abaco_kpi_calculator.py::test_calculator_init PASSED     [ 81%]
tests/unit/test_abaco_kpi_calculator.py::test_aum_by_customer_type PASSED [ 82%]
tests/unit/test_abaco_pipeline_cli_write_audit.py::test_write_audit_dry_run_prints_enriched_payload PASSED [ 82%]
tests/unit/test_abaco_pipeline_cli_write_audit.py::test_write_audit_writes_to_supabase PASSED [ 82%]
tests/unit/test_abaco_pipeline_output.py::test_write_manifest_writes_json PASSED [ 82%]
tests/unit/test_abaco_pipeline_quality.py::test_compute_freshness_hours_zero_when_same_time PASSED [ 83%]
tests/unit/test_abaco_pipeline_quality.py::test_compute_freshness_hours_positive_delta PASSED [ 83%]
tests/unit/test_abaco_pipeline_supabase_writer.py::test_upsert_pipeline_run_posts_expected_url_headers_and_body PASSED [ 83%]
tests/unit/test_abaco_pipeline_supabase_writer.py::test_insert_kpi_values_noop_on_empty PASSED [ 83%]
tests/unit/test_agent_output_storage_stub.py::test_placeholder PASSED    [ 83%]
tests/unit/test_agent_stub.py::test_placeholder PASSED                   [ 84%]
tests/unit/test_analytics_metrics_stub.py::test_placeholder PASSED       [ 84%]
tests/unit/test_archive_stub.py::test_placeholder PASSED                 [ 84%]
tests/unit/test_azure_monitor_stub.py::test_placeholder PASSED           [ 84%]
tests/unit/test_azure_outputs_stub.py::test_placeholder PASSED           [ 84%]
tests/unit/test_batch_export_runner_stub.py::test_placeholder PASSED     [ 85%]
tests/unit/test_brand_agent_stub.py::test_placeholder PASSED             [ 85%]
tests/unit/test_builtins_stub.py::test_placeholder PASSED                [ 85%]
tests/unit/test_business_rules_stub.py::test_placeholder PASSED          [ 85%]
tests/unit/test_c_suite_agent_stub.py::test_placeholder PASSED           [ 86%]
tests/unit/test_cascade_client_stub.py::test_placeholder PASSED          [ 86%]
tests/unit/test_cascade_stub.py::test_placeholder PASSED                 [ 86%]
tests/unit/test_churn_rate_stub.py::test_placeholder PASSED              [ 86%]
tests/unit/test_compliance_stub.py::test_placeholder PASSED              [ 86%]
tests/unit/test_customer_agent_stub.py::test_placeholder PASSED          [ 87%]
tests/unit/test_data_transformation_stub.py::test_placeholder PASSED     [ 87%]
tests/unit/test_data_validation_gx_stub.py::test_placeholder PASSED      [ 87%]
tests/unit/test_date_utils_stub.py::test_placeholder PASSED              [ 87%]
tests/unit/test_endpoints_stub.py::test_placeholder PASSED               [ 88%]
tests/unit/test_feature_engineering_stub.py::test_placeholder PASSED     [ 88%]
tests/unit/test_figma_client_stub.py::test_placeholder PASSED            [ 88%]
tests/unit/test_financial_agent_stub.py::test_placeholder PASSED         [ 88%]
tests/unit/test_financial_analysis_stub.py::test_placeholder PASSED      [ 88%]
tests/unit/test_gates_stub.py::test_placeholder PASSED                   [ 89%]
tests/unit/test_growth_agent_stub.py::test_placeholder PASSED            [ 89%]
tests/unit/test_ingest_init.py::test_dataloader_import PASSED            [ 89%]
tests/unit/test_ingest_init.py::test_transformer_import PASSED           [ 89%]
tests/unit/test_ingest_init.py::test_canonicalize_loan_tape PASSED       [ 89%]
tests/unit/test_ingestion_extended.py::test_ingest_dataframe PASSED      [ 90%]
tests/unit/test_ingestion_extended.py::test_validate_loans PASSED        [ 90%]
tests/unit/test_ingestion_extended.py::test_get_ingest_summary PASSED    [ 90%]
tests/unit/test_ingestion_extended.py::test_ingest_parquet_failure PASSED [ 90%]
tests/unit/test_ingestion_extended.py::test_ingest_excel_failure PASSED  [ 91%]
tests/unit/test_init_gx_stub.py::test_placeholder PASSED                 [ 91%]
tests/unit/test_investor_agent_stub.py::test_placeholder PASSED          [ 91%]
tests/unit/test_kpi_calculation_stub.py::test_placeholder PASSED         [ 91%]
tests/unit/test_kpi_calculator_complete_stub.py::test_placeholder PASSED [ 91%]
tests/unit/test_kpi_catalog_processor_stub.py::test_placeholder PASSED   [ 92%]
tests/unit/test_kpis_stub.py::test_placeholder PASSED                    [ 92%]
tests/unit/test_kri_calculator_stub.py::test_placeholder PASSED          [ 92%]
tests/unit/test_llm_provider_stub.py::test_placeholder PASSED            [ 92%]
tests/unit/test_main_stub.py::test_placeholder PASSED                    [ 93%]
tests/unit/test_market_agent_stub.py::test_placeholder PASSED            [ 93%]
tests/unit/test_meta_agent_analysis_stub.py::test_placeholder PASSED     [ 93%]
tests/unit/test_meta_client_stub.py::test_placeholder PASSED             [ 93%]
tests/unit/test_normalize_stub.py::test_placeholder PASSED               [ 93%]
tests/unit/test_notion_client_stub.py::test_placeholder PASSED           [ 94%]
tests/unit/test_ops_agent_stub.py::test_placeholder PASSED               [ 94%]
tests/unit/test_orchestrator_stub.py::test_orchestrator_workflow_execution PASSED [ 94%]
tests/unit/test_output_storage_stub.py::test_placeholder PASSED          [ 94%]
tests/unit/test_outputs_stub.py::test_placeholder PASSED                 [ 94%]
tests/unit/test_prefect_orchestrator_stub.py::test_placeholder PASSED    [ 95%]
tests/unit/test_product_agent_stub.py::test_placeholder PASSED           [ 95%]
tests/unit/test_quality_score_stub.py::test_placeholder PASSED           [ 95%]
tests/unit/test_recurrence_stub.py::test_placeholder PASSED              [ 95%]
tests/unit/test_registry_stub.py::test_placeholder PASSED                [ 96%]
tests/unit/test_requests_fix_stub.py::test_placeholder PASSED            [ 96%]
tests/unit/test_risk_agent_stub.py::test_placeholder PASSED              [ 96%]
tests/unit/test_run_pipeline_stub.py::test_placeholder PASSED            [ 96%]
tests/unit/test_sales_agent_stub.py::test_placeholder PASSED             [ 96%]
tests/unit/test_settings_stub.py::test_placeholder PASSED                [ 97%]
tests/unit/test_setup_stub.py::test_placeholder PASSED                   [ 97%]
tests/unit/test_supabase_client_stub.py::test_placeholder PASSED         [ 97%]
tests/unit/test_talent_agent_stub.py::test_placeholder PASSED            [ 97%]
tests/unit/test_theme_stub.py::test_placeholder PASSED                   [ 98%]
tests/unit/test_to_frames_stub.py::test_placeholder PASSED               [ 98%]
tests/unit/test_tools_stub.py::test_placeholder PASSED                   [ 98%]
tests/unit/test_tracing_setup_stub.py::test_placeholder PASSED           [ 98%]
tests/unit/test_tracing_stub.py::test_placeholder PASSED                 [ 98%]
tests/unit/test_unified_output_manager_stub.py::test_placeholder PASSED  [ 99%]
tests/unit/test_validate_kpi_formulas_stub.py::test_placeholder PASSED   [ 99%]
tests/unit/test_validation_extended.py::test_is_valid_iban_fallback_logic PASSED [ 99%]
tests/unit/test_validation_extended.py::test_validate_iban_edge_cases PASSED [ 99%]
tests/unit/test_writers_stub.py::test_placeholder PASSED                 [100%]

=============================== warnings summary ===============================
../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:19
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:19: DeprecationWarning: 'setName' deprecated - use 'set_name'
    token = pp.Word(tchar).setName("token")

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20: DeprecationWarning: 'leaveWhitespace' deprecated - use 'leave_whitespace'
    token68 = pp.Combine(pp.Word("-._~+/" + pp.nums + pp.alphas) + pp.Optional(pp.Word("=").leaveWhitespace())).setName(

../../Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/httplib2/auth.py:20: DeprecationWarning: 'setName' deprecated - use 'set_name'
    token68 = pp.Combine(pp.Word("-._~+/" + pp.nums + pp.alphas) + pp.Optional(pp.Word("=").leaveWhitespace())).setName(

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

../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:64
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:64: DeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85: DeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89: DeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../Library/Python/3.9/lib/python/site-packages/matplotlib/_mathtext.py:45
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/matplotlib/_mathtext.py:45: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:72
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:72: DeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85: DeprecationWarning: 'escChar' argument is deprecated, use 'esc_char'
    quoted_identifier = QuotedString('"', escChar="\\", unquoteResults=True)

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/expressions/parser.py:85: DeprecationWarning: 'unquoteResults' argument is deprecated, use 'unquote_results'
    quoted_identifier = QuotedString('"', escChar="\\", unquoteResults=True)

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:366
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:366: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def construct_refs(cls, data: TableMetadataV1) -> TableMetadataV1:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:495
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:495: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_schemas(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:499
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:499: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_partition_specs(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:503
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:503: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_sort_orders(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:507
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:507: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def construct_refs(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:539
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:539: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_schemas(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:543
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:543: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_partition_specs(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:547
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:547: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def check_sort_orders(cls, table_metadata: TableMetadata) -> TableMetadata:

../../Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:551
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pyiceberg/table/metadata.py:551: PydanticDeprecatedSince212: Using `@model_validator` with mode='after' on a classmethod is deprecated. Instead, use an instance method. See the documentation at https://docs.pydantic.dev/2.12/concepts/validators/#model-after-validator. Deprecated in Pydantic V2.12 to be removed in V3.0.
    def construct_refs(cls, table_metadata: TableMetadata) -> TableMetadata:

tests/fi-analytics/test_analytics_integration.py::TestAnalyticsIntegration::test_d01_otlp_span_generation
  /Users/jenineferderas/Library/Python/3.9/lib/python/site-packages/pandera/_pandas_deprecated.py:160: FutureWarning: Importing pandas-specific classes and functions from the
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

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========== 449 passed, 13 skipped, 36 warnings in 146.06s (0:02:26) ===========

**Result**: ✓ PASSED

## 4. LINTING CHECKS
### Pylint
************* Module src.pipeline.data_ingestion
src/pipeline/data_ingestion.py:69:12: W0101: Unreachable code (unreachable)
************* Module src.abaco_pipeline.quality.gates
src/abaco_pipeline/quality/gates.py:49:0: R0911: Too many return statements (7/6) (too-many-return-statements)

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)


### Flake8

### Ruff
All checks passed!

## 5. TYPE CHECKING
### mypy
Success: no issues found in 137 source files

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
