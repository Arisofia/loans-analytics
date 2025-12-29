#!/bin/bash

##############################################################################
# GitHub Secrets Setup Script
# Version: 2.0
# Date: 2025-12-26
# Purpose: Interactive setup of GitHub repository secrets for CI/CD pipeline
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
REPO_OWNER=$(git config --get remote.origin.url | sed -E 's/.*[:/]([^/]+)\/([^/]+)\.git/\1/')

# Required secrets
REQUIRED_STAGING_SECRETS=(
  "STAGING_SUPABASE_URL"
  "STAGING_SUPABASE_KEY"
  "AZURE_STATIC_WEB_APPS_TOKEN_STAGING"
)

REQUIRED_PROD_SECRETS=(
  "PROD_SUPABASE_URL"
  "PROD_SUPABASE_KEY"
  "PROD_SENTRY_DSN"
  "AZURE_STATIC_WEB_APPS_TOKEN_PROD"
)

##############################################################################
# Functions
##############################################################################

print_header() {
  echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║${NC} $1"
  echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_section() {
  echo -e "\n${YELLOW}━━━ $1 ━━━${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

verify_repo() {
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not a git repository"
    exit 1
  fi
  print_success "Git repository verified"
}

verify_gh_cli() {
  if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) not installed"
    echo ""
    echo "Install GitHub CLI:"
    echo "  macOS: brew install gh"
    echo "  Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  Windows: choco install gh"
    exit 1
  fi
  print_success "GitHub CLI installed"
}

verify_gh_auth() {
  if ! gh auth status > /dev/null 2>&1; then
    print_error "Not authenticated with GitHub CLI"
    echo ""
    echo "Run: gh auth login"
    exit 1
  fi
  print_success "GitHub CLI authenticated"
}

get_repo_info() {
  print_section "Repository Information"
  
  if [ -z "$REPO_OWNER" ] || [ "$REPO_OWNER" == "origin" ]; then
    echo -e "${YELLOW}Enter your GitHub username/organization:${NC}"
    read -p "> " REPO_OWNER
  fi
  
  REPO_URL="$REPO_OWNER/$REPO_NAME"
  print_info "Repository: $REPO_URL"
  
  read -p "Is this correct? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Exiting setup"
    exit 1
  fi
  
  print_success "Repository confirmed: $REPO_URL"
}

print_secret_info() {
  local secret_name=$1
  local source=$2
  local instructions=$3
  
  echo -e "\n${BLUE}Secret: ${YELLOW}$secret_name${NC}"
  echo "Source: $source"
  echo "Instructions:"
  echo "$instructions"
}

get_staging_secrets() {
  print_section "Staging Environment Secrets"
  
  echo "You need to provide 3 secrets for staging environment:"
  echo ""
  
  # STAGING_SUPABASE_URL
  print_secret_info "STAGING_SUPABASE_URL" "Supabase Dashboard" \
    "1. Go to https://supabase.com/dashboard
2. Select your staging project
3. Click 'Settings' → 'API'
4. Copy the 'Project URL' (looks like: https://xxx.supabase.co)
5. Paste below"
  
  read -p "Enter STAGING_SUPABASE_URL: " STAGING_SUPABASE_URL
  if [ -z "$STAGING_SUPABASE_URL" ]; then
    print_error "STAGING_SUPABASE_URL cannot be empty"
    return 1
  fi
  print_success "STAGING_SUPABASE_URL set"
  
  # STAGING_SUPABASE_KEY
  print_secret_info "STAGING_SUPABASE_KEY" "Supabase Dashboard" \
    "1. Same as above: Settings → API
2. Copy the 'anon public' key (not the service_role key)
3. Paste below"
  
  read -sp "Enter STAGING_SUPABASE_KEY: " STAGING_SUPABASE_KEY
  echo ""
  if [ -z "$STAGING_SUPABASE_KEY" ]; then
    print_error "STAGING_SUPABASE_KEY cannot be empty"
    return 1
  fi
  print_success "STAGING_SUPABASE_KEY set (hidden)"
  
  # AZURE_STATIC_WEB_APPS_TOKEN_STAGING
  print_secret_info "AZURE_STATIC_WEB_APPS_TOKEN_STAGING" "Azure Portal" \
    "1. Go to https://portal.azure.com
2. Find your Static Web App (staging)
3. Click 'Manage deployment token'
4. Copy the deployment token
5. Paste below"
  
  read -sp "Enter AZURE_STATIC_WEB_APPS_TOKEN_STAGING: " AZURE_STATIC_WEB_APPS_TOKEN_STAGING
  echo ""
  if [ -z "$AZURE_STATIC_WEB_APPS_TOKEN_STAGING" ]; then
    print_error "AZURE_STATIC_WEB_APPS_TOKEN_STAGING cannot be empty"
    return 1
  fi
  print_success "AZURE_STATIC_WEB_APPS_TOKEN_STAGING set (hidden)"
}

get_production_secrets() {
  print_section "Production Environment Secrets"
  
  echo "You need to provide 4 secrets for production environment:"
  echo ""
  
  # PROD_SUPABASE_URL
  print_secret_info "PROD_SUPABASE_URL" "Supabase Dashboard" \
    "1. Go to https://supabase.com/dashboard
2. Select your production project
3. Click 'Settings' → 'API'
4. Copy the 'Project URL'
5. Paste below"
  
  read -p "Enter PROD_SUPABASE_URL: " PROD_SUPABASE_URL
  if [ -z "$PROD_SUPABASE_URL" ]; then
    print_error "PROD_SUPABASE_URL cannot be empty"
    return 1
  fi
  print_success "PROD_SUPABASE_URL set"
  
  # PROD_SUPABASE_KEY
  print_secret_info "PROD_SUPABASE_KEY" "Supabase Dashboard" \
    "1. Same as above: Settings → API
2. Copy the 'anon public' key
3. Paste below"
  
  read -sp "Enter PROD_SUPABASE_KEY: " PROD_SUPABASE_KEY
  echo ""
  if [ -z "$PROD_SUPABASE_KEY" ]; then
    print_error "PROD_SUPABASE_KEY cannot be empty"
    return 1
  fi
  print_success "PROD_SUPABASE_KEY set (hidden)"
  
  # PROD_SENTRY_DSN
  print_secret_info "PROD_SENTRY_DSN" "Sentry Dashboard" \
    "1. Go to https://sentry.io/organizations/
2. Select your organization and project
3. Click 'Settings' → 'Client Keys (DSN)'
4. Copy the DSN (looks like: https://xxx@xxx.ingest.sentry.io/xxx)
5. Paste below"
  
  read -sp "Enter PROD_SENTRY_DSN: " PROD_SENTRY_DSN
  echo ""
  if [ -z "$PROD_SENTRY_DSN" ]; then
    print_error "PROD_SENTRY_DSN cannot be empty"
    return 1
  fi
  print_success "PROD_SENTRY_DSN set (hidden)"
  
  # AZURE_STATIC_WEB_APPS_TOKEN_PROD
  print_secret_info "AZURE_STATIC_WEB_APPS_TOKEN_PROD" "Azure Portal" \
    "1. Go to https://portal.azure.com
2. Find your Static Web App (production)
3. Click 'Manage deployment token'
4. Copy the deployment token
5. Paste below"
  
  read -sp "Enter AZURE_STATIC_WEB_APPS_TOKEN_PROD: " AZURE_STATIC_WEB_APPS_TOKEN_PROD
  echo ""
  if [ -z "$AZURE_STATIC_WEB_APPS_TOKEN_PROD" ]; then
    print_error "AZURE_STATIC_WEB_APPS_TOKEN_PROD cannot be empty"
    return 1
  fi
  print_success "AZURE_STATIC_WEB_APPS_TOKEN_PROD set (hidden)"
}

create_secrets() {
  print_section "Creating GitHub Secrets"
  
  echo "This will create the following secrets in GitHub:"
  echo ""
  echo "Staging:"
  for secret in "${REQUIRED_STAGING_SECRETS[@]}"; do
    echo "  - $secret"
  done
  echo ""
  echo "Production:"
  for secret in "${REQUIRED_PROD_SECRETS[@]}"; do
    echo "  - $secret"
  done
  echo ""
  
  read -p "Continue? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Aborted - secrets not created"
    return 1
  fi
  
  # Create staging secrets
  print_info "Creating staging secrets..."
  
  gh secret set STAGING_SUPABASE_URL --body "$STAGING_SUPABASE_URL" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "STAGING_SUPABASE_URL created"
  
  gh secret set STAGING_SUPABASE_KEY --body "$STAGING_SUPABASE_KEY" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "STAGING_SUPABASE_KEY created"
  
  gh secret set AZURE_STATIC_WEB_APPS_TOKEN_STAGING --body "$AZURE_STATIC_WEB_APPS_TOKEN_STAGING" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "AZURE_STATIC_WEB_APPS_TOKEN_STAGING created"
  
  # Create production secrets
  print_info "Creating production secrets..."
  
  gh secret set PROD_SUPABASE_URL --body "$PROD_SUPABASE_URL" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "PROD_SUPABASE_URL created"
  
  gh secret set PROD_SUPABASE_KEY --body "$PROD_SUPABASE_KEY" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "PROD_SUPABASE_KEY created"
  
  gh secret set PROD_SENTRY_DSN --body "$PROD_SENTRY_DSN" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "PROD_SENTRY_DSN created"
  
  gh secret set AZURE_STATIC_WEB_APPS_TOKEN_PROD --body "$AZURE_STATIC_WEB_APPS_TOKEN_PROD" -R "$REPO_OWNER/$REPO_NAME" && \
    print_success "AZURE_STATIC_WEB_APPS_TOKEN_PROD created"
}

verify_secrets() {
  print_section "Verifying Secrets"
  
  echo "Checking secrets in GitHub..."
  echo ""
  
  all_created=true
  
  for secret in "${REQUIRED_STAGING_SECRETS[@]}"; do
    if gh secret list -R "$REPO_OWNER/$REPO_NAME" | grep -q "$secret"; then
      print_success "$secret"
    else
      print_error "$secret (not found)"
      all_created=false
    fi
  done
  
  for secret in "${REQUIRED_PROD_SECRETS[@]}"; do
    if gh secret list -R "$REPO_OWNER/$REPO_NAME" | grep -q "$secret"; then
      print_success "$secret"
    else
      print_error "$secret (not found)"
      all_created=false
    fi
  done
  
  if [ "$all_created" = true ]; then
    print_success "All secrets created successfully!"
    return 0
  else
    print_error "Some secrets were not created"
    return 1
  fi
}

print_next_steps() {
  print_section "Next Steps"
  
  echo "✅ GitHub secrets configured"
  echo ""
  echo "Week 1 Setup Remaining:"
  echo "  ☐ Configure staging environment file (config/environments/staging.yml)"
  echo "  ☐ Configure production environment file (config/environments/production.yml)"
  echo "  ☐ Create GitHub environments (staging, production, production-rollback)"
  echo "  ☐ Set approval requirements for production environment"
  echo ""
  echo "Week 2: Dry-Runs"
  echo "  ☐ Test local CI checks (pnpm check-all, npm test)"
  echo "  ☐ Merge to develop and watch staging deploy"
  echo "  ☐ Create test version tag and watch production CI"
  echo "  ☐ Practice rollback workflow"
  echo ""
  echo "Documentation:"
  echo "  📖 .github/README.md - Complete guide"
  echo "  📖 .github/DEPLOYMENT_CONFIG.md - Technical details"
  echo "  📖 .github/POST_IMPLEMENTATION_CHECKLIST.md - Full setup checklist"
  echo ""
  echo "GitHub: https://github.com/$REPO_OWNER/$REPO_NAME/settings/secrets/actions"
  echo ""
}

##############################################################################
# Main
##############################################################################

main() {
  print_header "GitHub Secrets Setup"
  
  # Verification
  verify_repo
  verify_gh_cli
  verify_gh_auth
  
  # Get repository info
  get_repo_info
  
  # Get secrets
  if ! get_staging_secrets; then
    print_error "Failed to get staging secrets"
    exit 1
  fi
  
  if ! get_production_secrets; then
    print_error "Failed to get production secrets"
    exit 1
  fi
  
  # Create secrets
  if ! create_secrets; then
    print_error "Failed to create secrets"
    exit 1
  fi
  
  # Verify
  if ! verify_secrets; then
    print_error "Verification failed"
    exit 1
  fi
  
  # Next steps
  print_next_steps
  
  print_success "Setup complete!"
}

main
