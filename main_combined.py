#!/usr/bin/env python3
"""
Combined entry point for running both FastAPI API server and SMTP server together.
This is designed for Docker containers where both services need to run in the same process.
"""
import logging
import signal
import subprocess
import sys
import threading
import time

from smtp_server import start_smtp_server

# Initialize logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("smtpy.combined")


class CombinedServer:
    """Manages both FastAPI and SMTP servers in a single process."""

    def __init__(self):
        self.smtp_controller = None
        self.api_server = None
        self.shutdown_flag = False
        self.smtp_ready = threading.Event()
        self.smtp_failed = threading.Event()

    def start_smtp(self):
        """Start SMTP server in a separate thread."""
        try:
            # Use 0.0.0.0 for Docker container accessibility
            self.smtp_controller = start_smtp_server(host="0.0.0.0", port=1025)
            logger.info("SMTP server started successfully")
            self.smtp_ready.set()
        except Exception as e:
            logger.error(f"Failed to start SMTP server: {e}")
            self.smtp_failed.set()
            # Set shutdown flag to terminate the main process if SMTP fails
            self.shutdown_flag = True

    def stop_smtp(self):
        """Stop SMTP server."""
        if self.smtp_controller:
            try:
                self.smtp_controller.stop()
                logger.info("SMTP server stopped")
            except Exception as e:
                logger.error(f"Error stopping SMTP server: {e}")

    def signal_handler_sync(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_flag = True

    def run_combined(self):
        """Run both servers together."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler_sync)
        signal.signal(signal.SIGTERM, self.signal_handler_sync)

        try:
            # Start SMTP server in background thread
            smtp_thread = threading.Thread(target=self.start_smtp, daemon=True)
            smtp_thread.start()

            # Wait for SMTP server to start or fail (max 10 seconds)
            logger.info("Waiting for SMTP server to start...")
            ready_events = [self.smtp_ready, self.smtp_failed]
            for _ in range(100):  # 10 seconds total
                if any(event.is_set() for event in ready_events):
                    break
                time.sleep(0.1)

            if self.smtp_failed.is_set():
                logger.error("SMTP server failed to start, exiting...")
                return
            elif not self.smtp_ready.is_set():
                logger.error("SMTP server startup timed out, exiting...")
                return

            # Start API server using subprocess
            logger.info("Starting FastAPI server via subprocess...")
            api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "main:create_app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--factory"
            ])

            # Keep process alive and monitor both services
            while not self.shutdown_flag:
                # Check if API process is still running
                if api_process.poll() is not None:
                    logger.error("API server process died unexpectedly")
                    break
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error in combined server: {e}")
            raise
        finally:
            # Clean shutdown
            if 'api_process' in locals() and api_process.poll() is None:
                logger.info("Terminating API server...")
                api_process.terminate()
                api_process.wait(timeout=5)
            self.stop_smtp()
            logger.info("Combined server shutdown complete")


def main():
    """Main entry point."""
    server = CombinedServer()
    server.run_combined()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
