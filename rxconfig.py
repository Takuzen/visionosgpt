import reflex as rx

class ReflexConfig(rx.Config):
    pass

config = ReflexConfig(
    app_name="reflex1",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)