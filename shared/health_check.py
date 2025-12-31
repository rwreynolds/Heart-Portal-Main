"""
Health check endpoint functionality for all Heart Portal components
Enables monitoring and automated health checks
"""

from typing import Dict, Any, Callable, Optional
from flask import Flask, jsonify, Response
from datetime import datetime
import sys
from database import DatabaseConfig


def create_health_check_endpoint(
    app: Flask,
    component_name: str,
    database_url: Optional[str] = None,
    custom_checks: Optional[Dict[str, Callable[[], bool]]] = None
) -> None:
    """
    Add a /health endpoint to a Flask application

    Args:
        app: Flask application instance
        component_name: Name of the component (e.g., 'sodium-tracker')
        database_url: Optional database URL to test connectivity
        custom_checks: Optional dictionary of custom health check functions

    Usage:
        from shared.health_check import create_health_check_endpoint

        app = Flask(__name__)
        create_health_check_endpoint(
            app,
            'sodium-tracker',
            database_url=os.getenv('DATABASE_URL_SODIUM'),
            custom_checks={'usda_api': check_usda_api}
        )
    """

    @app.route('/health')
    def health_check() -> tuple[Response, int]:
        """
        Health check endpoint

        Returns JSON with:
        - status: 'healthy' or 'unhealthy'
        - component: component name
        - timestamp: current timestamp
        - checks: results of various health checks

        Status codes:
        - 200: All checks passed
        - 503: One or more checks failed
        """
        checks: Dict[str, Any] = {}
        overall_healthy = True

        # Basic system check
        checks['python'] = {
            'status': 'ok',
            'version': sys.version.split()[0]
        }

        # Database connectivity check
        if database_url:
            db_check = check_database(database_url)
            checks['database'] = db_check
            if not db_check['healthy']:
                overall_healthy = False

        # Custom checks
        if custom_checks:
            for check_name, check_func in custom_checks.items():
                try:
                    result = check_func()
                    checks[check_name] = {
                        'status': 'ok' if result else 'failed',
                        'healthy': result
                    }
                    if not result:
                        overall_healthy = False
                except Exception as e:
                    checks[check_name] = {
                        'status': 'error',
                        'healthy': False,
                        'error': str(e)
                    }
                    overall_healthy = False

        response_data = {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'component': component_name,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }

        status_code = 200 if overall_healthy else 503
        return jsonify(response_data), status_code


def check_database(database_url: str) -> Dict[str, Any]:
    """
    Check database connectivity

    Args:
        database_url: Database connection string

    Returns:
        Dictionary with check results
    """
    try:
        db = DatabaseConfig(database_url)
        conn = db.get_connection()

        # Try a simple query
        cursor = db.dict_cursor(conn)
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        db.release_connection(conn)

        return {
            'status': 'ok',
            'healthy': True,
            'connected': True
        }
    except Exception as e:
        return {
            'status': 'error',
            'healthy': False,
            'connected': False,
            'error': str(e)
        }
