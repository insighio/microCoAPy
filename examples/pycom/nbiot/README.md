Requires submodule initialization:

```
git submodule update --init --recursive
```

The implementation with the custom sockets that utilize AT commands uses project [microATsocket](https://github.com/insighio/microATsocket) to be able to send data using IPv6 addresses. In case of CoAP messages, microATsocket is advised to be used with custom build firmware with [Pull Request 429](https://github.com/pycom/pycom-micropython-sigfox/pull/429) than enables long message to be send over AT commands.
