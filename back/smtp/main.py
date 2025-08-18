# Entrypoint for SMTP service
from smtp_server import start_smtp_server

if __name__ == "__main__":
    print("Starting SMTP server...")
    smtp_controller = start_smtp_server()
    # Keep the process alive to handle SMTP
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down SMTP server...")
        smtp_controller.stop()
