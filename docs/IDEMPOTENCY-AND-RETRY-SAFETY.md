\# Idempotency and Retry Safety



\## Purpose



This document explains how the SDET Reliability Framework validates idempotency and retry-safe API behavior.



Idempotency is an important reliability pattern for write-style operations. It helps prevent duplicate processing when a client retries the same request because of a timeout, network issue, gateway retry, browser retry, or unclear response state.



The core rule is:



```text

Same idempotency key + same request = replay the original response.

Same idempotency key + different request = reject as a conflict.

```



\---



\## Why This Matters



Real systems retry requests.



Retries may happen because of:



```text

network timeout

load balancer retry

API gateway retry

client timeout

browser double-submit

background worker retry

message queue retry

deployment interruption

```



The risky scenario is:



```text

The server successfully processes the first request,

but the client does not receive the response.



The client retries the same request.



Without idempotency, the system may process the operation twice.

```



For write-style operations, duplicate processing can create bad data.



Example:



```text

First request:

&#x20; create encounter result A



Retry request:

&#x20; create encounter result B



Problem:

&#x20; one client intent created two business results

```



With idempotency:



```text

First request:

&#x20; create and store result A



Retry request:

&#x20; return stored result A



Outcome:

&#x20; no duplicate business result

```



\---



\## What This Project Validates



This project includes a local QA endpoint:



```text

POST /qa/idempotency-validation

```



The endpoint validates three behaviors:



```text

1\. A new request stores an original response.

2\. A retry with the same key and same request body replays the original response.

3\. A retry with the same key but different request body returns a conflict.

```



\---



\## Request Header



The endpoint requires this header:



```text

Idempotency-Key

```



Example:



```text

Idempotency-Key: idem-demo-001

```



This key identifies a client retry group.



It answers:



```text

Have I already processed this client request?

```



\---



\## Request Hash



The endpoint also calculates a SHA-256 hash of the request body.



Example:



```text

sha256:5300e324014769cc6d56976c28b7a909f1e38046451aa83e3939893cfef3ab52

```



The request hash helps determine whether the retry is truly the same request.



This protects against unsafe key reuse.



Example conflict:



```text

First request:

&#x20; Idempotency-Key: idem-demo-001

&#x20; patient\_id: 1001

&#x20; encounter\_type: primary\_care



Second request:

&#x20; Idempotency-Key: idem-demo-001

&#x20; patient\_id: 2002

&#x20; encounter\_type: urgent\_care



Expected:

&#x20; reject as a conflict

```



The same idempotency key should not be reused for different request content.



\---



\## Database Table



The project stores idempotency records in:



```text

idempotency\_keys

```



Important fields:



```text

idempotency\_key

request\_method

request\_path

request\_hash

response\_status

response\_body

replayed\_count

created\_at

last\_replayed\_at

expires\_at

trace\_id

span\_id

request\_id

service\_name

```



The primary key is:



```text

idempotency\_key

```



That prevents two rows from being stored for the same idempotency key.



The request hash, method, and path provide additional safety by proving whether the retry matches the original request.



\---



\## New Request Behavior



When a request arrives with a new idempotency key, the API stores:



```text

request method

request path

request hash

response status

response body

service name

created timestamp

expiration timestamp

```



The response indicates that the request was newly created.



Example response:



```json

{

&#x20; "validation": "idempotency\_created",

&#x20; "idempotency\_key": "idem-demo-001",

&#x20; "response\_status": 201,

&#x20; "replayed": false,

&#x20; "replayed\_count": 0

}

```



This proves that the request was processed as new.



\---



\## Replay Behavior



When the same idempotency key is used with the same request body, the endpoint returns the stored response instead of creating a new result.



Example response:



```json

{

&#x20; "validation": "idempotency\_replayed",

&#x20; "idempotency\_key": "idem-demo-001",

&#x20; "response\_status": 201,

&#x20; "replayed": true,

&#x20; "replayed\_count": 1

}

```



This proves that the retry was detected and safely replayed.



The stored response body remains the original response.



\---



\## Conflict Behavior



When the same idempotency key is reused with different request content, the endpoint returns a conflict.



Expected status:



```text

409 Conflict

```



Expected validation result:



```text

idempotency\_conflict

```



This protects the system from treating a different request as a safe retry.



\---



\## TTL Cleanup



Idempotency records should not remain forever.



This project includes Time To Live (TTL) cleanup support using:



```text

expires\_at

```



Rows can be removed after their retry-safety window has passed.



Cleanup script:



```text

scripts/cleanup\_expired\_idempotency\_keys.sql

```



Validation script:



```text

scripts/validate\_idempotency\_ttl\_cleanup.sql

```



This proves that:



```text

expired idempotency rows are removed

active idempotency rows remain

the table does not need to grow forever

```



\---



\## Automated Test Coverage



The project includes an integration test:



```text

tests/integration/test\_idempotency\_validation.py

```



The test validates:



```text

new request creates a stored response

same request replays the stored response

conflicting request returns HTTP 409

test cleanup removes the synthetic idempotency key

```



The test skips cleanly when the QA endpoint is unavailable or disabled in environments such as GitHub Actions.



\---



\## Reliability Value



This feature demonstrates more than basic API testing.



It validates production-style behavior:



```text

safe retries

duplicate-write prevention

request fingerprinting

stored response replay

conflict detection

database-backed evidence

table lifecycle cleanup

CI-aware integration testing

```



This is relevant to API testing, backend validation, Site Reliability Engineering (SRE), healthcare integration testing, and reliability-focused Software Development Engineer in Test (SDET) work.



\---



\## Summary



The idempotency feature proves that the system can handle repeated write-style requests safely.



The key behavior is:



```text

Same key, same request:

&#x20; replay the original response



Same key, different request:

&#x20; reject as conflict



Expired key:

&#x20; eligible for cleanup

```



This gives the framework a realistic reliability scenario that goes beyond simple success-path API validation.



