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

async function constructForm(service_name, message) {
    $("#service-name").text(service_name);
    const schema = await getSchema(service_name);

    if (message !== undefined && message !== null) {
        message = JSON.parse(atob(message));
        message = message.slice(1);
    } else {
        message = schema.map((param) => getDefault(param.type));
    }
    window.service = service_name;
    window.schema = schema;
    window.message = message;

    const form = $("#msg-form");
    form.submit(formSubmit);

    const elements = $("#form-elements");

    for (let i = 0; i < schema.length; i++) {
        const div = $("<div />").appendTo(elements).addClass("input-elem");
        if (schema[i].type == "BOOL") {
            $('<label />', { text: `${schema[i].name} (${schema[i].type.toLowerCase()})` }).appendTo(div);
            $('<input />', { type: 'checkbox', value: i, checked: message[i] !== 0 && message[i] !== false }).appendTo(div).change(function () {
                window.message[this.value] = this.checked;
            });
        } else {
            $('<label />', { text: `${schema[i].name} (${schema[i].type.toLowerCase()})` }).appendTo(div);
            $("<input/>", {
                type: 'number',
                step: schema[i].type.includes("INT") ? "1" : "0.00000001",
                value: message[i]
            }).appendTo(div).change(function () {
                const parsed = schema[i].type.includes("INT") ? parseInt(this.value) : parseFloat(this.value);
                window.message[i] = parsed;
                this.value = parsed;
            });
        }
    }
}

function getDefault(type) {
    switch (type) {
        case "BOOL":    return false;
        default:        return 0;
    }
}

function formSubmit(e) {
    e.preventDefault();
    const submit = $("#form-submit");
    const status = $("#form-status");
    submit.prop("disabled", true);
    status.text("Sending...");

    injectMessage(window.service, window.message).then(() => {
        status.text("Sent!");
    }).catch(() => {
        status.text("Error!!!");
    }).finally(() => {
        submit.prop("disabled", false);
    });
}

function injectMessage(service, message) {
    return new Promise((resolve, reject) => {
        $.ajax("/inject", {
            data : JSON.stringify({
                service,
                message
            }),
            contentType : 'application/json',
            type : 'POST',
            success: (data) => {
                resolve();
            },
            error: () => {
                reject();
            }
        });
    });
}