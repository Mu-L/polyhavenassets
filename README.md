# Poly Haven Assets Add-on

A Blender add-on to integrate our assets natively in the asset browser.

![Screenshot](/screenshot.jpg)

## Features

1. Downloads all assets from [Poly Haven](https://polyhaven.com/) (at 1k resolution by default), and list them under their respective categories in the Asset Browser.
2. Lets you swap the resolution of an asset to higher/lower resolutions any time after import (most are at least 8K).
3. Set the texture mapping scale to the correct real-world size according to the surfaces you've applied it to.
4. One-click setup of texture displacement with adaptive subdivision.
5. Simple HDRI rotation, brightness, and color temperature sliders.

## Installation

This add-on is meant to be purchased on the [Blender Market](https://blendermarket.com/products/poly-haven-asset-browser) or through [Patreon](https://www.patreon.com/posts/70974704) to support our work making new assets. However if you would like to try-before-you-buy, you can also [download it here for free](https://github.com/Poly-Haven/polyhavenassets/releases/latest/download/polyhavenassets_github.zip).

If you like it, please consider [purchasing it](https://blendermarket.com/products/poly-haven-asset-browser) to support our work on future assets :) Everyone tells me $30 is a steal for over 1000 high quality assets. You'll also get **early access to upcoming content** months before everyone else.

1. Download the ZIP file...
    * From your [Blender Market account page](https://blendermarket.com/account/orders) if you purchased it there ($30).
    * From [this post on Patreon](https://www.patreon.com/posts/blender-asset-70974704) if you support us there ($5/m).
    * From [the latest release](https://github.com/Poly-Haven/polyhavenassets/releases/latest/download/polyhavenassets_github.zip) on GitHub (free).
2. Install the zip file from Blender's User Preferences.
3. Enable the add-on.

For more detailed instructions, please check our [video guide and documentation](https://docs.polyhaven.com/en/guides/blender-addon).

### Updating:

To check for a new version of the add-on, simply visit the Preferences and click the *Check now for update* button.

## Usage

> [A more detailed user guide and video demo is available here](https://docs.polyhaven.com/en/guides/blender-addon).

1. After enabling the add-on, [add a new Asset Library](https://file.coffee/u/sPrJY2-9578l2WjmmOA3n.png) in your preferences called `Poly Haven`. This is where assets will be downloaded to.
2. Open the asset browser editor and select the Poly Haven library at the top left.
3. Click the ***Fetch Assets*** button in the header of the asset browser.
4. After the initial download (which currently is around 3.3GB), simply drag and drop the assets into your scene.
5. We release new assets almost daily, so you can click that *Fetch Assets* button any time to download new assets.

## Known Issues

1. After installing and downloading assets for the first time, the list of catalogs may not be updated automatically. Simply restart Blender and you should see them.
2. It would be nice if users didn't have to download all ~1000 of our assets beforehand, but rather have them download dynamically when they're dragged into the scene. Right now it doesn't seem like this is possible in the Blender API, but it should be possible sometime in the future.
