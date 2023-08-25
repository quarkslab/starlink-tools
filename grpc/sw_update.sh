#!/bin/bash

# Copyright 2023 Quarkslab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

## Send a software update package to the dish
## through the user_terminal_frontend gRPC

set -e

CHUNK_SIZE=16384

function repeat {
    # Usage: repeat "ABC" 3 --> "ABCABCABC"
    for i in $(seq 0 $2); do
        echo -n $1;
    done
}

function message {
    if [ $# -le 1 ]; then
        echo "usage: message data[string] open[bool] close[bool]"
    fi

    ENCODED_DATA=`echo -n "$1" | base64 -w 0`

    jq -n \
        --arg data "$ENCODED_DATA" \
        --arg open "$2" \
        --arg close "$3" \
        '{id: "1",targetId: "lmao",softwareUpdate: {streamId: "2", data: $data, open: $open, close: $close}}'
}

function send_message {
    if [ $# -le 0 ]; then
        echo "usage: send_message data[string]"
    fi

    LEN=${#1}

    if [ $LEN -le $CHUNK_SIZE ]; then
        # send everything in one message
        MESSAGE=`message "$1" true true`
        
        echo "Sending: "
        echo $MESSAGE

        echo $MESSAGE | grpc_cli --protofiles Protos/device.proto --json_input call 192.168.100.1:9200 SpaceX.API.Device.Device.Handle
    else
        # split into chunks
        for i in $(seq 0 $CHUNK_SIZE $LEN); do
            OPEN=false
            CLOSE=false

            if [ $i -eq 0 ]; then
                OPEN=true
            fi

            if (( $i + $CHUNK_SIZE >= $LEN )); then
                CLOSE=true
            fi

            MESSAGE=`message "${1:$i:$CHUNK_SIZE}" $OPEN $CLOSE`

            echo "Sending: "
            echo $MESSAGE

            echo $MESSAGE | grpc_cli --protofiles Protos/device.proto --json_input call 192.168.100.1:9200 SpaceX.API.Device.Device.Handle
        done
    fi
}

send_message `repeat A 132073`