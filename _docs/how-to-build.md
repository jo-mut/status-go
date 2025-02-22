# Build status-go

## Introduction

status-go is an underlying part of Status. It heavily depends on [go-ethereum](https://github.com/ethereum/go-ethereum/) which is [forked](https://github.com/status-im/go-ethereum) and slightly modified by us.

## Build status-go

### 1. Requirements

* Nix (Installed automatically)
* Docker (only if cross-compiling).

> go is provided by Nix

### 2. Clone the repository

```shell
git clone https://github.com/status-im/status-go
cd status-go
```

### 3. Set up build environment

status-go uses nix in the Makefile to provide every tools required.

### 4. Build the statusd CLI

To get started, let’s build the Ethereum node Command Line Interface tool, called `statusd`.

```shell
make statusgo
```

Once that is completed, you can run it straight away with a default configuration by running

```shell
build/bin/statusd
```

### 5. Build a library for Android and iOS

```shell
make install-gomobile
make statusgo-cross # statusgo-android or statusgo-ios to build for specific platform
```

## Debugging

### IDE Debugging

If you’re using Visual Studio Code, you can rename the [.vscode/launch.example.json](https://github.com/status-im/status-go/blob/develop/.vscode/launch.example.json) file to .vscode/launch.json so that you can run the statusd server with the debugger attached.

### Android debugging

In order to see the log files while debugging on an Android device, do the following:

* Ensure that the app can write to disk by granting it file permissions. For that, you can for instance set your avatar from a file on disk.
* Connect a USB cable to your phone and make sure you can use adb.
Run

```shell
adb shell tail -f sdcard/Android/data/im.status.ethereum.debug/files/Download/geth.log
```

## Testing

First, make sure the code is linted properly:

```shell
make lint
```

Next, run unit tests:

```shell
make test
```

Unit tests can also be run using `go test` command. If you want to launch specific test, for instance `RPCSendTransactions`, use the following command:

```shell
go test -tags gowaku_skip_migrations -v ./api/ -testify.m ^RPCSendTransaction$
```

Note -testify.m as [testify/suite](https://godoc.org/github.com/stretchr/testify/suite) is used to group individual tests.

Finally, run e2e tests:

```shell
make test-e2e
```

There is also a command to run all tests in one go:

```shell
make ci
```

### Running

Passing the `-h` flag will output all the possible flags used to configure the tool. Although the tool can be used with default configuration, you’ll probably want to delve into the configuration and modify it to your needs.

Node configuration - be it through the CLI or as a static library - is done through JSON files following a precise structure. At any point, you can add the `-version` argument to `statusd` to get an output of the JSON configuration in use. You can pass multiple configuration files which will be applied in the order in which they were specified.

There are a few standard configuration files located in the config/cli folder to get you started. For instance you can pass `-c les-enabled.json` to enable LES mode.

For more details on running a Status Node see [the dedicated page](https://github.com/status-im/status-go/blob/develop/_examples/README.md#run-waku-node).

### Testing with an Ethereum network

To setup accounts passphrase you need to setup an environment variable: `export ACCOUNT_PASSWORD="secret_pass_phrase"`.

To test statusgo using a given network by name, use:

```shell
make ci networkid=rinkeby
```

To test statusgo using a given network by number ID, use:

```shell
make ci networkid=3
```

If you have problems running tests on public network we suggest reading e2e guide.
