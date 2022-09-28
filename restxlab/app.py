from flask import Flask
from apiv1 import blueprint as apiv1
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from core.database import db_session, init_db
import logging
import sys
import os

# app factory
def create_app(test_config=None):
    # configure root logger
    logging.basicConfig(format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z',
        stream=sys.stdout,
        level=logging.DEBUG)

    app_instance = Flask(__name__)
    app_instance.wsgi_app = ProxyFix(app_instance.wsgi_app)
    app_instance.register_blueprint(apiv1, url_prefix='/api/v1')


    # setup logging handler
    #handler = logging.StreamHandler(sys.stdout)
    #handler.setFormatter(logging.Formatter(
     #   '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # clear any default handlers and configure app   
    #app_instance.logger.handlers.clear()
    #app_instance.logger.addHandler(handler)
    #app_instance.logger.setLevel(logging.DEBUG)
    #app_instance.logger.name = 'app'
    
    # enable CORS
    CORS(app_instance)

    init_db()

    # sqlalchemy teardown
    @app_instance.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # commit transaction up completion
    @app_instance.after_request
    def after_request(response):
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            app_instance.logger.exception("Request failed rolling back db transactions")
            response = default_error_handler(e)
        return response

    # default error handler AP response
    @app_instance.errorhandler(Exception)
    def default_error_handler(error):
        response = {
            'message': str(error),
            'exception': error.__class__.__name__
        }
        return response, getattr(error, 'error_code', 500)

    return app_instance


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)