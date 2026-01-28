from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.domain.value_objects.notification import Notification
from app.infrastructure.template_render.interfaces import ITemplateRenderer
from app.settings.settings import Settings


class JinjaTemplateRenderer(ITemplateRenderer):
    """Рендерер через jinja"""

    def __init__(self, settings: Settings) -> None:
        self.env = Environment(
            loader=FileSystemLoader(settings.templates.dir),
            autoescape=select_autoescape(enabled_extensions=()),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, payload: dict) -> Notification:
        """Рендеринг и создание уведомления"""
        template = self.env.get_template(template_name)
        title = payload.get("title")
        status = payload.get("status")
        alertname = payload.get("alertname")
        common_labels = payload.get("common_labels")
        common_annotations = payload.get("common_annotations")
        selector = payload.get("selector")
        error_filter = payload.get("error_filter")
        search_window = payload.get("search_window")
        context_before = payload.get("context_before")
        context_after = payload.get("context_after")
        max_matches = payload.get("max_matches")
        contexts = payload.get("contexts")

        body = template.render(
            title=title,
            status=status,
            alertname=alertname,
            labels=common_labels,
            annotations=common_annotations,
            selector=selector,
            error_filter=error_filter,
            search_window=search_window,
            context_before=context_before,
            context_after=context_after,
            max_matches=max_matches,
            contexts=contexts,
        ).strip()
        return Notification(title=title, body=body)
