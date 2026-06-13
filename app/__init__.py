from pathlib import Path

from flask import Flask

from config import Config

from .extensions import db
from .db_bootstrap import ensure_mysql_database


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    upload_dir: Path = app.config["UPLOAD_FOLDER"]
    upload_dir.mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from .public_routes import public_bp
    from .auth_routes import auth_bp
    from .user_routes import user_bp
    from .admin_auth import admin_auth_bp
    from .admin_routes import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(admin_auth_bp, url_prefix="/admin")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        ensure_mysql_database(app.config.get("SQLALCHEMY_DATABASE_URI"))
        db.create_all()

    @app.template_global()
    def paginate_url(page):
        from flask import request, url_for

        flat = request.args.to_dict(flat=True)
        flat["page"] = page
        view_args = request.view_args or {}
        return url_for(request.endpoint, **view_args, **flat)

    @app.context_processor
    def inject_globals():
        from .models import Category, HomepageSetting, Brand

        try:
            cats = Category.query.filter_by(is_active=True).order_by(Category.name).limit(20).all()
        except Exception:
            cats = []
        try:
            brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).limit(20).all()
        except Exception:
            brands = []

        def setting(key: str, default: str = "") -> str:
            try:
                row = HomepageSetting.query.filter_by(key=key).first()
                return row.value if row and row.value is not None else default
            except Exception:
                return default

        return dict(header_categories=cats, header_brands=brands, site_setting=setting)

    return app
