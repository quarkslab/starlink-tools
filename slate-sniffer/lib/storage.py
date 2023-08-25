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

import sys
from threading import Lock
from .slate import Slate
from .service import Service
from .sniffer import Sniffer
from .utils import binary_search

MAX_MSG_IN_QUEUE = 100


class SingleSlateStore:
    def __init__(self, slate: Slate, max_msg_in_queue=MAX_MSG_IN_QUEUE):
        self.slate = slate
        self.max_msg_in_queue = max_msg_in_queue
        self.current_msg_id = 0
        self.messages = []
        self.lock = Lock()

    def insert(self, message):
        self.lock.acquire()
        self.messages.append((self.current_msg_id, message))
        self.current_msg_id += 1

        # if the max size has been reached, remove 10% of the elements
        if len(self.messages) > self.max_msg_in_queue:
            self.messages = self.messages[int(self.max_msg_in_queue / 10) :]
        self.lock.release()

    def get_messages(self, last_id: int = None) -> list:
        if last_id == None or len(self.messages) == 0 or last_id < self.messages[0][0]:
            return self.messages
        elif last_id >= self.messages[-1][0]:
            return []
        else:
            # here I need to lock
            self.lock.acquire()
            index = binary_search(self.messages, last_id, lambda x: x[0])
            self.lock.release()
            if index != -1:
                return self.messages[index + 1 :]
            else:
                return []


class SlateStorage:
    def __init__(self, slates: list[Slate]):
        self.store = dict()

        for slate in slates:
            self.store.update({slate.service.name: SingleSlateStore(slate)})

    def handle_message(self, name: str, message):
        store = self.store.get(name)
        if store == None:
            raise Exception(f"Invalid slate name: {name}")
        else:
            store.insert(message)
            # print(f"Message received for slate {name}, # messages in queue: {len(store.messages)}")

    def get_messages(self, name: str, last_id: int = None) -> list | None:
        store: SingleSlateStore = self.store.get(name)
        if store == None:
            return None
        return store.get_messages(last_id)

    def get_schema(self, name: str) -> list | None:
        store = self.store.get(name)
        if store == None:
            return None
        return store.slate.message_parser.params


def main():
    services = Service.parse("./config/service_directory")
    slates = list(map(Slate.from_service, services))
    sniffer = Sniffer(slates)
    store = SlateStorage(slates)

    def handler(name, message):
        store.handle_message(name, message)

    sniffer.sniff(handler)


if __name__ == "__main__":
    main()
