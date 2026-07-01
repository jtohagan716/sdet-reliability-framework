const fs = require("fs");

const collectionPath = "postman/SDET_Reliability_Framework.postman_collection.json";

const collection = JSON.parse(fs.readFileSync(collectionPath, "utf8"));

collection.item = collection.item || [];

// Remove existing folder if this script is run more than once.
// This keeps the update idempotent and prevents duplicate folders.
collection.item = collection.item.filter(
    (item) => item.name !== "Synthetic Patient API"
);

function makeRequestItem(name, method, url, testScript) {
    return {
        name,
        event: [
            {
                listen: "test",
                script: {
                    type: "text/javascript",
                    exec: testScript.trim().split("\n"),
                },
            },
        ],
        request: {
            method,
            header: [],
            url,
        },
        response: [],
    };
}

const responseTimeCheck = `
const maxResponseMs = Number(pm.environment.get("max_response_ms") || 1000);

pm.test("Response time is below configured threshold", function () {
    pm.expect(pm.response.responseTime).to.be.below(maxResponseMs);
});
`;

const sensitiveFieldCheck = `
const sensitiveFields = [
    "ssn",
    "social_security_number",
    "password",
    "token",
    "api_key",
    "secret",
    "diagnosis",
    "real_address",
    "production_system_id",
    "medical_record_number"
];

pm.test("Response does not expose sensitive fields", function () {
    const jsonData = pm.response.json();

    sensitiveFields.forEach(function (field) {
        pm.expect(jsonData).to.not.have.property(field);
    });
});
`;

const patient1001Tests = `
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

${responseTimeCheck}

pm.test("Response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("Response contains expected synthetic patient 1001 data", function () {
    const jsonData = pm.response.json();

    pm.expect(jsonData).to.have.property("patient_id", 1001);
    pm.expect(jsonData).to.have.property("name", "Alex Morgan");
    pm.expect(jsonData).to.have.property("status", "active");
    pm.expect(jsonData).to.have.property("last_visit", "2026-06-15");
});

${sensitiveFieldCheck}
`;

const patient1002Tests = `
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

${responseTimeCheck}

pm.test("Response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("Response contains expected synthetic patient 1002 data", function () {
    const jsonData = pm.response.json();

    pm.expect(jsonData).to.have.property("patient_id", 1002);
    pm.expect(jsonData).to.have.property("name", "Jordan Lee");
    pm.expect(jsonData).to.have.property("status", "inactive");
    pm.expect(jsonData).to.have.property("last_visit", "2026-05-20");
});

${sensitiveFieldCheck}
`;

const unknownPatientTests = `
pm.test("Status code is 404", function () {
    pm.response.to.have.status(404);
});

${responseTimeCheck}

pm.test("Response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("Unknown synthetic patient returns controlled detail message", function () {
    const jsonData = pm.response.json();

    pm.expect(jsonData).to.have.property("detail", "Synthetic patient 9999 not found");
});
`;

const invalidPatientIdTests = `
pm.test("Status code is 422", function () {
    pm.response.to.have.status(422);
});

${responseTimeCheck}

pm.test("Response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("Invalid patient ID returns validation detail array", function () {
    const jsonData = pm.response.json();

    pm.expect(jsonData).to.have.property("detail");
    pm.expect(jsonData.detail).to.be.an("array");
});
`;

const unsupportedPostTests = `
pm.test("Status code is 405", function () {
    pm.response.to.have.status(405);
});

${responseTimeCheck}

pm.test("Response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("Unsupported method returns controlled error detail", function () {
    const jsonData = pm.response.json();

    pm.expect(jsonData).to.have.property("detail");
});
`;

const openApiPatientContractTests = `
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

${responseTimeCheck}

pm.test("OpenAPI response is valid JSON", function () {
    pm.response.to.be.json;
});

pm.test("OpenAPI contract documents synthetic patient endpoint", function () {
    const openapi = pm.response.json();

    pm.expect(openapi).to.have.property("paths");
    pm.expect(openapi.paths).to.have.property("/patients/{patient_id}");
    pm.expect(openapi.paths["/patients/{patient_id}"]).to.have.property("get");
});
`;

const syntheticPatientFolder = {
    name: "Synthetic Patient API",
    item: [
        makeRequestItem(
            "GET /patients/1001 returns synthetic active patient",
            "GET",
            "{{base_url}}/patients/1001",
            patient1001Tests
        ),
        makeRequestItem(
            "GET /patients/1002 returns synthetic inactive patient",
            "GET",
            "{{base_url}}/patients/1002",
            patient1002Tests
        ),
        makeRequestItem(
            "GET /patients/9999 returns 404 for unknown patient",
            "GET",
            "{{base_url}}/patients/9999",
            unknownPatientTests
        ),
        makeRequestItem(
            "GET /patients/abc returns 422 for invalid path parameter",
            "GET",
            "{{base_url}}/patients/abc",
            invalidPatientIdTests
        ),
        makeRequestItem(
            "POST /patients/1001 returns 405 for unsupported method",
            "POST",
            "{{base_url}}/patients/1001",
            unsupportedPostTests
        ),
        makeRequestItem(
            "GET /openapi.json documents synthetic patient endpoint",
            "GET",
            "{{base_url}}/openapi.json",
            openApiPatientContractTests
        ),
    ],
};

collection.item.push(syntheticPatientFolder);

fs.writeFileSync(collectionPath, JSON.stringify(collection, null, 2) + "\n");

console.log("Synthetic Patient API Postman tests added successfully.");