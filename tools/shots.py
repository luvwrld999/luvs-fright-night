#!/usr/bin/env python3
"""Turn the runner's PPM dumps into a PNG contact sheet for review."""

import os
import sys

from PIL import Image, ImageDraw

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emu', 'shots')


def sheet(out_path, scale=2, columns=2, title='Captured frames'):
    names = sorted(f for f in os.listdir(SHOTS) if f.endswith('.ppm'))
    if not names:
        print('no shots')
        return None
    imgs = [(n[:-4], Image.open(os.path.join(SHOTS, n)).convert('RGB'))
            for n in names]
    w, h = imgs[0][1].size
    cw, ch = w * scale + 12, h * scale + 26
    rows = (len(imgs) + columns - 1) // columns
    sheet_img = Image.new('RGB', (columns * cw + 12, rows * ch + 34), (12, 8, 18))
    d = ImageDraw.Draw(sheet_img)
    d.text((12, 10), title, fill=(255, 216, 56))
    for i, (name, im) in enumerate(imgs):
        x = 12 + (i % columns) * cw
        y = 30 + (i // columns) * ch
        sheet_img.paste(im.resize((w * scale, h * scale), Image.NEAREST), (x, y))
        d.text((x, y + h * scale + 5), name, fill=(190, 170, 215))
    sheet_img.save(out_path)
    print('%s  (%d frames)' % (out_path, len(imgs)))
    return out_path


if __name__ == '__main__':
    sheet(sys.argv[1] if len(sys.argv) > 1 else '/tmp/shots.png',
          int(sys.argv[2]) if len(sys.argv) > 2 else 2,
          int(sys.argv[3]) if len(sys.argv) > 3 else 2,
          sys.argv[4] if len(sys.argv) > 4 else 'Captured frames')
