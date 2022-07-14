import bpy
import json
import subprocess
import requests
from shutil import copy as copy_file
from pathlib import Path
from ..utils.get_asset_lib import get_asset_lib
from concurrent.futures import ThreadPoolExecutor
from time import sleep


def get_asset_list():
    url = "https://api.polyhaven.com/assets"
    res = requests.get(url)

    if res.status_code != 200:
        return (f"Error retrieving asset list, status code: {res.status_code}", None)

    return (None, res.json())


def update_asset(slug, info, lib_dir):
    info_fp = lib_dir / slug / "info.json"
    if not info_fp.exists():
        download_asset(slug, info, lib_dir, info_fp)


def download_asset(slug, info, lib_dir, info_fp):
    url = f"https://api.polyhaven.com/files/{slug}"
    res = requests.get(url)

    if res.status_code != 200:
        return (f"Error retrieving file list for {slug}, status code: {res.status_code}", None)

    info['files'] = res.json()
    info_fp.parent.mkdir(parents=True, exist_ok=True)
    with info_fp.open('w') as f:
        f.write(json.dumps(info, indent=4))

    print("Downloading", slug)
    res = "1k"  # Download lowest resolution by default

    thumbnail_file = lib_dir / slug / "thumbnail.webp"
    download_file(f"https://cdn.polyhaven.com/asset_img/thumbs/{slug}.png?width=256&height=256", thumbnail_file)

    if info['type'] > 0:  # Textures and models
        blend = info['files']['blend'][res]['blend']
        blend_file = lib_dir / slug / f"{slug}.blend"
        executor = ThreadPoolExecutor(max_workers=10)
        threads = []
        t = executor.submit(download_file, blend['url'], blend_file)
        threads.append(t)
        for sub_path, incl in blend['include'].items():
            t = executor.submit(download_file, incl['url'], lib_dir / slug / sub_path)
            threads.append(t)
        while (any(t._state != "FINISHED" for t in threads)):
            sleep(0.1)  # Block until all downloads are complete
        mark_asset(blend_file, slug, info, thumbnail_file)
    else:  # HDRIs
        url = info['files']['hdri'][res]['hdr']['url']
        hdr_file = lib_dir / slug / Path(url).name
        download_file(url, hdr_file)
        make_hdr_blend(hdr_file, slug, info, thumbnail_file)

    return (None, None)


def download_file(url, dest):
    print("Downloading", Path(url).name)

    res = requests.get(url)
    if res.status_code != 200:
        return f"Error retrieving {url}, status code: {res.status_code}"

    dest.parent.mkdir(parents=True, exist_ok=True)

    with dest.open("wb") as f:
        f.write(res.content)

    return None


def mark_asset(blend_file, slug, info, thumbnail_file):
    script_path = Path(__file__).parents[1] / 'utils' / 'make_blend.py'
    subprocess.call([
        bpy.app.binary_path,
        '--background',
        blend_file,
        '--factory-startup',
        '--python',
        script_path,
        '--',
        slug,
        str(info['type']),
        thumbnail_file,
        ', '.join(info['authors'].keys()),
        ';'.join(info['categories']),
        ';'.join(info['tags']),
        "NONE"
    ])


def make_hdr_blend(hdr_file, slug, info, thumbnail_file):
    script_path = Path(__file__).parents[1] / 'utils' / 'make_blend.py'
    template_blend = Path(__file__).parents[1] / 'utils' / "hdri_template.blend"
    subprocess.call([
        bpy.app.binary_path,
        '--background',
        template_blend,
        '--factory-startup',
        '--python',
        script_path,
        '--',
        slug,
        "0",
        thumbnail_file,
        ', '.join(info['authors'].keys()),
        ';'.join(info['categories']),
        ';'.join(info['tags']),
        hdr_file
    ])


class PHA_OT_pull_from_polyhaven(bpy.types.Operator):
    bl_idname = "pha.pull_from_polyhaven"
    bl_label = "Pull from Poly Haven"
    bl_description = "Updates the local asset library with new assets from polyhaven.com"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        asset_lib = get_asset_lib(context)
        if asset_lib is None:
            self.report({'ERROR'}, "First open Preferences > File Paths and create an asset library named \"Poly Haven\"")
            return {'CANCELLED'}
        if not Path(asset_lib.path).exists():
            self.report({'ERROR'}, "Asset library path not found! Please check the folder still exists")
            return {'CANCELLED'}

        error, assets = get_asset_list()
        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        catalog_file = Path(asset_lib.path) / 'blender_assets.cats.txt'
        if not catalog_file.exists():
            catalog_file.parent.mkdir(parents=True, exist_ok=True)  # Juuuust in case the library folder was removed
            default_catalog_file = Path(__file__).parents[1] / "blender_assets.cats.txt"
            copy_file(default_catalog_file, catalog_file)

        executor = ThreadPoolExecutor(max_workers=20)
        threads = []
        for slug, asset in assets.items():
            t = executor.submit(update_asset, slug, asset, Path(asset_lib.path))
            threads.append(t)

        self.report({'INFO'}, "Downloading in background...")
        return {'FINISHED'}
