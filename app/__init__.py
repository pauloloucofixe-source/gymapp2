import os
from flask import Flask
from config import Config
from app.db import close_db, init_db

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Garantir que a pasta instance existe
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    app.teardown_appcontext(close_db)

    # Inicializar DB se ainda não existir
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            init_db()

    # Registar Blueprints
    from app.routes.workouts import bp as workouts_bp
    from app.routes.body import bp as body_bp
    from app.routes.analytics import bp as analytics_bp

    app.register_blueprint(workouts_bp)
    app.register_blueprint(body_bp)
    app.register_blueprint(analytics_bp)

    return app