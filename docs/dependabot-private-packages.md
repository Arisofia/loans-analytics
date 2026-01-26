# Dependabot access to Abaco private GitHub Packages

This guide explains how to let Dependabot download Abaco's private packages from GitHub Packages by authenticating with a fine-grained Personal Access Token (PAT) stored as a Dependabot secret. The steps below assume you are configuring the `.github/dependabot.yml` that lives at the repository root.

## 1) Create a read-only GitHub PAT for packages
1. From your GitHub profile, create a **fine-grained token**.
2. Limit the **Resource owner** to **Abaco-Technol** and scope the **Repository access** to only the repositories whose packages Dependabot needs to read.
3. Under **Repository permissions**, set **Packages** to **Read-only**.
4. Set an expiration date and create the token. Copy the token value—you will not be able to see it again.

## 2) Add the PAT as a Dependabot secret
1. In the target repository, go to **Settings → Secrets and variables → Dependabot secrets**.
2. Add a new secret named **`ABACO_GITHUB_PACKAGES_TOKEN`**.
3. Paste the PAT value from the previous step and save. Keep the secret name stable so existing automation continues working when the token is rotated.

## 3) Configure the GitHub Packages registry in Dependabot
Add a `registries` entry and reference it from the npm update configuration in `.github/dependabot.yml`:

```yaml
version: 2
registries:
  abaco-github-packages:
    type: npm-registry
    url: https://npm.pkg.github.com/Abaco-Technol
    token: "${{secrets.ABACO_GITHUB_PACKAGES_TOKEN}}"

updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - abaco-github-packages
    # ...existing options...
```

### Usage notes
- Dependabot will use the registry URL above for Abaco package scopes (for example, packages published under `@abaco` or `@abaco-technol`). Keep the URL unchanged unless you are targeting a different GitHub Packages owner.
- Rotate the PAT regularly by replacing the Dependabot secret value while keeping the name `ABACO_GITHUB_PACKAGES_TOKEN`.
