# Standard library imports
import pkgutil
from importlib import import_module

def register_all_blueprints(app):
    """Register all blueprints in the route directory"""
    package = __package__
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        module = import_module(f"{package}.{module_name}")
        bp = getattr(module, "bp", None)
        if bp is not None:
            app.register_blueprint(bp)
