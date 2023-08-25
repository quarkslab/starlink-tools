# Copyright 2023 Quarkslab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, abort, request, Response, send_from_directory, redirect
from threading import Thread
import argparse
import json
from typing import Callable
from lib.sniffer import Sniffer
from lib.service import Service
from lib.slate import Slate
from lib.injector import Injector
from lib.storage import SlateStorage
from lib import config

thread_should_stop = False
sniff_thread = None


def thread_should_stop_cb():
    global thread_should_stop
    return thread_should_stop


def start_thread(sniffer: Sniffer, handler: Callable[[str, tuple], None]):
    global sniff_thread
    global thread_should_stop
    thread_should_stop = False
    sniff_thread = Thread(
        target=Sniffer.sniff, args=(sniffer, handler, thread_should_stop_cb)
    )
    sniff_thread.start()


def main():
    services = Service.parse("./config/service_directory.json")
    slates = list(map(Slate.from_service, services))
    sniffer = Sniffer(slates)
    store = SlateStorage(slates)
    injector = Injector(slates)

    def handler(name: str, message: tuple):
        store.handle_message(name, message)

    api = Flask(__name__)

    json_encoder = json.JSONEncoder(default=lambda o: o.__dict__)

    @api.route("/status", methods=["GET", "POST"])
    def handle_status():
        global sniff_thread
        global thread_should_stop
        if request.method == "GET":
            return Response(
                json_encoder.encode(
                    {"status": sniff_thread != None and sniff_thread.is_alive()}
                ),
                mimetype="application/json",
            )
        elif request.method == "POST":
            data = request.json
            newStatus = data.get("status")
            if newStatus == True:
                start_thread(sniffer, handler)
            else:
                thread_should_stop = True
            return Response(
                json_encoder.encode({"status": newStatus}), mimetype="application/json"
            )

    @api.route("/services", methods=["GET"])
    def get_services():
        return Response(json_encoder.encode(services), mimetype="application/json")

    @api.route("/services/<name>/messages", methods=["GET"])
    def get_messages(name: str):
        last_id = request.args.get("last_id", default=None, type=int)
        messages = store.get_messages(name, last_id)
        if messages != None:
            return Response(json_encoder.encode(messages), mimetype="application/json")
        else:
            abort(404)

    @api.route("/services/<name>/schema", methods=["GET"])
    def get_schema(name: str):
        schema = store.get_schema(name)
        if schema:
            return Response(
                json_encoder.encode(
                    list(map(lambda x: {"name": x.name, "type": x.dtype.name}, schema))
                ),
                mimetype="application/json",
            )
        else:
            abort(404)

    @api.route("/inject", methods=["POST"])
    def inject():
        data = request.json
        service = data["service"]
        message = data["message"]
        try:
            injector.send_message(service, tuple(message))
            return ("", 200)
        except:
            abort(400)

    @api.route("/", defaults={"path": "index.html"})
    @api.route("/<path:path>", methods=["GET"])
    def static_files(path):
        return send_from_directory("./frontend", path)

    api.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="server",
        description="Sniff slate messages in a remote dish and present them in a web interface",
    )
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    args = parser.parse_args()
    config.verbose = args.verbose
    main()
