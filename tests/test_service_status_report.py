import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from scripts.maintenance.generate_service_status_report import ServiceStatusChecker, generate_markdown_report

class TestServiceStatusChecker:

    def test_init(self):
        checker = ServiceStatusChecker()
        assert checker.results == {}
        assert isinstance(checker.repo_root, Path)

    def test_run_command_success(self):
        checker = ServiceStatusChecker()
        success, stdout, stderr = checker.run_command([sys.executable, '-c', 'import sys; sys.stdout.write("test")'])
        assert success is True
        assert 'test' in stdout
        assert stderr == ''

    def test_run_command_failure(self):
        checker = ServiceStatusChecker()
        success, stdout, stderr = checker.run_command([sys.executable, '-c', 'import sys; sys.exit(1)'])
        assert success is False

    def test_check_git_status_success(self):
        checker = ServiceStatusChecker()
        result = checker.check_git_status()
        assert 'name' in result
        assert result['name'] == 'Git Repository'
        assert 'success' in result
        assert 'details' in result

    def test_check_git_status_excludes_report_files(self):
        checker = ServiceStatusChecker()

        def mock_run_command(cmd, timeout=30):
            if 'status' in cmd and '--porcelain' in cmd:
                return (True, 'M service_status_report.md\nM service_status_report.json\nM other_file.py\n', '')
            return (True, 'main\n', '')
        checker.run_command = mock_run_command
        result = checker.check_git_status()
        assert result['details']['uncommitted_changes'] is True

    def test_check_python_environment(self):
        checker = ServiceStatusChecker()
        result = checker.check_python_environment()
        assert result['name'] == 'Python Environment'
        assert 'python_version' in result['details']
        assert 'virtual_env_active' in result['details']
        assert 'packages' in result['details']

    def test_check_supabase_configuration_missing_url(self):
        checker = ServiceStatusChecker()
        with patch.dict('os.environ', {}, clear=True):
            result = checker.check_supabase_configuration()
        assert result['success'] is False
        assert 'url_configured' in result['details']
        assert result['details']['url_configured'] is False
        assert 'SUPABASE_URL not configured' in result['details']['message']

    def test_check_supabase_configuration_missing_key(self):
        checker = ServiceStatusChecker()
        with patch.dict('os.environ', {'SUPABASE_URL': 'http://example.com'}, clear=True):
            result = checker.check_supabase_configuration()
        assert result['success'] is False
        assert result['details']['url_configured'] is True
        assert result['details']['key_configured'] is False
        assert 'key missing' in result['details']['message']

    def test_check_supabase_configuration_complete(self):
        checker = ServiceStatusChecker()
        with patch.dict('os.environ', {'SUPABASE_URL': 'http://example.com', 'SUPABASE_ANON_KEY': 'test-key'}, clear=True):
            result = checker.check_supabase_configuration()
        assert result['success'] is True
        assert result['details']['url_configured'] is True
        assert result['details']['key_configured'] is True
        assert 'Configuration complete' in result['details']['message']

    def test_check_pipeline(self):
        checker = ServiceStatusChecker()
        result = checker.check_pipeline()
        assert result['name'] == 'Data Pipeline'
        assert 'script_exists' in result['details']
        assert 'config_exists' in result['details']
        assert 'modules' in result['details']

    def test_run_all_checks_continues_on_error(self):
        checker = ServiceStatusChecker()

        def failing_check():
            raise ValueError('Test error')
        checker.check_git_status = failing_check
        with patch.object(checker, 'run_command', return_value=(True, '', '')):
            results = checker.run_all_checks()
        assert 'git' in results
        assert results['git']['success'] is False
        assert 'error' in results['git']['details']
        assert len(results) == 9

class TestGenerateMarkdownReport:

    def test_generate_markdown_report_empty_results(self):
        report = generate_markdown_report({})
        assert '# Service Status Report' in report
        assert '0/0 checks passed' in report

    def test_generate_markdown_report_all_passing(self):
        results = {'test1': {'name': 'Test Component 1', 'success': True, 'details': {'key': 'value'}}, 'test2': {'name': 'Test Component 2', 'success': True, 'details': {}}}
        report = generate_markdown_report(results)
        assert '# Service Status Report' in report
        assert '2/2 checks passed' in report
        assert '✅ Test Component 1' in report
        assert '✅ Test Component 2' in report
        assert 'No actions required' in report

    def test_generate_markdown_report_some_failing(self):
        results = {'passing': {'name': 'Passing Check', 'success': True, 'details': {}}, 'failing': {'name': 'Failing Check', 'success': False, 'details': {'error': 'Something went wrong'}}}
        report = generate_markdown_report(results)
        assert '1/2 checks passed' in report
        assert '✅ Passing Check' in report
        assert '❌ Failing Check' in report
        assert 'Failing Check' in report
        assert '❌ **Critical**' in report

    def test_generate_markdown_report_boolean_rendering(self):
        results = {'test': {'name': 'Test', 'success': True, 'details': {'boolean_true': True, 'boolean_false': False}}}
        report = generate_markdown_report(results)
        assert '**Boolean True:** Yes' in report
        assert '**Boolean False:** No' in report

    def test_generate_markdown_report_dict_values(self):
        results = {'test': {'name': 'Test', 'success': True, 'details': {'packages': {'pandas': '✅ Installed', 'numpy': '❌ Not installed'}}}}
        report = generate_markdown_report(results)
        assert '**Packages:**' in report
        assert 'pandas: ✅ Installed' in report
        assert 'numpy: ❌ Not installed' in report

    def test_generate_markdown_report_utf8_characters(self):
        results = {'test': {'name': 'Test Component', 'success': True, 'details': {}}}
        report = generate_markdown_report(results)
        assert '✅' in report

class TestEdgeCases:

    def test_check_with_no_git(self):
        checker = ServiceStatusChecker()

        def mock_run_command(cmd, timeout=30):
            return (False, '', 'git: command not found')
        checker.run_command = mock_run_command
        result = checker.check_git_status()
        assert result['success'] is False
        assert 'error' in str(result['details']).lower()

    def test_todo_count_with_unreadable_files(self):
        checker = ServiceStatusChecker()
        checker.run_command = MagicMock(return_value=(True, '', ''))
        result = checker.check_linting()
        assert 'active_todos' in result['details']
        assert isinstance(result['details']['active_todos'], str)

    def test_check_tests_missing_directory(self):
        checker = ServiceStatusChecker()
        checker.repo_root = Path('/nonexistent/path')
        result = checker.check_tests()
        assert result['success'] is False
        assert any((key in result['details'] for key in ('result_summary', 'exit_code')))
