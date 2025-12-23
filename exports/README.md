# Exports

The `evolutivo_gobierno_2025.csv` file currently contains illustrative figures taken from the prior request. It is not refreshed from the Cascade Platform source because this environment cannot access external links.

To replace it with the real numbers:

1. Access the validated CSV from the Cascade Platform data export:
   - Navigate to the Cascade Platform Analytics Dashboard
   - Use the data export feature to download the latest verified dataset
   - Select the `evolutivo_gobierno_2025` view

2. Overwrite `exports/evolutivo_gobierno_2025.csv` with that file.

3. Commit the updated export.

If you prefer to automate the download, add a script that authenticates to the Cascade Platform API using an authorized service account or OAuth token, then writes the CSV to this path. API authentication details are available in the Cascade Platform documentation at https://docs.cascade.app/api. Network credentials are required for that workflow and are not available in this sandboxed environment.
