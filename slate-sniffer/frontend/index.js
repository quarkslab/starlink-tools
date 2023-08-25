// Copyright 2023 Quarkslab

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function getServices() {
    return new Promise((resolve, reject) => {
        $.get("/services", (data, status) => {
            if (status === "success") {
                resolve(data);
            } else {
                reject(status);
            }
        });
    });
}

function getSchema(service) {
    return new Promise((resolve, reject) => {
        $.get(`/services/${service}/schema`, (data, status) => {
            if (status === "success") {
                resolve(data);
            } else {
                reject(status);
            }
        });
    });
}

function getMessages(service, last_id = undefined) {
    return new Promise((resolve, reject) => {
        $.get(`/services/${service}/messages` + (last_id !== undefined ? `?last_id=${last_id}` : ""), (data, status) => {
            if (status === "success") {
                resolve(data);
            } else {
                reject(status);
            }
        });
    });
}

function getStatus() {
    return new Promise((resolve, reject) => {
        $.get("/status", (data, status) => {
            if (status === "success") {
                resolve(data.status);
            } else {
                reject(status);
            }
        });
    });
}

function setStatus(newStatus) {
    return new Promise((resolve, reject) => {
        $.ajax("/status", {
            data : JSON.stringify({
                status: newStatus
            }),
            contentType : 'application/json',
            type : 'POST',
            success: (data) => {
                resolve(data.status);
            },
            error: () => {
                reject();
            }
        });
    });
}

async function initServiceTable() {
    const services = await getServices();

    const table = $("#table-services").DataTable({
        paging: false,
        data: services.map((s) => [s.name, s.host, s.port]),
        columns: [
            {
                title: "Name",
                render: (data, type, row) => {
                    if (type === "display")
                        return `<a href=/displayService.html?s=${data}>${data}</a>`;
                    return data;
                }
            },
            { title: "Host" },
            { title: "Port" }
        ],
    });
}

function handle_autoscroll() {
    window.auto_scroll = true;
    window.ignore_next_scroll_event = false;

    window.addEventListener("scroll", () => {
        if(!window.ignore_next_scroll_event) {
            window.auto_scroll = false;
            // if the user scrolls to the bottom of the page, we reenable auto scroll
            if ((window.innerHeight + Math.round(window.scrollY)) >= document.body.offsetHeight) {
                window.auto_scroll = true;
            }
        }
        window.ignore_next_scroll_event = false;
    });
}

function scroll_tobottom() {
    if (window.auto_scroll) {
        window.ignore_next_scroll_event = true;
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: "auto"
        });
    }
}

function render_column_chooser(table) {
    const columns = table.settings().init().columns;
    const parent = $("#columns-chooser");
    columns.forEach((c, i) => {
        const div = $('<div />').appendTo(parent);
        $('<input />', { type: 'checkbox', value: i, checked: true }).appendTo(div).change(function () {
            table.column(this.value).visible(this.checked);
            table.columns.adjust().draw();
        });
        $('<label />', { text: c.title }).appendTo(div);
    });
}

function allColumns(status) {
    $("#columns-chooser input").prop("checked", status);
    const table = $("#table-service").DataTable();
    table.columns().every((i) => {
        table.column(i).visible(status);
    });
    table.columns.adjust().draw();
}

function onlyChangedColumns() {
    $("#columns-chooser input").each((i, e) => {
        $(e).prop("checked", changed_columns.has(i));
    });
    const table = $("#table-service").DataTable();
    table.columns().every((i) => {
        table.column(i).visible(changed_columns.has(i));
    });
    table.columns.adjust().draw();
}

function handleNewStatus(status) {
    sniffing = status;
    $("#status").text(status ? "Capturing..." : "Stopped");
    $("#status-button").text(status ? "Stop capturing" : "Start capturing")
    $("#status-button").off('click').on('click', () => {
        setStatus(!status).then((newStatus) => {
            handleNewStatus(newStatus);
        });
    })
}

async function initStatus() {
    getStatus().then((status) => handleNewStatus(status));
}

sniffing = false;
const changed_columns = new Set();

async function displayService(service_name) {
    $("#service-name").text(service_name);
    $("#btn-inject").click(() => window.open(`sendMessage.html?s=${service_name}`, '_blank'))
    const schema = await getSchema(service_name);

    const table = $("#table-service").DataTable({
        columns: [
            {
                title: "#",
                render: (data, type, row) => {
                    if (type === "display")
                        return `<a target="_blank" href=/sendMessage.html?s=${service_name}&m=${btoa(JSON.stringify(row))}>${data}</a>`;
                    return data
                }
            },
            ...schema.map((s) => ({ title: s.name }))
        ],
        scrollX: true,
        ordering: true,
        paging: false,
        info: false,
        fixedHeader: true
    });

    window.last_id = undefined;

    function updateTableData(first = false) {
        if (first || sniffing) {
            getMessages(service_name, window.last_id).then((messages) => {
                if (messages.length > 0) {
                    window.last_id = messages[messages.length - 1][0];
                    table.rows.add(messages.map(m => ([m[0], ...m[1]])));
                    table.draw(false);
                    hilight_changes(table);
                    if (!first) {
                        scroll_tobottom();
                    }
                }
            });
        }
    }

    initStatus();
    render_column_chooser(table);
    handle_autoscroll();
    updateTableData(true);
    setInterval(updateTableData, 1000);
}

function hilight_changes(table) {
    table.rows().every((i) => {
        if (i > 0) {
            const prevRowData = table.row(i-1).data();
            const row = table.row(i);
            const rowData = row.data();
            // skip the first column (id)
            for(var j = 1; j < rowData.length; j++) {
                if (prevRowData[j] !== rowData[j]) {
                    const cell = table.cell({
                        row: i,
                        column: j
                    }).node();
                    $(cell).addClass("changed");
                    changed_columns.add(j);
                }
            }
        }
    });
    changed_columns.forEach((j) => $(table.column(j).header()).addClass("column-changed"));
    $("#columns-chooser").children().each((i, elem) => {
        if (changed_columns.has(i)) {
            $(elem).addClass("column-changed");
        } else {
            $(elem).removeClass("column-changed");
        }
    })
}