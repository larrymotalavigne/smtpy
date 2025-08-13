#!/usr/bin/env python3
"""
Combined entry point for running both FastAPI API server and SMTP server together.
This is designed for Docker containers where both services need to run in the same process.
"""
import asyncio
import signal
import subprocess
import sys
import threading
import time

from smtp_server import start_smtp_server
from utils.logging_config import get_logger

logger = get_logger("combined")


class CombinedServer:
    """Manages both FastAPI and SMTP servers in a single process."""
    
    def __init__(self):
        self.smtp_controller = None
        self.api_server = None
        self.shutdown_flag = False
        
    def start_smtp(self):
        """Start SMTP server in a separate thread."""
        try:
            # Use 0.0.0.0 for Docker container accessibility
            self.smtp_controller = start_smtp_server(host="0.0.0.0", port=1025)
            logger.info("SMTP server started successfully")
        except Exception as e:
            logger.error(f"Failed to start SMTP server: {e}")
            raise
            
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
        sys.exit(1)