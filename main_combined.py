#!/usr/bin/env python3
"""
Combined entry point for running both FastAPI API server and SMTP server together.
This is designed for Docker containers where both services need to run in the same process.
"""
import logging
import os
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
        """Start SMTP server in a separate thread with isolated event loop."""
        import asyncio
        
        def run_smtp_with_loop():
            """Run SMTP server in its own event loop."""
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use 0.0.0.0 for Docker container accessibility
                self.smtp_controller = start_smtp_server(host="0.0.0.0", port=1025)
                logging.info("SMTP server started successfully")
                self.smtp_ready.set()
                
                # Keep the event loop running until shutdown
                while not self.shutdown_flag:
                    time.sleep(0.1)
                    
            except Exception as e:
                logging.error(f"Failed to start SMTP server: {e}")
                self.smtp_failed.set()
                self.shutdown_flag = True
            finally:
                # Properly close the event loop
                try:
                    if loop.is_running():
                        loop.stop()
                    if not loop.is_closed():
                        loop.close()
                except Exception as e:
                    logging.error(f"Error closing SMTP event loop: {e}")
        
        try:
            run_smtp_with_loop()
        except Exception as e:
            logging.error(f"Error in SMTP thread: {e}")
            self.smtp_failed.set()
            self.shutdown_flag = True

    def stop_smtp(self):
        """Stop SMTP server."""
        if self.smtp_controller:
            try:
                self.smtp_controller.stop()
                logging.info("SMTP server stopped")
            except Exception as e:
                logging.error(f"Error stopping SMTP server: {e}")

    def signal_handler_sync(self, signum, frame):
        """Handle shutdown signals."""
        logging.info(f"Received signal {signum}, shutting down...")
        self.shutdown_flag = True

    def run_combined(self):
        """Run both servers together."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler_sync)
        signal.signal(signal.SIGTERM, self.signal_handler_sync)

        api_process = None
        try:
            # Start SMTP server in background thread
            smtp_thread = threading.Thread(target=self.start_smtp, daemon=True)
            smtp_thread.start()

            # Wait for SMTP server to start or fail (max 10 seconds)
            logging.info("Waiting for SMTP server to start...")
            ready_events = [self.smtp_ready, self.smtp_failed]
            for _ in range(100):  # 10 seconds total
                if any(event.is_set() for event in ready_events):
                    break
                time.sleep(0.1)

            if self.smtp_failed.is_set():
                logging.error("SMTP server failed to start, exiting...")
                return
            elif not self.smtp_ready.is_set():
                logging.error("SMTP server startup timed out, exiting...")
                return

            # Start API server using subprocess
            logging.info("Starting FastAPI server via subprocess...")
            api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "main:create_app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--factory"
            ], 
            # Prevent asyncio event loop inheritance issues
            preexec_fn=None if sys.platform == "win32" else os.setsid,
            # Close file descriptors to prevent conflicts
            close_fds=True)

            # Keep process alive and monitor both services
            while not self.shutdown_flag:
                # Check if API process is still running
                poll_result = api_process.poll()
                if poll_result is not None:
                    logging.error(f"API server process died unexpectedly with exit code {poll_result}")
                    # Give some time for proper cleanup before breaking
                    time.sleep(2)
                    break
                time.sleep(1)

        except Exception as e:
            logging.error(f"Error in combined server: {e}")
            import traceback
            logging.error(traceback.format_exc())
        finally:
            # Clean shutdown with proper process handling
            if api_process is not None:
                try:
                    if api_process.poll() is None:
                        logging.info("Terminating API server...")
                        # Try graceful shutdown first
                        api_process.terminate()
                        try:
                            api_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            logging.warning("API server didn't terminate gracefully, killing...")
                            api_process.kill()
                            api_process.wait(timeout=2)
                except Exception as e:
                    logging.error(f"Error during API server shutdown: {e}")
                    
            # Stop SMTP server
            self.stop_smtp()
            logging.info("Combined server shutdown complete")


def main():
    """Main entry point."""
    server = CombinedServer()
    server.run_combined()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
