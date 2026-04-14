__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from app.main import app as fastapi_app

        return fastapi_app
    raise AttributeError(name)
