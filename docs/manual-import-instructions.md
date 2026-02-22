### Garmin Bulk Importer (From Garmin Connect Export)

If you downloaded a bulk export .zip from the Garmin Connect website. You can import that data as well without having to be rate limited by API calls.

> [!IMPORTANT]
> This import path does not restore intraday historic data from cold storage. It imports supported daily and activity-level data from your export.

#### Using Docker

Use this method if your Garmin Grafana stack is running locally on the same machine.

1. Download your Garmin data export from Garmin Connect (this request may take several days to complete).
2. Unzip the export archive to a local folder.
3. Stop the currently running stack if needed:

```bash
docker compose down
```

4. Run the bulk importer and mount the unzipped export directory into the container:

```bash
# In ~/garmin-grafana
docker compose run --rm -v "<path_to_unzipped_export>:/bulk_export" -e MANUAL_START_DATE=YYYY-MM-DD -e MANUAL_END_DATE=YYYY-MM-DD garmin-fetch-data python /app/garmin_grafana/garmin_bulk_importer.py
```

Example:

```bash
docker compose run --rm -v "$HOME/Downloads/Garmin Export 2025-11-27:/bulk_export" -e MANUAL_START_DATE=2018-01-01 -e MANUAL_END_DATE=2025-01-03 garmin-fetch-data python /app/garmin_grafana/garmin_bulk_importer.py
```

5. Start regular online sync again:

```bash
docker compose up -d
```

> [!TIP]
> If you want to continue on non-critical parse issues, add `--ignore_errors` at the end of the importer command.
