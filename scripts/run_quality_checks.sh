#!/bin/bash
# Code Quality Analysis Runner
# Runs all configured code quality tools and generates a comprehensive report

set -e  # Exit on error

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Code Quality Analysis Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Track overall status
OVERALL_STATUS=0

# Function to print section header
print_header() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo "----------------------------------------"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 1. Pylint (Python)
print_header "Running Pylint (Python)"
if [ -d "python" ] || [ -d "apps/analytics" ]; then
    if command -v pylint &> /dev/null; then
        echo "Analyzing Python code..."
        if pylint --rcfile=.pylintrc --exit-zero python/ apps/analytics/src 2>/dev/null | tee pylint_output.txt; then
            SCORE=$(grep "Your code has been rated" pylint_output.txt | sed 's/.*rated at \([0-9.]*\).*/\1/' || echo "0")
            if [ -z "$SCORE" ]; then
                SCORE="0"
            fi
            echo "Pylint Score: $SCORE/10"
            if (( $(echo "$SCORE >= 9.0" | bc -l) )); then
                print_success "Pylint passed with excellent score: $SCORE/10"
            elif (( $(echo "$SCORE >= 8.5" | bc -l) )); then
                print_warning "Pylint passed with good score: $SCORE/10"
            else
                print_error "Pylint score below threshold: $SCORE/10 (minimum: 8.5)"
                OVERALL_STATUS=1
            fi
        else
            print_error "Pylint analysis failed"
            OVERALL_STATUS=1
        fi
        rm -f pylint_output.txt
    else
        print_warning "Pylint not installed. Run: pip install pylint"
        OVERALL_STATUS=1
    fi
else
    print_warning "No Python directories found"
fi

# 2. ESLint (TypeScript/JavaScript)
print_header "Running ESLint (TypeScript/JavaScript)"
if [ -d "apps/web" ]; then
    echo "Analyzing TypeScript/JavaScript code..."
    cd apps/web
    if [ -f "package.json" ]; then
        if npm run lint 2>&1 | tee ../../eslint_output.txt; then
            print_success "ESLint passed"
        else
            print_error "ESLint found issues"
            OVERALL_STATUS=1
        fi
        rm -f ../../eslint_output.txt
    else
        print_warning "No package.json found in apps/web"
    fi
    cd "$REPO_ROOT"
else
    print_warning "No apps/web directory found"
fi

# 3. TypeScript Type Check
print_header "Running TypeScript Type Check"
if [ -d "apps/web" ]; then
    echo "Type checking TypeScript code..."
    cd apps/web
    if npm run type-check 2>&1; then
        print_success "TypeScript type check passed"
    else
        print_error "TypeScript type check failed"
        OVERALL_STATUS=1
    fi
    cd "$REPO_ROOT"
fi

# 4. Python Tests with Coverage
print_header "Running Python Tests with Coverage"
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    if command -v pytest &> /dev/null; then
        echo "Running Python tests..."
        if pytest --cov=python --cov-report=term-missing --cov-report=xml:coverage-python.xml -q; then
            print_success "Python tests passed"
            
            # Check coverage
            if command -v coverage &> /dev/null; then
                COVERAGE=$(coverage report | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
                if [ ! -z "$COVERAGE" ]; then
                    echo "Coverage: $COVERAGE%"
                    if (( $(echo "$COVERAGE >= 85.0" | bc -l) )); then
                        print_success "Coverage exceeds target: $COVERAGE% (target: 85%)"
                    elif (( $(echo "$COVERAGE >= 40.0" | bc -l) )); then
                        print_warning "Coverage meets minimum: $COVERAGE% (target: 85%)"
                    else
                        print_error "Coverage below minimum: $COVERAGE% (minimum: 40%)"
                        OVERALL_STATUS=1
                    fi
                fi
            fi
        else
            print_error "Python tests failed"
            OVERALL_STATUS=1
        fi
    else
        print_warning "pytest not installed. Run: pip install pytest pytest-cov"
    fi
else
    print_warning "No pytest configuration found"
fi

# 5. Black (Python formatting check)
print_header "Checking Python Code Formatting (Black)"
if [ -d "python" ]; then
    if command -v black &> /dev/null; then
        echo "Checking Python code formatting..."
        if black --check python/ tests/ 2>&1; then
            print_success "Python code is properly formatted"
        else
            print_warning "Python code needs formatting. Run: black python/ tests/"
            OVERALL_STATUS=1
        fi
    else
        print_warning "black not installed. Run: pip install black"
    fi
fi

# 6. isort (Python import sorting check)
print_header "Checking Python Import Sorting (isort)"
if [ -d "python" ]; then
    if command -v isort &> /dev/null; then
        echo "Checking Python import sorting..."
        if isort --check-only python/ tests/ 2>&1; then
            print_success "Python imports are properly sorted"
        else
            print_warning "Python imports need sorting. Run: isort python/ tests/"
            OVERALL_STATUS=1
        fi
    else
        print_warning "isort not installed. Run: pip install isort"
    fi
fi

# 7. Pre-commit hooks check
print_header "Pre-commit Hooks Status"
if [ -f ".pre-commit-config.yaml" ]; then
    if command -v pre-commit &> /dev/null; then
        if [ -d ".git/hooks" ] && [ -f ".git/hooks/pre-commit" ]; then
            print_success "Pre-commit hooks are installed"
        else
            print_warning "Pre-commit hooks not installed. Run: pre-commit install"
        fi
    else
        print_warning "pre-commit not installed. Run: pip install pre-commit"
    fi
else
    print_warning "No .pre-commit-config.yaml found"
fi

# 8. Code Climate validation
print_header "Code Climate Configuration"
if [ -f ".codeclimate.yml" ]; then
    print_success "Code Climate configuration exists (.codeclimate.yml)"
    echo "To analyze with Code Climate:"
    echo "  1. Visit https://codeclimate.com/"
    echo "  2. Connect your GitHub repository"
    echo "  3. Or install CLI: brew install codeclimate/formulae/codeclimate"
    echo "  4. Run: codeclimate analyze"
else
    print_warning "No .codeclimate.yml found"
fi

# 9. SonarQube configuration
print_header "SonarQube Configuration"
if [ -f "sonar-project.properties" ]; then
    print_success "SonarQube configuration exists (sonar-project.properties)"
    echo "SonarQube runs automatically in CI on main branch"
    echo "View reports at: https://sonarcloud.io/organizations/abaco-fintech"
else
    print_warning "No sonar-project.properties found"
fi

# Summary
echo ""
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}=================================${NC}"

if [ $OVERALL_STATUS -eq 0 ]; then
    print_success "All code quality checks passed! 🎉"
    echo ""
    echo "Next steps:"
    echo "  1. Commit your changes: git commit -m 'Your message'"
    echo "  2. Push to GitHub: git push"
    echo "  3. CI will run all checks automatically"
else
    print_error "Some code quality checks failed."
    echo ""
    echo "Please fix the issues above before committing."
    echo ""
    echo "Quick fixes:"
    echo "  - Format Python: black python/ tests/"
    echo "  - Sort imports: isort python/ tests/"
    echo "  - Fix ESLint: cd apps/web && npm run lint:fix"
    echo "  - Run tests: pytest"
fi

echo ""
exit $OVERALL_STATUS
