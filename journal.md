# 2025-12-28

Schema sections:
- Sleep
- Heart
- Training
- Steps
- Date
- Weight
- Diet

Schema super-sections:
- Regen
- Activity
- Weight
- Diet

Schema Subscetions:
```sh
- Regen
    - Sleep
        - time
            - startTime [ts]
            - endTime [ts]
            - timeAsleep [h]
            - timeInBed [h]
        - efficiency [%]
        - stages
            - deep [h]
            - light [h]
            - rem [h]
            - wake [h]
    - Heart
        - HRV [ms] 
        - RHR [bpm]
- Activity
    - Training 
        - Type [txt] # manually
        - Load [%]   # manually
    - NEAT
        - Steps [1]
- Weight
    - Date [Date]    
    - Weight [kg]    # manually
- Diet 
    - Cal. [kcal]
    - Prot. [g]
    - Fats. [g]
    - Carb. [g]
```

Jak się dostać do Fitbit API? -> [1 - Intro and accessing FitBit API with Postman - FitBit API for Beginners](https://youtu.be/e5WYfIqt_Zk?si=z8fNUBzy5bypgUQ_).



# 26-11-07 Migration: Fitbit -> Google Health

## What happened
- Fitbit Web API + Fitbit OAuth were turned off on 2026-11-02. Last good run: 2026-11-02.
- From 2026-11-03 every daily run failed: `401` on `api.fitbit.com/.../profile.json`, then `410 Gone` on `api.fitbit.com/oauth2/token` (the refresh attempt). Nothing alerts on a failed run, so it went unnoticed for 5 days.
- Replaced the Fitbit client with the Google Health API (`https://health.googleapis.com/v4/users/me`). Old Fitbit tokens can't be migrated - had to consent again with Google.

## Setup done (one time)
- Google account linked to Google Health (Fitbit account moved to Google Account).
- Google Cloud project `Monitor-2026`: "Google Health API" enabled, OAuth client type "Web Server", redirect URI `https://www.google.com`.
- Consent screen: External, **published ("In production")**. Without that the refresh token expires after 7 days. It stays "unverified" (warning screen -> Advanced -> Go to Monitor-2026). 1 of 100 users, that is fine. Branding verification complaints can be ignored.
- Scopes: `googlehealth.sleep.readonly`, `googlehealth.health_metrics_and_measurements.readonly`, `googlehealth.activity_and_fitness.readonly`.

## Code
- `infra/fitbit/` -> `infra/google_health/client.py` (`GoogleHealthClient`), same methods: `sleep`, `hrv`, `rhr`, `steps`. `monitor.py` only got renames.
- sleep: `dataPoints:reconcile` with `google-wearables` (plain list returns duplicates: Withings via Health Connect + Fitbit). Main sleep = `metadata.mainSleep`. Efficiency is NOT in the API -> computed `round(asleep / in_bed * 100)` (matches the old Fitbit values in the sheet). Times converted from UTC + offset to local.
- hrv: `daily-heart-rate-variability` -> `averageHeartRateVariabilityMilliseconds`. rhr: `daily-resting-heart-rate` -> `beatsPerMinute`. steps: `steps:dailyRollUp` -> `countSum`.
- env: `GOOGLE_HEALTH_CLIENT_ID`, `GOOGLE_HEALTH_CLIENT_SECRET`, `GOOGLE_HEALTH_TOKENS_FILE` (replace `FITBIT_*`).
- Tokens file is still `data/.fitbit_tokens.json` (name kept so the Makefile mounts did not change). It holds the **Google Health** tokens: `{"access_token", "refresh_token"}`.
- Backfilled 2026-11-03 ... 2026-11-07 via `/api/v1/run?date=...`. Sheets `429` (read quota per minute) when running days back to back - wait ~1 min between runs.

## When the Google Health token expires
- Access token: lives ~1h, the client refreshes it by itself on `401`. Nothing to do.
- Refresh token: lives until revoked or unused for ~6 months (7 days if the app is ever put back to "Testing"). Symptom in `docker logs monitor-2026`: `400 ... oauth2.googleapis.com/token` (`invalid_grant`) after a `401` from `health.googleapis.com`.
- Manual refresh (Postman) - to check that the refresh token is still alive:
  `POST https://oauth2.googleapis.com/token` (x-www-form-urlencoded): `client_id`, `client_secret`, `refresh_token`, `grant_type=refresh_token`.
- Re-authorize (when the refresh token is dead):
  1. Browser (logged in as the Google account linked to Google Health):
     `https://accounts.google.com/o/oauth2/v2/auth?client_id=<ID>&redirect_uri=https://www.google.com&response_type=code&access_type=offline&prompt=consent&scope=<3 scopes, space separated>`
     -> Advanced -> Go to Monitor-2026 -> approve -> copy `code=` from the address bar (no leading `=`).
  2. `POST https://oauth2.googleapis.com/token`: `code`, `client_id`, `client_secret`, `redirect_uri=https://www.google.com`, `grant_type=authorization_code`. The code is single use and short lived.
  3. Put `access_token` + `refresh_token` into `data/.fitbit_tokens.json`, then `make docker-restart`.
- Client secret: rotate in Google Cloud -> Credentials -> your OAuth client -> add secret -> update `.env` -> restart.

# 26-11-07 Withings: Integration

## Why
- Google Health API has no muscle mass (no data type for muscle/lean/bone/water, only `weight` and `body-fat` %). Weight and fat do flow from the Withings scale through Health Connect, but that is undocumented, so the Withings API is used directly for all three columns.
- Muscle mass is Withings `meastype` 76 (not lean mass). Types used: `1` weight (kg), `8` fat mass (kg), `76` muscle mass (kg). Value = `value * 10^unit`.

## Setup done (one time)
- App registered in the Withings developer dashboard (https://developer.withings.com/dashboard/), scope `user.metrics`.
- Postman requests: `Withings SIGNATURE` (getnonce) and `Withings TOKEN` (requesttoken). The TOKEN pre-request script fetches its own nonce, so only one click is needed after the browser step.

## Code
- `infra/withings/client.py` (`WithingsClient`): `body_composition(date)` = first weigh-in of the day (Europe/Warsaw), returns `weight`, `fat`, `muscle` rounded to 1 decimal. Endpoint `POST https://wbsapi.withings.net/measure` (`action=getmeas`, `meastypes=1,8,76`, `category=1`). Responses are `200` with `{"status": ..., "body": ...}`; `status 401` = bad access token -> refresh once and retry.
- `DaySnapshot` got `weight`, `fat`, `muscle` -> sheet columns `weight [kg]`, `fat [kg]`, `muscle [kg]` (same row as the date).
- env: `WITHINGS_CLIENT_ID`, `WITHINGS_CLIENT_SECRET`, `WITHINGS_TOKENS_FILE=/data/.withings_tokens.json`. File on host: `data/.withings_tokens.json` (create it BEFORE starting the container, otherwise Docker makes a directory), mounted in all `make docker-*` targets.
- Tested live: Nov 3-7 values equal the sheet. Forced refresh worked (Withings returned the same refresh token, the client stores whatever it gets).

## When the Withings token expires
- Access token: lives 3h, the client refreshes it by itself (nonce -> `requesttoken`). Nothing to do.
- Refresh token: lives 1 year (so around 2027-11) and, per the docs, rotates on refresh (the client saves the new one). Symptom in logs: `RuntimeError: Withings token refresh failed: {'status': ..., 'error': ...}`.
- Re-authorize:
  1. Browser: `https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=<ID>&scope=user.metrics&redirect_uri=<registered URI>&state=abc` -> approve -> copy `code=`. **The code lives only 30 seconds.**
  2. Postman `Withings TOKEN` (`action=requesttoken`, `grant_type=authorization_code`, `code`, `redirect_uri`, signature + nonce from the pre-request script) -> send immediately.
  3. Put `access_token` + `refresh_token` from the response `body` into `data/.withings_tokens.json`, then `make docker-restart`.
- Signature = hex HMAC-SHA256 with the client secret over `getnonce,<client_id>,<timestamp>` (nonce call) and `requesttoken,<client_id>,<nonce>` (token call). Nonces are single use and expire fast. `Invalid HMAC signature` = wrong message / secret, `Expired nonce` = fetch a new one.

## Deploy / gotchas
- Deploy: `make docker-build && make docker-restart` (needs `data/.fitbit_tokens.json`, `data/.withings_tokens.json`, `run/secrets/credentials.json` and `.env`). `HOST_PORT` comes from the shell env (`LUKA`).
- Check: `make curl-ready`; run a day manually: `make curl-run-date DATE=YYYY-MM-DD`.
- Chmod 600 on `.env` and the token files.
- Idea, not done: VO2 max is available in Google Health (`daily-vo2-max`, `dailyVo2Max.vo2Max`), the sheet has no column for it yet.
