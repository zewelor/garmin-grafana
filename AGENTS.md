# Garmin Grafana Fork Maintenance

This repository is an intentional fork of
`arpanghosh8453/garmin-grafana`, not a clean mirror. When pulling
upstream fixes, preserve this fork's QuestDB, Kubernetes, and runtime
contract.

## Fork invariants

- Default backend is QuestDB. Keep `INFLUXDB_*` env names only as
  compatibility names.
- Grafana datasource is PostgreSQL/QuestDB with UID `garmin_stats`; do
  not restore the upstream InfluxDB datasource/dashboard wholesale.
- Do not reintroduce InfluxDB v3 support unless explicitly requested:
  no `influxdb3-python`, `INFLUXDB_VERSION=3`,
  `INFLUXDB_V3_ACCESS_TOKEN`, or `INFLUXDB_ORG` paths.
- Runtime image is distroless nonroot. Preserve
  `/home/nonroot/.garminconnect`, Kubernetes UID/GID `65532`, and
  `ghcr.io/zewelor/garmin-grafana:latest`.
- Sync mode is one-shot and exits after a run. Preserve external
  scheduling and `MAX_CATCHUP_DAYS`; do not restore the upstream
  infinite sleep loop as the default.
- `ActivityLap` ingestion is intentionally disabled because it conflicts
  with QuestDB field typing.
- Do not re-add removed upstream distribution/build files:
  `src/garmin_grafana/fit_activity_importer.py`,
  `.github/workflows/codeberg-sync.yml`,
  `.github/workflows/version.release.yml`, `.woodpecker/docker.yml`, or
  Docker Hub/Codeberg publish flow.
- Preserve fork dashboard shape, including the QuestDB SQL dashboard and
  `Grafana_Dashboard/Garmin-Grafana-GPS-Dashboard.json`.

## Tracking upstream

Use inspection before integration:

1. Check local state:
   `git status --short --branch`
2. Check current upstream head:
   `git ls-remote --symref upstream HEAD refs/heads/main`
3. Fetch when ready to inspect locally:
   `git fetch upstream main`
4. Review commits and files before applying:
   `git log --oneline --left-right --cherry-pick main...upstream/main`
   `git diff --name-status main...upstream/main`
5. Prefer selective porting or `git cherry-pick -n` plus cleanup over
   blind `git merge upstream/main`.
6. For each upstream change, classify it as:
   - safe bugfix to port,
   - upstream infra/docs that should stay upstream-only,
   - feature needing QuestDB adaptation,
   - change that would revert a fork invariant.
7. If upstream uses InfluxDB-specific APIs, verify the QuestDB equivalent
   before porting. Do not add unsupported delete/query/write paths just
   because they exist upstream.

## Current upstream delta

As of 2026-05-24, local `main` is at `e5bb8bf` and upstream `main` is at
`94cced8`.

The latest upstream fix, `94cced8`, purges stale `StrengthExerciseSet`
series before rewriting strength exercises. Upstream implements this with
InfluxDB `delete_series`. Do not copy that implementation directly into
this fork: the default backend here is QuestDB. Exact QuestDB cleanup must
be designed and verified separately.

The current code recognizes QuestDB by probing its `/exec` SQL endpoint.
Because current QuestDB docs say direct row deletion is not supported, the
QuestDB path rebuilds `StrengthExerciseSet` without the refreshed
`ActivityID`, then writes the fresh Garmin snapshot. The rebuilt table keeps
WAL deduplication with `UPSERT KEYS(timestamp, ActivityID, SetOrder)`. Keep
`tests/questdb_strength_cleanup/run.sh` passing if this behavior changes.

## Verification

After porting upstream fixes, run:

- `git diff --check`
- `uv run python -m compileall src`
- `docker build -t garmin-grafana:merge-check .` when Docker, runtime, or
  dependency files changed.
