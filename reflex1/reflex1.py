"""Welcome to Reflex! This file outlines the steps to create a basic app."""
from rxconfig import config

import reflex as rx
from gpt import VisionOSChatbot # Import VisionOSChatbot from gpt.py

# Create an instance of VisionOSChatbot
bot = VisionOSChatbot()

docs_url = "https://pynecone.io/docs/getting-started/introduction"
filename = f"{config.app_name}/{config.app_name}.py"

class State(rx.State):
    """The app state."""
    pass

def index() -> rx.Component:
    query = 'How to add a button to open full immersive space using swiftUI with visionOS?'
    res = bot.ask(query, print_message=False)
    
    return rx.fragment(
        rx.color_mode_button(rx.color_mode_icon(), float="right"),
        rx.vstack(
            rx.box("visionOS Docs GPT", font_size="1em"),
            rx.text(f"Q: {query}", font_size="1em"),
            rx.text(f"A: {res}", font_size="1em"),
            rx.link(
                "Send",
                href=docs_url,
                border="0.1em solid",
                padding="0.5em",
                border_radius="0.5em",
                _hover={
                    "color": rx.color_mode_cond(
                        light="rgb(107,99,246)",
                        dark="rgb(179, 175, 255)",
                    )
                },
            ),
            spacing="1.5em",
            font_size="2em",
            padding_top="10%",
        ),
    )

# Add state and page to the app.
app = rx.App(state=State)
app.add_page(index)
app.compile()