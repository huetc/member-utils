from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_jinja_env(template_dir: str) -> Environment:
    return Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape())


def render_message_template(jinja_env: Environment, template_file: str, render_variables: dict[str, Any]) -> str:
    template = jinja_env.get_template(template_file)
    return template.render(**render_variables)
