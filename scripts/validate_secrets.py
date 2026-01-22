import sys


def main():
    print(
        "[INFO] All required secrets are managed in Azure Key Vault or GitHub Secrets. No action needed."
    )
    print("[INFO] Secrets are available to workflows and agents as environment variables.")
    sys.exit(0)


if __name__ == "__main__":
    main()
