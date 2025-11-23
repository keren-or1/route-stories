"""
Flask application factory for Route Stories web UI.
"""

import os
import sys
from pathlib import Path
from flask import Flask

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.utils import setup_logger


def create_app():
    """
    Create and configure Flask application.

    Returns:
        Flask application instance
    """
    # Create Flask app
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / 'templates'),
        static_folder=str(Path(__file__).parent / 'static')
    )

    # Load configuration
    try:
        settings = get_settings()
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        app.config['SETTINGS'] = settings
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file (copy from .env.example)")
        print("2. Added your GOOGLE_MAPS_API_KEY")
        print("3. Added your ANTHROPIC_API_KEY")
        sys.exit(1)

    # Setup logging
    logger = setup_logger(
        log_level=settings.log_level,
        log_dir=settings.logs_dir,
        enable_console=True,
        enable_file=True
    )

    app.logger.info("Route Stories Web UI - Starting")

    # Register blueprints
    from src.web.routes import main_bp
    app.register_blueprint(main_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500

    return app
