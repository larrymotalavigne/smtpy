# Entrypoint for smtpy
from smtp_server import start_smtp_server

if __name__ == "__main__":
    print("Starting smtpy (SMTP server and API)...")
    smtp_controller = start_smtp_server()
    # TODO: Start FastAPI app (API/admin panel)
    # For now, keep the process alive to handle SMTP
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down SMTP server...")
        smtp_controller.stop()
    # Note: For production, use proper async server and graceful shutdown 