import bpy
import json
import logging
import requests
import subprocess
from shutil import copy as copy_file
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from ..constants import REQ_HEADERS
from ..utils.download_file import download_file
from ..utils.get_asset_lib import get_asset_lib
from ..utils.get_asset_list import get_asset_list
from ..utils import progress

log = logging.getLogger(__name__)


def update_asset(context, slug, info, lib_dir, dry_run=False):
    """
    Download asset if it doesn't exist.
    If dry_run is True, return a boolean indicating whether the asset exists.
    """
    if context.window_manager.pha_props.progress_cancel:
        return None
    info_fp = lib_dir / slug / "info.json"
    if not info_fp.exists():
        if dry_run:
            return False
        download_asset(slug, info, lib_dir, info_fp)
        return slug
    if dry_run:
        return True
    return None


def download_asset(slug, info, lib_dir, info_fp):
    url = f"https://api.polyhaven.com/files/{slug}"
    res = requests.get(url, headers=REQ_HEADERS)

    if res.status_code != 200:
        msg = f"Error retrieving file list for {slug}, status code: {res.status_code}"
        log.error(msg)
        return (msg, None)

    info["files"] = res.json()
    info_fp.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading {slug}")
    res = "1k"  # Download lowest resolution by default

    if bpy.context.window_manager.pha_props.progress_cancel:
        return (f"Cancelled {slug}", None)

    thumbnail_file = lib_dir / slug / "thumbnail.webp"
    download_file(
        f"https://cdn.polyhaven.com/asset_img/thumbs/{slug}.png?width=256&height=256",
        thumbnail_file,
    )

    if bpy.context.window_manager.pha_props.progress_cancel:
        return (f"Cancelled {slug}", None)

    if info["type"] > 0:  # Textures and models
        blend = info["files"]["blend"][res]["blend"]
        blend_file = lib_dir / slug / f"{slug}.blend"
        executor = ThreadPoolExecutor(max_workers=10)
        threads = []
        t = executor.submit(download_file, blend["url"], blend_file)
        threads.append(t)
        for sub_path, incl in blend["include"].items():
            t = executor.submit(download_file, incl["url"], lib_dir / slug / sub_path)
            threads.append(t)
        while any(t._state != "FINISHED" for t in threads):
            sleep(0.1)  # Block until all downloads are complete
        if bpy.context.window_manager.pha_props.progress_cancel:
            return (f"Cancelled {slug}", None)
        mark_asset(blend_file, slug, info, thumbnail_file)
    else:  # HDRIs
        url = info["files"]["hdri"][res]["hdr"]["url"]
        hdr_file = lib_dir / slug / Path(url).name
        download_file(url, hdr_file)
        if bpy.context.window_manager.pha_props.progress_cancel:
            return (f"Cancelled {slug}", None)
        make_hdr_blend(hdr_file, slug, info, thumbnail_file)

    if bpy.context.window_manager.pha_props.progress_cancel:
        return (f"Cancelled {slug}", None)

    with info_fp.open("w") as f:
        f.write(json.dumps(info, indent=4))

    return (None, None)


def mark_asset(blend_file, slug, info, thumbnail_file):
    script_path = Path(__file__).parents[1] / "utils" / "make_blend.py"
    subprocess.call(
        [
            bpy.app.binary_path,
            "--background",
            blend_file,
            "--factory-startup",
            "--python",
            script_path,
            "--",
            slug,
            str(info["type"]),
            thumbnail_file,
            ", ".join(info["authors"].keys()),
            ";".join(info["categories"]),
            ";".join(info["tags"]),
            ";".join(str(x) for x in info["dimensions"]) if "dimensions" in info else "NONE",
            "NONE",
        ]
    )


def make_hdr_blend(hdr_file, slug, info, thumbnail_file):
    script_path = Path(__file__).parents[1] / "utils" / "make_blend.py"
    template_blend = Path(__file__).parents[1] / "utils" / "hdri_template.blend"
    subprocess.call(
        [
            bpy.app.binary_path,
            "--background",
            template_blend,
            "--factory-startup",
            "--python",
            script_path,
            "--",
            slug,
            "0",
            thumbnail_file,
            ", ".join(info["authors"].keys()),
            ";".join(info["categories"]),
            ";".join(info["tags"]),
            "NONE",
            hdr_file,
        ]
    )


class PHA_OT_pull_from_polyhaven(bpy.types.Operator):
    bl_idname = "pha.pull_from_polyhaven"
    bl_label = "Fetch assets from polyhaven.com"
    bl_description = "Updates the local asset library with new assets from polyhaven.com"
    bl_options = {"REGISTER", "UNDO"}

    asset_type: bpy.props.StringProperty(default="all")

    prog = 0
    prog_text = None
    num_downloaded = 0
    _timer = None
    th = None

    @classmethod
    def poll(self, context):
        return context.window_manager.pha_props.progress_total == 0

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def modal(self, context, event):
        if event.type == "TIMER":
            progress.update(context, self.prog, self.prog_text)

            if not self.th.is_alive():
                log.debug("FINISHED ALL THREADS")
                progress.end(context)
                self.th.join()
                self.report(
                    {"INFO"}, f"Downloaded {self.num_downloaded} asset{'s' if self.num_downloaded != 1 else ''}"
                )
                try:
                    bpy.ops.asset.library_refresh()
                except RuntimeError:
                    # Context has changed
                    pass
                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        import threading

        def long_task(self, assets, asset_lib):
            assets_to_fetch = {}
            for slug, asset in assets.items():
                exists = update_asset(context, slug, asset, Path(asset_lib.path), dry_run=True)
                if not exists:
                    assets_to_fetch[slug] = asset
            progress.init(context, len(assets_to_fetch), word="Downloading")
            executor = ThreadPoolExecutor(max_workers=20)
            threads = []
            for slug, asset in assets_to_fetch.items():
                t = executor.submit(update_asset, context, slug, asset, Path(asset_lib.path))
                threads.append(t)

            finished_threads = []
            while True:
                for tt in threads:
                    if tt._state == "FINISHED":
                        if tt not in finished_threads:
                            finished_threads.append(tt)
                            self.prog += 1
                            if tt.result() is not None:
                                self.num_downloaded += 1
                                self.prog_text = f"Downloaded {tt.result()}"
                if all(t._state == "FINISHED" for t in threads):
                    break
                sleep(0.5)

        asset_lib = get_asset_lib(context)
        if asset_lib is None:
            self.report(
                {"ERROR"},
                'First open Preferences > File Paths and create an asset library named "Poly Haven"',
            )
            return {"CANCELLED"}
        if not Path(asset_lib.path).exists():
            self.report(
                {"ERROR"},
                "Asset library path not found! Please check the folder still exists",
            )
            return {"CANCELLED"}

        if self.asset_type not in ["hdris", "textures", "models", "all"]:
            self.report(
                {"ERROR"},
                f"Type {self.asset_type} is not a valid asset type",
            )
            return {"CANCELLED"}

        error, assets = get_asset_list(self.asset_type)
        if error:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}

        catalog_file = Path(asset_lib.path) / "blender_assets.cats.txt"
        if not catalog_file.exists():
            catalog_file.parent.mkdir(parents=True, exist_ok=True)  # Juuuust in case the library folder was removed
            default_catalog_file = Path(__file__).parents[1] / "blender_assets.cats.txt"
            copy_file(default_catalog_file, catalog_file)

        self.th = threading.Thread(target=long_task, args=(self, assets, asset_lib))

        self.th.start()

        self.report({"INFO"}, "Downloading in background...")

        context.window_manager.pha_props.new_assets = 0

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}
