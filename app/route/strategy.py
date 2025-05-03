from flask import Blueprint
from app.strategy.core.controller import create_rule_factory

bp = Blueprint("strategy", __name__, url_prefix="/strategy")

rule_factory = create_rule_factory()

@bp.route("/rules")
def list_rules():
    return {"rules": rule_factory.get_available_rule_types()}
