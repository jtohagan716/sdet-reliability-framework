\# Test Baseline Notes



\## Date



2026-07-08



\## Purpose



Baseline the current SDET Reliability Framework before adding PostgreSQL audit logic and OpenTelemetry trace correlation.



\## Environment



\- OS: Windows 11

\- Runtime: Docker Compose

\- API: FastAPI

\- Database: PostgreSQL

\- Browser testing: Playwright



\## Commands Run



```powershell

git status

docker compose up -d --build

docker compose ps

Invoke-RestMethod http://localhost:8000/health

python -m pytest tests -v

npx playwright test





PS sdet-reliability-framework> npx playwright test



Running 105 tests using 4 workers

\[chromium] › tests\\ui\\api\_health.spec.ts:3:5 › Synthetic Canary - Local API Health Check



================================

API RESPONSE TRACE

================================

HTTP Status : 200

Status Text : OK

Payload:

{

&#x20; "status": "UP",

&#x20; "timestamp\_utc": "2026-07-08T11:52:56.395063+00:00"

}

================================





================================

API HEALTH CANARY

================================

Journey : Local API Health Check

Status  : PASS

Duration: 120 ms

Signal  : HEALTHY

================================



\[chromium] › tests\\ui\\api\_mocking.spec.ts:3:5 › simulate backend failure with mocked response



================================

MOCKED FAILURE TEST

================================

Backend Response : 500

Signal           : MOCK ACTIVE

================================



\[chromium] › tests\\ui\\canary.spec.ts:3:5 › Synthetic Canary - Framework Health Check



================================

SYNTHETIC CANARY

================================

Journey : Framework Health Check

Status  : PASS

Duration: 2902 ms

Signal  : HEALTHY

================================



\[chromium] › tests\\ui\\e2e\_security\_workflow.spec.ts:18:5 › end-to-end security workflow grants access to valid provider token



================================

E2E SECURITY WORKFLOW

================================

Subject  : james

Role     : provider

Resource : patient-summary

Status   : ACCESS\_GRANTED

Signal   : ACCESS GRANTED

================================



\[chromium] › tests\\ui\\fastapi\_health.spec.ts:3:5 › FastAPI health endpoint returns UP status



================================

FASTAPI HEALTH VIA PLAYWRIGHT

================================

HTTP Status : 200

Service     : UP

Timestamp   : 2026-07-08T11:53:50.618930+00:00

================================



\[chromium] › tests\\ui\\network\_inspection.spec.ts:6:5 › standard user login captures network responses during inventory load



================================

NETWORK INSPECTION

================================

200 https://www.saucedemo.com/

200 https://www.saucedemo.com/assets/index-Co7SA-g\_.css

200 https://www.saucedemo.com/assets/index-XyuNVFOR.js

200 https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500\&family=DM+Sans:wght@400;500

200 https://fonts.gstatic.com/s/dmmono/v16/aFTU7PB1QTsUX8KYthqQBA.woff2

200 https://www.saucedemo.com/assets/sauce-backpack-1200x1500-CjRW-Djj.jpg

200 https://www.saucedemo.com/assets/bike-light-1200x1500-DxcZRFOA.jpg

200 https://www.saucedemo.com/assets/red-onesie-1200x1500-BrSuq0ic.jpg

200 https://www.saucedemo.com/assets/sauce-pullover-1200x1500-BfbI-PSd.jpg

200 https://www.saucedemo.com/assets/bolt-shirt-1200x1500-mR0ldpVS.jpg

================================



\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



================================

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

PLAYWRIGHT PERFORMANCE HISTORY REPORT

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

================================

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

================================

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

PLAYWRIGHT PERFORMANCE TREND REPORT

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Previous Run : 2026-07-07T23:05:37.904Z

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

================================

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Current Run  : 2026-07-07T23:06:21.526Z

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Baseline Method      : MEDIAN

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Historical Runs Used : 43

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Health API

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Latest Run           : 2026-07-07T23:06:21.526Z

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Previous : 94 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Current  : 44 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Health API

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Variance : -53.19%

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Historical Median : 30 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Signal   : IMPROVING

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Latest            : 44 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Variance          : 46.67%

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Login

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Signal            : ELEVATED

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Previous : 1170 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Current  : 878 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Login

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Variance : -24.96%

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Historical Median : 655 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Signal   : IMPROVING

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Latest            : 878 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Variance          : 34.05%

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Total Workflow

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Signal            : ELEVATED

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Previous : 2612 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Current  : 1507 ms

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Total Workflow

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Variance : -42.3%

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Historical Median : 1512 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

Signal   : IMPROVING

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Latest            : 1507 ms

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report

================================

\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Variance          : -0.33%

\[chromium] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



\[chromium] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline

Signal            : STABLE

================================



\[chromium] › tests\\ui\\performance\_baseline.spec.ts:8:5 › measure login and inventory workflow performance



================================

PLAYWRIGHT PERFORMANCE BASELINE

================================

Health API Duration     : 10 ms

Login Duration          : 281 ms

Total Workflow Duration : 627 ms

History File            : C:\\Users\\james\\Documents\\sdet-reliability-framework\\reports\\baselines\\playwright\_performance\_history.json

Signal                  : BASELINE\_CAPTURED

================================



\[firefox] › tests\\ui\\api\_health.spec.ts:3:5 › Synthetic Canary - Local API Health Check



================================

API RESPONSE TRACE

================================

HTTP Status : 200

Status Text : OK

Payload:

{

&#x20; "status": "UP",

&#x20; "timestamp\_utc": "2026-07-08T11:54:00.266760+00:00"

}

================================





================================

API HEALTH CANARY

================================

Journey : Local API Health Check

Status  : PASS

Duration: 33 ms

Signal  : HEALTHY

================================



\[firefox] › tests\\ui\\api\_mocking.spec.ts:3:5 › simulate backend failure with mocked response



================================

MOCKED FAILURE TEST

================================

Backend Response : 500

Signal           : MOCK ACTIVE

================================



\[firefox] › tests\\ui\\canary.spec.ts:3:5 › Synthetic Canary - Framework Health Check



================================

SYNTHETIC CANARY

================================

Journey : Framework Health Check

Status  : PASS

Duration: 689 ms

Signal  : HEALTHY

================================



\[firefox] › tests\\ui\\e2e\_security\_workflow.spec.ts:18:5 › end-to-end security workflow grants access to valid provider token



================================

E2E SECURITY WORKFLOW

================================

Subject  : james

Role     : provider

Resource : patient-summary

Status   : ACCESS\_GRANTED

Signal   : ACCESS GRANTED

================================



\[firefox] › tests\\ui\\fastapi\_health.spec.ts:3:5 › FastAPI health endpoint returns UP status



================================

FASTAPI HEALTH VIA PLAYWRIGHT

================================

HTTP Status : 200

Service     : UP

Timestamp   : 2026-07-08T11:54:53.688017+00:00

================================



\[firefox] › tests\\ui\\network\_inspection.spec.ts:6:5 › standard user login captures network responses during inventory load



================================

NETWORK INSPECTION

================================

200 https://www.saucedemo.com/

200 https://www.saucedemo.com/assets/index-Co7SA-g\_.css

200 https://www.saucedemo.com/assets/index-XyuNVFOR.js

200 https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500\&family=DM+Sans:wght@400;500

200 https://fonts.gstatic.com/s/dmmono/v16/aFTR7PB1QTsUX8KYvumzEYOtbQ.woff2

200 https://fonts.gstatic.com/s/dmmono/v16/aFTU7PB1QTsUX8KYthqQBA.woff2

200 https://fonts.gstatic.com/s/dmsans/v17/rP2Yp2ywxg089UriI5-g4vlH9VoD8Cmcqbu0-K6z8GXhnU0.woff2

401 https://events.backtrace.io/api/summed-events/submit?universe=UNIVERSE\&token=TOKEN

401 https://events.backtrace.io/api/unique-events/submit?universe=UNIVERSE\&token=TOKEN

200 https://www.saucedemo.com/icon-192x192.png

================================



\[firefox] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



================================

PLAYWRIGHT PERFORMANCE HISTORY REPORT

================================

Previous Run : 2026-07-07T23:06:21.526Z

Current Run  : 2026-07-08T11:53:55.976Z



Health API

Previous : 44 ms

Current  : 10 ms

Variance : -77.27%

Signal   : IMPROVING



Login

Previous : 878 ms

Current  : 281 ms

Variance : -68%

Signal   : IMPROVING



Total Workflow

Previous : 1507 ms

Current  : 627 ms

Variance : -58.39%

Signal   : IMPROVING

================================



\[firefox] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



================================

PLAYWRIGHT PERFORMANCE TREND REPORT

================================

Baseline Method      : MEDIAN

Historical Runs Used : 44

Latest Run           : 2026-07-08T11:53:55.976Z



Health API

Historical Median : 32.5 ms

Latest            : 10 ms

Variance          : -69.23%

Signal            : STABLE



Login

Historical Median : 674 ms

Latest            : 281 ms

Variance          : -58.31%

Signal            : STABLE



Total Workflow

Historical Median : 1509.5 ms

Latest            : 627 ms

Variance          : -58.46%

Signal            : STABLE

================================



\[firefox] › tests\\ui\\performance\_baseline.spec.ts:8:5 › measure login and inventory workflow performance



================================

PLAYWRIGHT PERFORMANCE BASELINE

================================

Health API Duration     : 34 ms

Login Duration          : 530 ms

Total Workflow Duration : 1570 ms

History File            : C:\\Users\\james\\Documents\\sdet-reliability-framework\\reports\\baselines\\playwright\_performance\_history.json

Signal                  : BASELINE\_CAPTURED

================================



\[webkit] › tests\\ui\\api\_health.spec.ts:3:5 › Synthetic Canary - Local API Health Check



================================

API RESPONSE TRACE

================================

HTTP Status : 200

Status Text : OK

Payload:

{

&#x20; "status": "UP",

&#x20; "timestamp\_utc": "2026-07-08T11:55:07.527551+00:00"

}

================================





================================

API HEALTH CANARY

================================

Journey : Local API Health Check

Status  : PASS

Duration: 44 ms

Signal  : HEALTHY

================================



\[webkit] › tests\\ui\\api\_mocking.spec.ts:3:5 › simulate backend failure with mocked response



================================

MOCKED FAILURE TEST

================================

Backend Response : 500

Signal           : MOCK ACTIVE

================================



\[webkit] › tests\\ui\\canary.spec.ts:3:5 › Synthetic Canary - Framework Health Check



================================

SYNTHETIC CANARY

================================

Journey : Framework Health Check

Status  : PASS

Duration: 378 ms

Signal  : HEALTHY

================================



\[webkit] › tests\\ui\\e2e\_security\_workflow.spec.ts:18:5 › end-to-end security workflow grants access to valid provider token



================================

E2E SECURITY WORKFLOW

================================

Subject  : james

Role     : provider

Resource : patient-summary

Status   : ACCESS\_GRANTED

Signal   : ACCESS GRANTED

================================



\[webkit] › tests\\ui\\fastapi\_health.spec.ts:3:5 › FastAPI health endpoint returns UP status



================================

FASTAPI HEALTH VIA PLAYWRIGHT

================================

HTTP Status : 200

Service     : UP

Timestamp   : 2026-07-08T11:55:26.270134+00:00

================================



\[webkit] › tests\\ui\\network\_inspection.spec.ts:6:5 › standard user login captures network responses during inventory load



================================

NETWORK INSPECTION

================================

200 https://www.saucedemo.com/

200 https://www.saucedemo.com/manifest.json

200 https://www.saucedemo.com/assets/index-XyuNVFOR.js

200 https://www.saucedemo.com/assets/index-Co7SA-g\_.css

200 https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500\&family=DM+Sans:wght@400;500

200 https://fonts.gstatic.com/s/dmsans/v17/rP2Yp2ywxg089UriI5-g4vlH9VoD8Cmcqbu0-K6z9mXg.woff2

200 https://fonts.gstatic.com/s/dmmono/v16/aFTU7PB1QTsUX8KYthqQBK6PYK0.woff2

200 https://fonts.gstatic.com/s/dmmono/v16/aFTR7PB1QTsUX8KYvumzEYOtbYf-Vlg.woff2

401 https://events.backtrace.io/api/unique-events/submit?universe=UNIVERSE\&token=TOKEN

401 https://events.backtrace.io/api/summed-events/submit?universe=UNIVERSE\&token=TOKEN

================================



\[webkit] › tests\\ui\\performance\_history\_report.spec.ts:36:5 › generate Playwright performance history report



================================

PLAYWRIGHT PERFORMANCE HISTORY REPORT

================================

Previous Run : 2026-07-08T11:53:55.976Z

Current Run  : 2026-07-08T11:55:02.604Z



Health API

Previous : 10 ms

Current  : 34 ms

Variance : 240%

Signal   : DEGRADING



Login

Previous : 281 ms

Current  : 530 ms

Variance : 88.61%

Signal   : DEGRADING



Total Workflow

Previous : 627 ms

Current  : 1570 ms

Variance : 150.4%

Signal   : DEGRADING

================================



\[webkit] › tests\\ui\\performance\_trend\_report.spec.ts:44:5 › generate Playwright performance trend report using median baseline



================================

PLAYWRIGHT PERFORMANCE TREND REPORT

================================

Baseline Method      : MEDIAN

Historical Runs Used : 45

Latest Run           : 2026-07-08T11:55:02.604Z



Health API

Historical Median : 30 ms

Latest            : 34 ms

Variance          : 13.33%

Signal            : STABLE



Login

Historical Median : 655 ms

Latest            : 530 ms

Variance          : -19.08%

Signal            : STABLE



Total Workflow

Historical Median : 1507 ms

Latest            : 1570 ms

Variance          : 4.18%

Signal            : STABLE

================================



\[webkit] › tests\\ui\\performance\_baseline.spec.ts:8:5 › measure login and inventory workflow performance



================================

PLAYWRIGHT PERFORMANCE BASELINE

================================

Health API Duration     : 11 ms

Login Duration          : 785 ms

Total Workflow Duration : 1273 ms

History File            : C:\\Users\\james\\Documents\\sdet-reliability-framework\\reports\\baselines\\playwright\_performance\_history.json

Signal                  : BASELINE\_CAPTURED

================================



&#x20; 105 passed (2.7m)



To open last HTML report run:



&#x20; npx playwright show-report



PS sdet-reliability-framework> npx playwright show-report



&#x20; Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.

PS sdet-reliability-framework> docker compose logs api --tail=120

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:28,241 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=50af589b-69c1-4c1a-af72-536f4223ab0f method=GET path=/patients/1001

sdet-reliability-api  | 2026-07-08 11:55:28,242 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_started request\_id=50af589b-69c1-4c1a-af72-536f4223ab0f patient\_id=1001 data\_source=postgres defect\_mode=none

sdet-reliability-api  | 2026-07-08 11:55:28,286 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_success request\_id=50af589b-69c1-4c1a-af72-536f4223ab0f patient\_id=1001 status=active

sdet-reliability-api  | 2026-07-08 11:55:28,287 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=50af589b-69c1-4c1a-af72-536f4223ab0f method=GET path=/patients/1001 status\_code=200 duration\_ms=46.72

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /patients/1001 HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:28,297 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=df12eee8-173f-4eaf-8b86-2252fcd2ca8b method=GET path=/patients/9999

sdet-reliability-api  | 2026-07-08 11:55:28,298 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_started request\_id=df12eee8-173f-4eaf-8b86-2252fcd2ca8b patient\_id=9999 data\_source=postgres defect\_mode=none

sdet-reliability-api  | 2026-07-08 11:55:28,324 level=WARNING logger=sdet\_reliability\_api message=patient\_lookup\_not\_found request\_id=df12eee8-173f-4eaf-8b86-2252fcd2ca8b patient\_id=9999

sdet-reliability-api  | 2026-07-08 11:55:28,325 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=df12eee8-173f-4eaf-8b86-2252fcd2ca8b method=GET path=/patients/9999 status\_code=404 duration\_ms=27.97

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /patients/9999 HTTP/1.1" 404 Not Found

sdet-reliability-api  | 2026-07-08 11:55:28,335 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=24fc9859-9d44-4a14-a5a4-93fd034b5db5 method=GET path=/metrics

sdet-reliability-api  | 2026-07-08 11:55:28,340 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=24fc9859-9d44-4a14-a5a4-93fd034b5db5 method=GET path=/metrics status\_code=200 duration\_ms=5.19

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:28,462 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=cdbb9619-1eab-4a16-b378-e338e56575e7 method=GET path=/health

sdet-reliability-api  | 2026-07-08 11:55:28,463 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=cdbb9619-1eab-4a16-b378-e338e56575e7 method=GET path=/health status\_code=200 duration\_ms=1.4

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:28,909 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=e127c656-489a-46bc-b223-2d475e8189c5 method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:28,911 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=e127c656-489a-46bc-b223-2d475e8189c5 method=GET path=/patient-lookup status\_code=200 duration\_ms=2.25

sdet-reliability-api  | INFO:     172.18.0.1:38804 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:29,581 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=4e854ece-64d0-449d-90ba-8d2988b48239 method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:29,583 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=4e854ece-64d0-449d-90ba-8d2988b48239 method=GET path=/patient-lookup status\_code=200 duration\_ms=1.48

sdet-reliability-api  | INFO:     172.18.0.1:38806 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:30,425 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=8685ada5-0e8b-440b-ba69-b4f2e75c1417 method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:30,427 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=8685ada5-0e8b-440b-ba69-b4f2e75c1417 method=GET path=/patient-lookup status\_code=200 duration\_ms=1.85

sdet-reliability-api  | INFO:     172.18.0.1:38820 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:30,461 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=54e19f4e-4bc7-4e96-99c6-dff6304e2c99 method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:30,463 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=54e19f4e-4bc7-4e96-99c6-dff6304e2c99 method=GET path=/patient-lookup status\_code=200 duration\_ms=1.87

sdet-reliability-api  | INFO:     172.18.0.1:38836 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:30,562 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=cc78b357-6423-4869-951d-6c507abb95e2 method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:30,564 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=cc78b357-6423-4869-951d-6c507abb95e2 method=GET path=/patient-lookup status\_code=200 duration\_ms=2.07

sdet-reliability-api  | INFO:     172.18.0.1:38846 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:30,756 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=6b49f8f3-ab1e-4cf8-9fc1-341c51b6d70b method=GET path=/patients/1001

sdet-reliability-api  | 2026-07-08 11:55:30,764 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_started request\_id=6b49f8f3-ab1e-4cf8-9fc1-341c51b6d70b patient\_id=1001 data\_source=postgres defect\_mode=none

sdet-reliability-api  | 2026-07-08 11:55:30,810 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_success request\_id=6b49f8f3-ab1e-4cf8-9fc1-341c51b6d70b patient\_id=1001 status=active

sdet-reliability-api  | 2026-07-08 11:55:30,812 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=6b49f8f3-ab1e-4cf8-9fc1-341c51b6d70b method=GET path=/patients/1001 status\_code=200 duration\_ms=55.73

sdet-reliability-api  | INFO:     172.18.0.1:38836 - "GET /patients/1001 HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:30,853 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=f4149a85-6fe8-4e9e-8383-1ce5eb04247a method=GET path=/patients/9999

sdet-reliability-api  | 2026-07-08 11:55:30,854 level=INFO logger=sdet\_reliability\_api message=patient\_lookup\_started request\_id=f4149a85-6fe8-4e9e-8383-1ce5eb04247a patient\_id=9999 data\_source=postgres defect\_mode=none

sdet-reliability-api  | 2026-07-08 11:55:30,890 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=fe9b6aff-720c-4a7f-83a3-3094893acefe method=GET path=/patient-lookup

sdet-reliability-api  | 2026-07-08 11:55:30,941 level=WARNING logger=sdet\_reliability\_api message=patient\_lookup\_not\_found request\_id=f4149a85-6fe8-4e9e-8383-1ce5eb04247a patient\_id=9999

sdet-reliability-api  | 2026-07-08 11:55:30,943 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=f4149a85-6fe8-4e9e-8383-1ce5eb04247a method=GET path=/patients/9999 status\_code=404 duration\_ms=89.54

sdet-reliability-api  | INFO:     172.18.0.1:38846 - "GET /patients/9999 HTTP/1.1" 404 Not Found

sdet-reliability-api  | 2026-07-08 11:55:30,945 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=fe9b6aff-720c-4a7f-83a3-3094893acefe method=GET path=/patient-lookup status\_code=200 duration\_ms=54.49

sdet-reliability-api  | INFO:     172.18.0.1:38860 - "GET /patient-lookup HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:31,185 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=a5552716-60e5-489f-a3ae-398d54e87a3c method=GET path=/health

sdet-reliability-api  | 2026-07-08 11:55:31,187 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=a5552716-60e5-489f-a3ae-398d54e87a3c method=GET path=/health status\_code=200 duration\_ms=1.76

sdet-reliability-api  | INFO:     172.18.0.1:56118 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:31,320 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=92b25f7a-e8ed-43b2-a9f5-a8afc5afceb3 method=GET path=/secure/patient-summary

sdet-reliability-api  | 2026-07-08 11:55:31,322 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=92b25f7a-e8ed-43b2-a9f5-a8afc5afceb3 method=GET path=/secure/patient-summary status\_code=401 duration\_ms=2.76

sdet-reliability-api  | INFO:     172.18.0.1:56130 - "GET /secure/patient-summary HTTP/1.1" 401 Unauthorized

sdet-reliability-api  | 2026-07-08 11:55:31,377 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=00dca6c9-0f40-4bd3-8ba7-829c8a0e7cd1 method=GET path=/secure/patient-summary

sdet-reliability-api  | 2026-07-08 11:55:31,379 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=00dca6c9-0f40-4bd3-8ba7-829c8a0e7cd1 method=GET path=/secure/patient-summary status\_code=401 duration\_ms=2.0

sdet-reliability-api  | INFO:     172.18.0.1:56130 - "GET /secure/patient-summary HTTP/1.1" 401 Unauthorized

sdet-reliability-api  | 2026-07-08 11:55:31,456 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=ce7a345b-942f-4156-9c80-33d1818c4f0f method=GET path=/secure/patient-summary

sdet-reliability-api  | 2026-07-08 11:55:31,458 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=ce7a345b-942f-4156-9c80-33d1818c4f0f method=GET path=/secure/patient-summary status\_code=403 duration\_ms=1.94

sdet-reliability-api  | INFO:     172.18.0.1:56130 - "GET /secure/patient-summary HTTP/1.1" 403 Forbidden

sdet-reliability-api  | 2026-07-08 11:55:31,520 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=bc51821a-753f-474f-aa3d-98305d035b17 method=GET path=/secure/patient-summary

sdet-reliability-api  | 2026-07-08 11:55:31,522 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=bc51821a-753f-474f-aa3d-98305d035b17 method=GET path=/secure/patient-summary status\_code=200 duration\_ms=2.18

sdet-reliability-api  | INFO:     172.18.0.1:56130 - "GET /secure/patient-summary HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:37,783 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=8b1dc529-598f-48c3-b562-81958112cc42 method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:47298 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:37,784 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=8b1dc529-598f-48c3-b562-81958112cc42 method=GET path=/health status\_code=200 duration\_ms=1.32

sdet-reliability-api  | 2026-07-08 11:55:41,623 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=a35c0c96-b5a0-4238-9e28-096ef329075d method=GET path=/metrics

sdet-reliability-api  | 2026-07-08 11:55:41,627 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=a35c0c96-b5a0-4238-9e28-096ef329075d method=GET path=/metrics status\_code=200 duration\_ms=4.88

sdet-reliability-api  | INFO:     172.18.0.4:44478 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:48,170 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=c1951215-59b0-4395-810b-781bfc8a0f9d method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:38696 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:48,171 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=c1951215-59b0-4395-810b-781bfc8a0f9d method=GET path=/health status\_code=200 duration\_ms=0.88

sdet-reliability-api  | 2026-07-08 11:55:56,679 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=93c59db1-cf70-4702-b4bc-d687344adfce method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:37894 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:56,689 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=93c59db1-cf70-4702-b4bc-d687344adfce method=GET path=/metrics status\_code=200 duration\_ms=9.5

sdet-reliability-api  | 2026-07-08 11:55:58,420 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=689433d0-5d1e-4117-8a58-80de29916ae8 method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:49928 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:55:58,421 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=689433d0-5d1e-4117-8a58-80de29916ae8 method=GET path=/health status\_code=200 duration\_ms=0.81

sdet-reliability-api  | 2026-07-08 11:56:08,597 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=cbb6d3f2-51f6-46c1-a62c-e344b6e688cf method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:49308 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:08,598 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=cbb6d3f2-51f6-46c1-a62c-e344b6e688cf method=GET path=/health status\_code=200 duration\_ms=0.76

sdet-reliability-api  | 2026-07-08 11:56:11,678 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=52a8909c-3fca-4145-956b-2f2bb965db4e method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:58744 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:11,691 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=52a8909c-3fca-4145-956b-2f2bb965db4e method=GET path=/metrics status\_code=200 duration\_ms=13.18

sdet-reliability-api  | 2026-07-08 11:56:18,815 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=476871bd-cae7-409d-9a83-f421a533ea71 method=GET path=/health

sdet-reliability-api  | 2026-07-08 11:56:18,819 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=476871bd-cae7-409d-9a83-f421a533ea71 method=GET path=/health status\_code=200 duration\_ms=4.73

sdet-reliability-api  | INFO:     127.0.0.1:50184 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:26,673 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=bd460dc2-a68f-4ed8-8148-8f7699d9d811 method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:50992 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:26,677 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=bd460dc2-a68f-4ed8-8148-8f7699d9d811 method=GET path=/metrics status\_code=200 duration\_ms=4.02

sdet-reliability-api  | 2026-07-08 11:56:29,032 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=c65dd719-b630-44ba-ab03-1911a417c232 method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:33016 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:29,033 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=c65dd719-b630-44ba-ab03-1911a417c232 method=GET path=/health status\_code=200 duration\_ms=0.8

sdet-reliability-api  | 2026-07-08 11:56:39,318 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=22c4cc41-3967-4071-9364-eb780d17c1b6 method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:37318 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:39,319 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=22c4cc41-3967-4071-9364-eb780d17c1b6 method=GET path=/health status\_code=200 duration\_ms=0.91

sdet-reliability-api  | 2026-07-08 11:56:41,687 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=8d3112fa-0594-4400-8fab-0e68210e5903 method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:46902 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:41,691 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=8d3112fa-0594-4400-8fab-0e68210e5903 method=GET path=/metrics status\_code=200 duration\_ms=3.69

sdet-reliability-api  | 2026-07-08 11:56:49,497 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=2d6803a7-b378-45ce-9788-1e7c4efe5500 method=GET path=/health

sdet-reliability-api  | 2026-07-08 11:56:49,499 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=2d6803a7-b378-45ce-9788-1e7c4efe5500 method=GET path=/health status\_code=200 duration\_ms=1.65

sdet-reliability-api  | INFO:     127.0.0.1:44298 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:56,683 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=8a40e6a0-426d-4d67-bcfb-fce2aa963e89 method=GET path=/metrics

sdet-reliability-api  | 2026-07-08 11:56:56,698 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=8a40e6a0-426d-4d67-bcfb-fce2aa963e89 method=GET path=/metrics status\_code=200 duration\_ms=15.49

sdet-reliability-api  | INFO:     172.18.0.4:42464 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:59,809 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=ddfdbf46-c8ef-45d4-98d1-e60376360ced method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:37422 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:56:59,810 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=ddfdbf46-c8ef-45d4-98d1-e60376360ced method=GET path=/health status\_code=200 duration\_ms=1.01

sdet-reliability-api  | 2026-07-08 11:57:10,010 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=53a72d5a-578f-4b6b-b90f-41a2d26a2bda method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:36814 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:57:10,011 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=53a72d5a-578f-4b6b-b90f-41a2d26a2bda method=GET path=/health status\_code=200 duration\_ms=0.79

sdet-reliability-api  | 2026-07-08 11:57:11,667 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=b10175c8-7191-4bfb-b3bb-eef70422fc20 method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:42100 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:57:11,684 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=b10175c8-7191-4bfb-b3bb-eef70422fc20 method=GET path=/metrics status\_code=200 duration\_ms=17.37

sdet-reliability-api  | 2026-07-08 11:57:20,204 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=f50dbf36-90f3-401d-bfa6-526de5107af4 method=GET path=/health

sdet-reliability-api  | 2026-07-08 11:57:20,205 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=f50dbf36-90f3-401d-bfa6-526de5107af4 method=GET path=/health status\_code=200 duration\_ms=0.87

sdet-reliability-api  | INFO:     127.0.0.1:33006 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:57:26,642 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=915dc96a-17e8-40fa-833c-f4a569cd4511 method=GET path=/metrics

sdet-reliability-api  | INFO:     172.18.0.4:56666 - "GET /metrics HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:57:26,651 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=915dc96a-17e8-40fa-833c-f4a569cd4511 method=GET path=/metrics status\_code=200 duration\_ms=9.25

sdet-reliability-api  | 2026-07-08 11:57:30,417 level=INFO logger=sdet\_reliability\_api message=request\_start request\_id=42774b9a-14c3-43ba-ac21-c038b26be0ba method=GET path=/health

sdet-reliability-api  | INFO:     127.0.0.1:60514 - "GET /health HTTP/1.1" 200 OK

sdet-reliability-api  | 2026-07-08 11:57:30,418 level=INFO logger=sdet\_reliability\_api message=request\_complete request\_id=42774b9a-14c3-43ba-ac21-c038b26be0ba method=GET path=/health status\_code=200 duration\_ms=0.84

PS sdet-reliability-framework> New-Item -ItemType Directory -Force docs





&#x20;   Directory: C:\\Users\\james\\Documents\\sdet-reliability-framework





Mode                 LastWriteTime         Length Name

\----                 -------------         ------ ----

d-----          7/7/2026   4:50 PM                docs





PS sdet-reliability-framework> New-Item -ItemType File -Force docs\\test-baseline-notes.md





&#x20;   Directory: C:\\Users\\james\\Documents\\sdet-reliability-framework\\docs





Mode                 LastWriteTime         Length Name

\----                 -------------         ------ ----

\-a----          7/8/2026   7:58 AM              0 test-baseline-notes.md





PS sdet-reliability-framework> notepad docs\\test-baseline-notes.md

PS sdet-reliability-framework>





