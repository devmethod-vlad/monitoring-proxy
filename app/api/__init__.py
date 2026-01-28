from litestar import Router

from app.api.v1.controllers.alert_controller import AlertController

v1_router = Router("/v1", route_handlers=[AlertController])
