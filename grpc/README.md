# GRPC client

Some examples of how to interact with the frontend process in the User Terminal using gRPC.

## Dependencies:

- Python's `grpc_tools` package
- Python's `grpc` package
- `grpc_cli` (only for the bash version of the `sw_update` script)

## Setting up the project

To be able to send messages, you will need the message's definitions.

You can get them in two ways:

1. By asking the reflection server on a live dish, using `grpcurl`, for example
2. By dumping the firmware of the device and extracting them from the `user_terminal_frontend` binary, using `pbtk`, for example.

Once you have them, copy them as they are in the `Protos` folder.

Then generate Python stubs using the script `generate_protos.py`.