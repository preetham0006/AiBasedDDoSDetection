let currentModel = null;


// ============================================================
// HELPERS
// ============================================================

function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}


function formatConfidence(value) {
    const number = Number(value || 0);
    return number.toFixed(1) + "%";
}


// ============================================================
// UPDATE STATISTICS
// ============================================================

function updateStats(data) {

    const stats = data.stats || {};

    document.getElementById("total").textContent =
        stats.total ?? 0;

    document.getElementById("ddos").textContent =
        stats.ddos ?? 0;

    document.getElementById("benign").textContent =
        stats.benign ?? 0;

    document.getElementById("confidence").textContent =
        formatConfidence(
            Number(stats.last_confidence || 0) * 100
        );
}


// ============================================================
// CURRENT DETECTION
// ============================================================

function updateCurrentDetection(data) {

    const events = Array.isArray(data.recent_events)
        ? data.recent_events
        : [];

    const state = document.getElementById("currentState");
    const meterFill = document.getElementById("meterFill");
    const meterText = document.getElementById("meterText");

    if (events.length === 0) {

        state.textContent = "WAITING FOR TRAFFIC";
        state.className = "state neutral";

        meterFill.style.width = "0%";
        meterText.textContent = "0%";

        document.getElementById("currentIp").textContent = "—";
        document.getElementById("currentAction").textContent = "—";
        document.getElementById("currentTime").textContent = "—";

        return;
    }

    const latest = events[0];

    const label =
        latest.label || "UNKNOWN";

    const confidence =
        Number(latest.confidence || 0);

    const isAttack =
        label.toUpperCase() === "DDOS";

    if (isAttack) {

        state.textContent = "DDoS DETECTED";
        state.className = "state attack";

    } else {

        state.textContent = "BENIGN TRAFFIC";
        state.className = "state normal";
    }

    meterFill.style.width =
        Math.min(confidence, 100) + "%";

    meterText.textContent =
        confidence.toFixed(1) + "%";

    document.getElementById("currentIp").textContent =
        latest.source_ip || "—";

    document.getElementById("currentAction").textContent =
        latest.action || "—";

    document.getElementById("currentTime").textContent =
        latest.time || "—";

    document.getElementById("currentModelTag").textContent =
        latest.model ||
        data.active_model ||
        "Unknown";
}


// ============================================================
// MODEL INFORMATION
// ============================================================

function updateModelUI(data) {

    currentModel =
        data.active_model || null;

    const activeModelElement =
        document.getElementById("activeModel");

    const classifierElement =
        document.getElementById("classifierName");

    const currentModelTag =
        document.getElementById("currentModelTag");

    if (activeModelElement) {
        activeModelElement.textContent =
            currentModel || "Unknown";
    }

    if (classifierElement) {
        classifierElement.textContent =
            currentModel || "Unknown";
    }

    if (currentModelTag) {
        currentModelTag.textContent =
            currentModel || "Unknown";
    }

    const select =
        document.getElementById("modelSelect");

    if (!select) {
        return;
    }

    const availableModels =
        Array.isArray(data.available_models)
            ? data.available_models
            : [];

    /*
     * Rebuild the dropdown from the backend.
     */

    select.innerHTML = "";

    if (availableModels.length === 0) {

        const option =
            document.createElement("option");

        option.value = "";
        option.textContent = "No models available";

        select.appendChild(option);

        select.disabled = true;

        return;
    }

    availableModels.forEach(model => {

        const option =
            document.createElement("option");

        option.value = model;
        option.textContent = model;

        if (model === currentModel) {
            option.selected = true;
        }

        select.appendChild(option);
    });

    select.disabled = false;
}


// ============================================================
// MODEL COMPARISON
// ============================================================

function updateModelComparison(metrics) {

    const container =
        document.getElementById("modelComparison");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!metrics || typeof metrics !== "object") {

        container.innerHTML =
            '<div class="empty-state">No model metrics available.</div>';

        return;
    }


    /*
     * IMPORTANT:
     *
     * metrics.json can have this structure:
     *
     * {
     *     "dataset": {...},
     *     "models": {
     *         "Random Forest": {...},
     *         "Logistic Regression": {...}
     *     },
     *     "training_configuration": {...}
     * }
     *
     * We ONLY want the contents of "models".
     */

    let modelMetrics;

    if (
        metrics.models &&
        typeof metrics.models === "object" &&
        !Array.isArray(metrics.models)
    ) {

        modelMetrics = metrics.models;

    } else {

        /*
         * Fallback in case metrics.json directly contains
         * the model names.
         */

        modelMetrics = metrics;
    }


    const entries =
        Object.entries(modelMetrics);


    /*
     * Only keep objects that actually contain
     * ML performance metrics.
     */

    const validModels =
        entries.filter(([name, values]) => {

            if (
                !values ||
                typeof values !== "object" ||
                Array.isArray(values)
            ) {
                return false;
            }

            return (
                "accuracy" in values ||
                "f1" in values ||
                "precision" in values ||
                "recall" in values
            );
        });


    if (validModels.length === 0) {

        container.innerHTML =
            '<div class="empty-state">No model performance metrics found.</div>';

        return;
    }


    // ========================================================
    // CREATE MODEL CARDS
    // ========================================================

    validModels.forEach(([name, values]) => {

        const accuracy =
            Number(values.accuracy || 0) * 100;

        const f1 =
            Number(values.f1 || 0) * 100;

        const precision =
            Number(values.precision || 0) * 100;

        const recall =
            Number(values.recall || 0) * 100;


        const card =
            document.createElement("div");

        card.className =
            "model-card" +
            (
                name === currentModel
                    ? " selected"
                    : ""
            );


        card.innerHTML = `

            <div class="model-card-header">

                <div>

                    <h3>
                        ${escapeHTML(name)}
                    </h3>

                    ${
                        name === currentModel
                            ? '<span class="selected-label">ACTIVE</span>'
                            : ''
                    }

                </div>

                <strong>
                    ${accuracy.toFixed(2)}%
                </strong>

            </div>


            <div class="metric">

                <div class="metric-row">

                    <span>Accuracy</span>

                    <b>
                        ${accuracy.toFixed(2)}%
                    </b>

                </div>


                <div class="bar">

                    <div
                        style="width:${Math.min(
                            Math.max(accuracy, 0),
                            100
                        )}%"
                    ></div>

                </div>

            </div>


            <div class="mini-metrics">

                <div>

                    <span>F1</span>

                    <b>
                        ${f1.toFixed(2)}%
                    </b>

                </div>


                <div>

                    <span>Precision</span>

                    <b>
                        ${precision.toFixed(2)}%
                    </b>

                </div>


                <div>

                    <span>Recall</span>

                    <b>
                        ${recall.toFixed(2)}%
                    </b>

                </div>

            </div>
        `;


        container.appendChild(card);
    });
}


// ============================================================
// DETECTION HISTORY
// ============================================================

function updateHistory(events) {

    const table =
        document.getElementById("events");

    if (!table) {
        return;
    }

    table.innerHTML = "";

    const items =
        Array.isArray(events)
            ? events
            : [];


    const historyCount =
        document.getElementById("historyCount");

    if (historyCount) {

        historyCount.textContent =
            `${items.length} event${
                items.length === 1
                    ? ""
                    : "s"
            }`;
    }


    if (items.length === 0) {

        table.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-table"
                >
                    No traffic events yet.
                </td>
            </tr>
        `;

        return;
    }


    items.forEach(event => {

        const tr =
            document.createElement("tr");


        const prediction =
            event.label || "UNKNOWN";


        const predictionClass =
            prediction.toUpperCase() === "DDOS"
                ? "bad"
                : "good";


        tr.innerHTML = `

            <td>
                ${escapeHTML(event.time || "—")}
            </td>

            <td class="mono">
                ${escapeHTML(event.source_ip || "—")}
            </td>

            <td>
                ${escapeHTML(event.model || "—")}
            </td>

            <td>
                <span class="tag ${predictionClass}">
                    ${escapeHTML(prediction)}
                </span>
            </td>

            <td>
                ${Number(event.confidence || 0).toFixed(2)}%
            </td>

            <td>
                <span class="tag action">
                    ${escapeHTML(event.action || "—")}
                </span>
            </td>
        `;


        table.appendChild(tr);
    });
}


// ============================================================
// BLOCKED IPs
// ============================================================

function updateBlockedList(blockedIps) {

    const container =
        document.getElementById("blocked");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const ips =
        Array.isArray(blockedIps)
            ? blockedIps
            : [];


    if (ips.length === 0) {

        container.textContent =
            "No blocked sources.";

        return;
    }


    ips.forEach(ip => {

        const span =
            document.createElement("span");

        span.className = "ip";

        span.textContent = ip;

        container.appendChild(span);
    });
}


// ============================================================
// REFRESH DASHBOARD
// ============================================================

async function refresh() {

    try {

        const response =
            await fetch(
                "/api/status",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log("Dashboard data:", data);


        /*
         * Update each section independently.
         *
         * This prevents one UI section from stopping
         * the entire dashboard if another section has
         * malformed data.
         */

        try {
            updateStats(data);
        } catch (error) {
            console.error(
                "Stats error:",
                error
            );
        }


        try {
            updateModelUI(data);
        } catch (error) {
            console.error(
                "Model UI error:",
                error
            );
        }


        try {
            updateCurrentDetection(data);
        } catch (error) {
            console.error(
                "Detection error:",
                error
            );
        }


        try {
            updateHistory(
                data.recent_events
            );
        } catch (error) {
            console.error(
                "History error:",
                error
            );
        }


        try {
            updateBlockedList(
                data.blocked_ips
            );
        } catch (error) {
            console.error(
                "Blocked list error:",
                error
            );
        }


        try {
            updateModelComparison(
                data.metrics
            );
        } catch (error) {
            console.error(
                "Model comparison error:",
                error
            );
        }


        const badge =
            document.getElementById(
                "modelBadge"
            );

        if (badge) {

            badge.textContent =
                "MODELS ONLINE";

            badge.classList.add(
                "ready"
            );
        }


    } catch (error) {

        console.error(
            "Dashboard connection error:",
            error
        );


        const badge =
            document.getElementById(
                "modelBadge"
            );

        if (badge) {

            badge.textContent =
                "BACKEND OFFLINE";

            badge.classList.remove(
                "ready"
            );
        }
    }
}


// ============================================================
// MODEL SWITCHING
// ============================================================

async function changeModel(modelName) {

    const status =
        document.getElementById(
            "switchStatus"
        );

    const select =
        document.getElementById(
            "modelSelect"
        );


    if (!modelName) {
        return;
    }


    status.textContent =
        "Switching...";

    status.className =
        "switch-status loading";

    select.disabled = true;


    try {

        const response =
            await fetch(
                "/api/model",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        model: modelName
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to switch model"
            );
        }


        currentModel =
            data.active_model;


        status.textContent =
            `Active: ${currentModel}`;

        status.className =
            "switch-status success";


        await refresh();


    } catch (error) {

        console.error(
            "Model switch error:",
            error
        );


        status.textContent =
            error.message ||
            "Model switch failed";

        status.className =
            "switch-status error";


        if (currentModel) {

            select.value =
                currentModel;
        }


    } finally {

        select.disabled = false;
    }
}


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const modelSelect =
            document.getElementById(
                "modelSelect"
            );


        if (modelSelect) {

            modelSelect.addEventListener(
                "change",
                event => {

                    changeModel(
                        event.target.value
                    );
                }
            );
        }


        // First load immediately
        refresh();


        // Refresh every second
        setInterval(
            refresh,
            1000
        );
    }
);