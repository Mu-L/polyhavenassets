if "bpy" not in locals():
    from . import pull_from_polyhaven
else:
    import importlib

    importlib.reload(pull_from_polyhaven)

import bpy  # noqa: F401

classes = [
    pull_from_polyhaven.PHA_OT_pull_from_polyhaven,
]
