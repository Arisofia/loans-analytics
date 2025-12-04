# Configure Dependabot for Abaco private GitHub Packages

Use these steps to let Dependabot authenticate to the private GitHub Packages feeds that the Abaco Loans Analytics repo depends on. Use the exact repository scope and secret name below so Dependabot can reach the Abaco organization packages.

## 1) Create a read-only Personal Access Token (PAT)
- In GitHub, open **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
- Click **Generate new token** and name it **abaco-dependabot-gh-packages**.
- Scope the token to **Abaco-Technol/abaco-loans-analytics** (and any other private package repos Dependabot must read).
- Under **Repository permissions**, set **Packages** to **Read-only** and leave other permissions at **No access**.
- Set an expiration date, then **Generate token** and copy it immediately.

## 2) Store the token as a Dependabot secret
- In this repo, go to **Settings → Secrets and variables → Dependabot → New repository secret**.
- Name the secret **ABACO_GITHUB_PACKAGES_TOKEN** and paste the PAT value.
- Save the secret so Dependabot can read it during updates.

## 3) Reference the secret from `.github/dependabot.yml`
Add the GitHub Packages registry under the top-level `registries` key and point the npm ecosystem to it:

```yaml
# .github/dependabot.yml
version: 2
registries:
  npm-abaco-github:
    type: npm-registry
    url: https://npm.pkg.github.com/Abaco-Technol
    token: ${{secrets.ABACO_GITHUB_PACKAGES_TOKEN}}

updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - npm-abaco-github
```

## Notes
- Dependabot resolves private scopes in `package.json`/`.npmrc` against `https://npm.pkg.github.com/Abaco-Technol` when the registry is declared as above.
- Keep the secret name stable (`ABACO_GITHUB_PACKAGES_TOKEN`) so CI and docs reference the same credential. Rotate the PAT before it expires and update the secret with the new value.
