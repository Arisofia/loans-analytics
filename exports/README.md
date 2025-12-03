# Exports

The `evolutivo_gobierno_2025.csv` file currently contains illustrative figures taken from the prior request. It is **not** refreshed from the Google Drive source because this environment cannot access external links.

To replace it with the real numbers:
1. Manually download the validated CSV from the shared Google Drive folder: `https://drive.google.com/drive/u/0/folders/1zt2foEb7_64enii0UNj1X1J9AlU9hfcR`.
2. Overwrite `exports/evolutivo_gobierno_2025.csv` with that file.
3. Commit the updated export.

If you prefer to automate the download, add a script that authenticates to Google Drive using an authorized service account or OAuth token, then writes the CSV to this path. Network credentials are required for that workflow and are not available in this sandboxed environment.
