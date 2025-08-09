import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Configures logging for the application based on the DEBUG flag.
    """
    if app.config['DEBUG']:
        # In debug mode, log to a file with rotation
        log_dir = os.path.join(app.root_path, '..', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, 'app_debug.log')
        
        # Rotate logs: 5 files, 1MB each
        file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Debug logging enabled, writing to file.')

    else:
        # In production, log to stdout
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        stream_handler.setFormatter(formatter)
        
        # Remove default handlers to avoid duplicate logs
        app.logger.handlers.clear()
        
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO) # Log INFO and above to console
        app.logger.info('Production logging enabled, writing to stdout.')

    # Ensure all unhandled exceptions are logged
    def log_exception(exc_type, exc_value, exc_traceback):
        app.logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

    import sys
    sys.excepthook = log_exception