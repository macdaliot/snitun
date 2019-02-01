"""Connector to end resource."""
from contextlib import suppress
import asyncio

from ..multiplexer.channel import MultiplexerChannel
from ..exceptions import MultiplexerTransportClose, MultiplexerTransportError


class Connector:
    """Connector to end resource."""

    def __init__(self, end_host: str, end_port=None):
        """Initialize Connector."""
        self._loop = asyncio.get_event_loop()
        self._end_host = end_host
        self._end_port = end_port or 443

    async def handler(self, channel: MultiplexerChannel) -> None:
        """Handle new connection from SNIProxy."""
        from_endpoint = None
        from_peer = None

        # Open connection to endpoint
        try:
            reader, writer = await asyncio.open_connection(
                host=self._end_host, port=self._end_port)
        except OSError:
            _LOGGER.error("Can't connect to endpoint %s:%s", self._end_host,
                          self._end_port)
            return

        try:
            # Process stream from multiplexer
            while not writer.transport.is_closing():
                if not from_endpoint:
                    from_endpoint = self._loop.create_task(reader.read(4096))
                if not from_peer:
                    from_peer = self._loop.create_task(channel.read())

                # Wait until data need to be processed
                await asyncio.wait([from_endpoint, from_peer],
                                   return_when=asyncio.FIRST_COMPLETED)

                # From proxy
                if from_endpoint.done():
                    if from_endpoint.exception():
                        raise from_endpoint.exception()

                    await channel.write(from_endpoint.result())
                    from_endpoint = None

                # From peer
                if from_peer.done():
                    if from_peer.exception():
                        raise from_peer.exception()

                    writer.write(from_peer.result())
                    from_peer = None

        except MultiplexerTransportError:
            _LOGGER.debug("Multiplex Transport Error for %s", channel.uuid)

        except MultiplexerTransportClose:
            _LOGGER.debug("Peer close connection for %s", channel.uuid)

        finally:
            if from_peer and not from_peer.done():
                from_peer.cancel()
            if from_endpoint and not from_endpoint.done():
                from_endpoint.cancel()
            with suppress(OSError):
                writer.close()