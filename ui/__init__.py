import imp

from . import PT_main
from . import prefs_lib_reminder
from . import asset_lib_support
from . import asset_lib_titlebar
from . import statusbar
from . import PT_asset_hdri
from . import PT_asset_model
from . import PT_asset_texture

imp.reload(PT_main)
imp.reload(prefs_lib_reminder)
imp.reload(asset_lib_support)
imp.reload(asset_lib_titlebar)
imp.reload(statusbar)
imp.reload(PT_asset_hdri)
imp.reload(PT_asset_model)
imp.reload(PT_asset_texture)

classes = [
    PT_main.PHA_PT_main,
    PT_asset_hdri.PHA_PT_asset_hdri,
    PT_asset_model.PHA_PT_asset_model,
    PT_asset_texture.PHA_PT_asset_texture_eevee,
    PT_asset_texture.PHA_PT_asset_texture_cycles,
]
