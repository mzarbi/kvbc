import os
import signal

import Pyro5

from core.config import logger
from core.stores import KeyValueServer


def start_server(label, plugin=None, **plugin_kwargs):
    try:
        daemon = Pyro5.server.Daemon(host=os.getenv('KVSTORE_HOST', 'localhost'), port=int(os.getenv('KVSTORE_PORT', 6666)))
        if plugin:
            store = plugin(label, **plugin_kwargs)
        else:
            store = KeyValueServer(label)
        uri = daemon.register(store)
        logger.info(f"Server is ready. URI = {uri}")

        def handle_signals(signum, frame):
            logger.info("Shutdown signal received, shutting down the server and cleanup thread...")
            if store.cleanup_thread:
                store.cleanup_thread.stop()
            daemon.shutdown()
            logger.info("Server cleanly shut down.")

        signal.signal(signal.SIGINT, handle_signals)
        signal.signal(signal.SIGTERM, handle_signals)

        daemon.requestLoop()
    except (Pyro5.errors.CommunicationError, Pyro5.errors.DaemonError) as e:
        logger.error(f"Pyro5 error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    start_server("kv.nas")