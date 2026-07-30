"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const page = document.body.dataset.page;

    document
        .querySelectorAll("[data-logout]")
        .forEach(function (button) {
            button.addEventListener("click", logout);
        });

    if (page === "login") startLogin();
    if (page === "signup") startSignup();
    if (page === "child") startChild();
    if (page === "monitor") startMonitor();
    if (page === "counsellor") startCounsellor();
});


async function api(url, options = {}) {
    const settings = {
        method: options.method || "GET",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    };

    if (options.body !== undefined) {
        settings.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, settings);
    const data = await response.json().catch(function () {
        return {};
    });

    if (response.status === 401) {
        window.location.href = "/";
        throw new Error("Please log in.");
    }

    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
    }

    return data;
}


function showMessage(id, text, type = "success") {
    const element = document.getElementById(id);

    if (!element) return;

    element.textContent = text;
    element.className = "message " + type;
}


function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value);
    return element.innerHTML;
}


async function logout() {
    await api("/api/logout", { method: "POST" });
    window.location.href = "/";
}


function startLogin() {
    const form = document.getElementById("loginForm");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        try {
            const result = await api("/api/login", {
                method: "POST",
                body: {
                    email: document.getElementById("loginEmail").value,
                    password: document.getElementById("loginPassword").value
                }
            });

            window.location.href = result.redirect;
        } catch (error) {
            showMessage("loginMessage", error.message, "error");
        }
    });
}


function startSignup() {
    const form = document.getElementById("signupForm");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        try {
            const result = await api("/api/signup", {
                method: "POST",
                body: {
                    full_name: document.getElementById("signupName").value,
                    email: document.getElementById("signupEmail").value,
                    password: document.getElementById("signupPassword").value,
                    role: document.getElementById("signupRole").value
                }
            });

            showMessage("signupMessage", result.message);
            form.reset();

            setTimeout(function () {
                window.location.href = "/";
            }, 800);
        } catch (error) {
            showMessage("signupMessage", error.message, "error");
        }
    });
}


async function startChild() {
    try {
        const data = await api("/api/child/dashboard");

        document.getElementById("childName").textContent =
            data.user.full_name;

        renderResources(data);
        renderAdvice(data.advice);

        document
            .getElementById("checkinForm")
            .addEventListener("submit", saveCheckIn);
    } catch (error) {
        showMessage("progressText", error.message, "error");
    }
}


function renderResources(data) {
    const grid = document.getElementById("resourcesGrid");

    grid.innerHTML = data.resources.map(function (resource) {
        let media;

        if (resource.resource_type === "video") {
            media = `
                <video controls preload="metadata">
                    <source
                        src="${escapeHtml(resource.file_url)}"
                        type="video/mp4"
                    >
                    Your browser cannot play this video.
                </video>
            `;
        } else {
            media = `
                <a
                    href="${escapeHtml(resource.file_url)}"
                    target="_blank"
                    rel="noopener"
                >
                    Open Booklet
                </a>
            `;
        }

        return `
            <article class="resource-card">
                <h3>${escapeHtml(resource.title)}</h3>
                <p>${escapeHtml(resource.description)}</p>
                ${media}
                <button
                    type="button"
                    data-resource-id="${resource.id}"
                    ${resource.completed ? "disabled" : ""}
                >
                    ${resource.completed
                        ? "Completed"
                        : "Mark as Completed"}
                </button>
            </article>
        `;
    }).join("");

    document.getElementById("progressText").textContent =
        data.completed_count +
        " of " +
        data.total_resources +
        " resources completed.";

    document
        .querySelectorAll("[data-resource-id]")
        .forEach(function (button) {
            button.addEventListener("click", async function () {
                try {
                    await api(
                        "/api/progress/" + button.dataset.resourceId,
                        { method: "POST" }
                    );

                    startChild();
                } catch (error) {
                    showMessage(
                        "progressText",
                        error.message,
                        "error"
                    );
                }
            });
        });
}


async function saveCheckIn(event) {
    event.preventDefault();

    try {
        const result = await api("/api/check-ins", {
            method: "POST",
            body: {
                feeling: document.getElementById("feeling").value,
                reason: document.getElementById("reason").value,
                support_requested:
                    document.getElementById("supportRequested").checked
            }
        });

        showMessage("checkinMessage", result.message);
        event.target.reset();
    } catch (error) {
        showMessage("checkinMessage", error.message, "error");
    }
}


function renderAdvice(advice) {
    const container = document.getElementById("adviceList");

    if (advice.length === 0) {
        container.innerHTML = "<p>No advice has been shared yet.</p>";
        return;
    }

    container.innerHTML = advice.map(function (item) {
        return `
            <article class="advice-item">
                <p>${escapeHtml(item.message)}</p>
                <small>
                    From ${escapeHtml(item.counsellor)}
                </small>
            </article>
        `;
    }).join("");
}


async function startMonitor() {
    try {
        const data = await api("/api/monitor/children");

        document.getElementById("monitorName").textContent =
            data.viewer;

        const table = document.getElementById("studentsBody");

        table.innerHTML = data.children.map(function (child) {
            return `
                <tr>
                    <td>${escapeHtml(child.full_name)}</td>
                    <td>${escapeHtml(child.email)}</td>
                    <td>
                        ${child.completed_count} /
                        ${child.total_resources}
                    </td>
                    <td>${escapeHtml(child.latest_feeling)}</td>
                    <td>
                        ${child.support_requested ? "Yes" : "No"}
                    </td>
                    <td class="${child.is_active ? "status-active" : "status-inactive"}">
                        ${child.is_active ? "Active" : "Inactive"}
                    </td>
                    <td>
                        <button
                            type="button"
                            class="small-button"
                            data-child-id="${child.id}"
                            data-next-status="${!child.is_active}"
                        >
                            ${child.is_active
                                ? "Set Inactive"
                                : "Set Active"}
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        document
            .querySelectorAll("[data-child-id]")
            .forEach(function (button) {
                button.addEventListener("click", async function () {
                    try {
                        await api(
                            "/api/monitor/children/" +
                            button.dataset.childId +
                            "/status",
                            {
                                method: "PATCH",
                                body: {
                                    is_active:
                                        button.dataset.nextStatus === "true"
                                }
                            }
                        );

                        startMonitor();
                    } catch (error) {
                        alert(error.message);
                    }
                });
            });
    } catch (error) {
        alert(error.message);
    }
}


async function startCounsellor() {
    try {
        const data = await api("/api/counsellor/children");

        document.getElementById("counsellorName").textContent =
            data.viewer;

        const table =
            document.getElementById("counsellorChildrenBody");

        table.innerHTML = data.children.map(function (child) {
            return `
                <tr>
                    <td>${escapeHtml(child.full_name)}</td>
                    <td>${escapeHtml(child.latest_feeling)}</td>
                    <td>${escapeHtml(child.reason)}</td>
                    <td>
                        ${child.support_requested ? "Yes" : "No"}
                    </td>
                </tr>
            `;
        }).join("");

        const select = document.getElementById("adviceChild");

        select.innerHTML =
            '<option value="">Choose a child</option>' +
            data.children.map(function (child) {
                return `
                    <option value="${child.id}">
                        ${escapeHtml(child.full_name)}
                    </option>
                `;
            }).join("");

        document
            .getElementById("adviceForm")
            .addEventListener("submit", saveAdvice);
    } catch (error) {
        alert(error.message);
    }
}


async function saveAdvice(event) {
    event.preventDefault();

    try {
        const result = await api("/api/counsellor/advice", {
            method: "POST",
            body: {
                child_id: Number(
                    document.getElementById("adviceChild").value
                ),
                message:
                    document.getElementById("adviceMessage").value
            }
        });

        showMessage("adviceMessageStatus", result.message);
        event.target.reset();
    } catch (error) {
        showMessage(
            "adviceMessageStatus",
            error.message,
            "error"
        );
    }
}
