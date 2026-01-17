#!/usr/bin/env python3
"""PhotonFlow backend server entry point with loading progress."""
import uvicorn
import sys
import os
import multiprocessing
import traceback
import logging
import tempfile

def emit_stage(stage: str) -> None:
    """Emit loading stage marker for Tauri to parse."""
    print(f"STAGE:{stage}", flush=True)

# Setup logging to a temp file so we can debug even if stdout is lost
log_file = os.path.join(tempfile.gettempdir(), 'photonflow_server.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, filemode='w')

logging.info("Starting run.py")
emit_stage("init")

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
    emit_stage("imports")
    from photonflow.server.app import app
    logging.info("App imported successfully.")
    
    # Ensure blocks are registered
    emit_stage("blocks")
    from photonflow.blocks import registry
    _ = registry.types()  # Trigger block registration
    logging.info(f"Registered {len(registry.types())} block types")

    if __name__ == "__main__":
        multiprocessing.freeze_support()
        
        # Debug: Log Parent PID periodically to see if we can use it for watchdog


        # Watchdog: Exit if stdin is closed (parent process dies)
        import threading
        def stdin_watchdog():
            try:
                # Read until EOF
                for _ in sys.stdin:
                    pass
            except Exception:
                pass
            logging.info("Parent process closed stdin. Exiting...")
            os._exit(0) # Force exit

        watchdog_thread = threading.Thread(target=stdin_watchdog, daemon=True)
        watchdog_thread.start()

        port = 8000
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                pass
                
        logging.info(f"Starting server on port {port}...")
        emit_stage("server")
        
        # Add stdout handler so user can see logs in terminal
        root_logger = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

        # Define lifespan context manager for startup/shutdown events
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def lifespan(application):
            # Startup
            emit_stage("ready")
            logging.info("Server is ready")
            yield
            # Shutdown (if needed)
            logging.info("Server shutting down")

        # Assign the lifespan to the app
        app.router.lifespan_context = lifespan

        # Use log_config=None to prevent uvicorn from overwriting our logging config
        try:
            # Explicitly use asyncio loop to avoid auto-detection issues in frozen app
            uvicorn.run(
                app, 
                host="127.0.0.1", 
                port=port, 
                log_config=None, 
                loop="asyncio"
            )
            logging.info("Uvicorn run finished normally.")
        except Exception as e:
            logging.error(f"Uvicorn run failed: {e}", exc_info=True)
            raise

except Exception as e:
    logging.error("Failed to start server", exc_info=True)
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
