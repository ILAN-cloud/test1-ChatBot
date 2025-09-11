"""
templates.py — rendu de templates Jinja2
Mono-tenant (aucun lien avec Stripe ou multi-tenant)
"""

from jinja2 import Environment, BaseLoader

_env = Environment(
    loader=BaseLoader(),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True
)

def render_template(tpl: str, **kwargs) -> str:
    """
    Rendu d'un template Jinja2 en chaîne.
    Args:
        tpl (str): texte du template Jinja2
        **kwargs: variables à injecter
    """
    return _env.from_string(tpl).render(**kwargs)
