from .basic import router as basic_router
from .commands import router as commands_router
from .food_input import router as food_input_router

__all__ = [
    "basic_router",
    "commands_router",
    "food_input_router",
]
