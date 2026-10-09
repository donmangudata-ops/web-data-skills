---
name: background-remover-local
description: Removes the background of an image and saves a transparent PNG on your own machine with the open-source rembg library and the u2net model, with no login, no API key and no account. Use when the user asks to remove or cut out the background of a photo, make a transparent PNG, or isolate the main subject of an image, for one image or a few. Not for hundreds of images, not for hair-level matting, not for editing the content of a photo.
author: Don Mangu
author_url: https://github.com/donmangudata-ops
metadata:
  category: image-processing
  keywords: "background remover, remove background, transparent png, rembg, u2net, image cutout"
---

# Background remover

Removes the background of an image with the open-source rembg library. It needs no credentials. The rembg licence reads: "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software". The u2net model comes from the U-2-Net project, which is under the Apache License 2.0.

Author: Don Mangu ([GitHub](https://github.com/donmangudata-ops)). This skill needs no token and runs on your own computer. For many images in one step, with a link to each PNG and the size and timing of each result in a table, the author also runs a paid hosted version on the Apify Store: [Background Remover API](https://apify.com/conserving_celerytop/background-remover-api) (disclosure: the author owns it). You never need it for the steps below. This is an independent tool and is not affiliated with the rembg or U-2-Net authors.

## Example prompts

- "Remove the background of product.jpg and save a transparent PNG."
- "Cut out the subject of this photo link."
- "Make cutouts of all JPG files in this folder."

Out of scope: "Remove the background from a photo of a person without their consent." Photos of people are personal data. Ask the user whether they have the right to edit the image.

## Step 1: install

Python 3.11 or newer is needed. Install two packages. The first run downloads the u2net model file once, 176 MB, to `~/.rembg`.

```bash
pip install "rembg==2.0.85" "onnxruntime==1.31.0"
```

## Step 2: choose the model on purpose

Always create the session with `new_session("u2net")` and pass it to `remove`. The default model of rembg 2.0.85 is `bria-rmbg`. Its weights need a paid agreement for commercial use. The rembg README says so: "RMBG-2.0 is released under a BRIA license ... that requires a paid agreement for commercial use." Do not use the default model, and do not use another model before you have read its licence.

## Step 3: run the script

Save this file as `cutout.py`. It takes a link or a file path and the name of the PNG to write.

```python
import io
import sys
import time
import urllib.request

from PIL import Image
from rembg import new_session, remove

# Never call remove() without a session: the default model of rembg 2.0.85 (bria-rmbg) needs a paid licence.
session = new_session("u2net")  # MIT code, Apache 2.0 weights, 176 MB, downloaded once to ~/.rembg

def cutout(source, target):
    if source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": "cutout-script/1.0 (personal use)"})
        data = urllib.request.urlopen(req, timeout=30).read()
    else:
        data = open(source, "rb").read()
    img = Image.open(io.BytesIO(data))
    print("input ", img.format, img.size, len(data), "bytes")
    if img.width * img.height > 16_000_000:
        sys.exit("Image has more than 16 megapixels. Resize it first.")
    img = img.convert("RGB")
    start = time.perf_counter()
    out = remove(img, session=session, post_process_mask=True)  # RGBA image
    out.save(target, "PNG")  # PNG keeps the alpha channel and holds no EXIF data
    alpha = out.getchannel("A")
    removed = sum(alpha.histogram()[:128]) / (out.width * out.height)
    print("output", target, out.size, f"{removed:.1%} of pixels removed, {time.perf_counter() - start:.2f} s")

cutout(sys.argv[1], sys.argv[2])
```

Real run on 9 October 2026, CPU only, on a CC0 photo from the scikit-image test data:

```text
$ python cutout.py https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.0/skimage/data/chelsea.png chelsea-cutout.png
input  PNG (451, 300) 240512 bytes
output chelsea-cutout.png (451, 300) 39.4% of pixels removed, 0.88 s
```

## Step 4: answer from the result

- Open the PNG on a coloured background to check the edges. u2net gives firm edges and can cut off thin parts such as whiskers or an antenna.
- The share of removed pixels is a quick check. A value near 0 or near 100 means the model found no clear subject. Look at the image.
- The PNG holds no EXIF data, so a GPS position of the photo is not copied. Say so when the user shares the file.
- If the result is poor, say so. Do not claim a clean cutout you did not look at.

## Rules

- Public or own files only. Do not fetch images behind a log-in and do not try to get around blocks.
- Download each link once, with a clear User-Agent, and keep the file under 15 MB and 16 megapixels.
- Check that the user has the right to edit the image. The tool does not check copyright.
- Say what you could not check: the quality on the user's own image type.

## Limits

The u2net model is a general-purpose model. It does not match newer and larger models on hair, glass and fine detail. On a CPU it needs about 1 second for an image of 0.2 megapixels on a laptop-class machine, measured for the run above. For hundreds of images, a script loop or the hosted version is quicker than asking one question at a time.
