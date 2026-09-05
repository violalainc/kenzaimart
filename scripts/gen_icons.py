#!/usr/bin/env python3
"""assets/Kenzaimart.png から favicon / アプリアイコン一式を生成する。

元画像が正方形でない場合は中央基準で正方形にクロップしてから
各サイズにリサイズする。apple-touch-icon のみ、透明背景を
白背景に合成する(iOSのホーム画面アイコンは透明部分が黒くなるため)。
"""

import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "Kenzaimart.png"
OUT_DIR = ROOT / "assets" / "icons"


def square_crop(img: Image.Image) -> Image.Image:
    w, h = img.size
    if w == h:
        return img
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    src = Image.open(SOURCE).convert("RGBA")
    src = square_crop(src)

    def resized(size: int) -> Image.Image:
        return src.resize((size, size), Image.LANCZOS)

    resized(16).save(OUT_DIR / "favicon-16x16.png")
    resized(32).save(OUT_DIR / "favicon-32x32.png")
    resized(192).save(OUT_DIR / "android-chrome-192x192.png")
    resized(512).save(OUT_DIR / "android-chrome-512x512.png")

    apple = resized(180)
    white_bg = Image.new("RGBA", apple.size, (255, 255, 255, 255))
    white_bg.alpha_composite(apple)
    white_bg.convert("RGB").save(OUT_DIR / "apple-touch-icon.png")

    ico_sizes = [16, 32, 48]
    resized(48).save(
        OUT_DIR / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
    )

    print(f"アイコンを {OUT_DIR.relative_to(ROOT)}/ に生成しました。")


if __name__ == "__main__":
    main()
