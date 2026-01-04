import uvicorn
import sys
import os
import multiprocessing
import traceback
import logging
import tempfile

# Setup logging to a temp file so we can debug even if stdout is lost
log_file = os.path.join(tempfile.gettempdir(), 'photonflow_server.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, filemode='w')

logging.info("Starting run.py")
logging.info(f"CWD: {os.getcwd()}")
logging.info(f"sys.path: {sys.path}")
logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")

try:
    # Add src to path so we can import photonflow
    # When running from source, we need to add src.
    # When running as frozen (PyInstaller), dependencies are bundled.
    if not getattr(sys, 'frozen', False):
        sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

    logging.info("Importing app...")
    from photonflow.server.app import app
    logging.info("App imported successfully.")

    if __name__ == "__main__":
        multiprocessing.freeze_support()
        
        # Debug: Log Parent PID periodically to see if we can use it for watchdog
        import threading
        import time
        def log_ppid():
            while True:
                try:
                    ppid = os.getppid()
                    logging.info(f"Current PPID: {ppid}")
                except Exception as e:
                    logging.error(f"Failed to get PPID: {e}")
                time.sleep(5)
        
        debug_thread = threading.Thread(target=log_ppid, daemon=True)
        debug_thread.start()

        port = 8000
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                pass
                
        logging.info(f"Starting server on port {port}...")
        
        # Add stdout handler so user can see logs in terminal
        root_logger = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

        # Use log_config=None to prevent uvicorn from overwriting our logging config
        try:
            # Explicitly use asyncio loop to avoid auto-detection issues in frozen app
            uvicorn.run(app, host="127.0.0.1", port=port, log_config=None, workers=1, loop="asyncio")
            logging.info("Uvicorn run finished normally.")
        except Exception as e:
            logging.error(f"Uvicorn run failed: {e}", exc_info=True)
            raise

except Exception as e:
    logging.error("Failed to start server", exc_info=True)
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
