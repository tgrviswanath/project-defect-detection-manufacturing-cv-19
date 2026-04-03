"""
Generate sample images for cv-19 Defect Detection (Manufacturing).
Run: pip install Pillow numpy && python generate_samples.py
Output: 6 images — good part, scratch, crack, dent, hole, contamination.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

OUT = os.path.dirname(__file__)


def save(img, name):
    img.save(os.path.join(OUT, name))
    print(f"  created: {name}")


def metal_surface(W=400, H=400, base=(180, 180, 185)):
    arr = np.random.randint(-8, 8, (H, W, 3), dtype=np.int16)
    arr += np.array(base, dtype=np.int16)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def good_part():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    # clean machined part outline
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    d.ellipse([150, 150, 250, 250], outline=(120, 120, 125), width=2)
    d.text((130, 370), "Good Part", fill=(60, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.5))


def scratch():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    # scratch lines
    d.line([100, 80, 320, 200], fill=(80, 80, 85), width=2)
    d.line([102, 82, 322, 202], fill=(220, 220, 225), width=1)
    d.line([150, 250, 280, 180], fill=(80, 80, 85), width=1)
    d.text((130, 370), "Scratch", fill=(180, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.5))


def crack():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    # jagged crack
    pts = [(120, 100), (135, 130), (125, 160), (145, 200), (130, 240), (150, 280), (140, 320)]
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=(40, 40, 45), width=3)
        d.line([(pts[i][0] + 1, pts[i][1]), (pts[i + 1][0] + 1, pts[i + 1][1])], fill=(220, 220, 225), width=1)
    d.text((140, 370), "Crack", fill=(180, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.5))


def dent():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    # dent — darker ellipse with shadow
    d.ellipse([160, 140, 260, 220], fill=(140, 140, 145))
    d.ellipse([165, 145, 255, 215], fill=(120, 120, 125))
    d.arc([160, 140, 260, 220], start=200, end=360, fill=(220, 220, 225), width=2)
    d.text((145, 370), "Dent", fill=(180, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.8))


def hole():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    # unexpected hole
    d.ellipse([170, 155, 230, 215], fill=(30, 30, 30))
    d.arc([168, 153, 232, 217], start=200, end=360, fill=(220, 220, 225), width=3)
    d.text((145, 370), "Hole", fill=(180, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.5))


def contamination():
    img = metal_surface()
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 350, 350], outline=(120, 120, 125), width=3)
    # oil/dirt spots
    for sx, sy, sr, sc in [(150, 130, 20, (80, 60, 30)), (220, 200, 15, (60, 50, 20)),
                            (180, 260, 25, (70, 55, 25)), (260, 150, 12, (90, 70, 35))]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=sc)
    d.text((110, 370), "Contamination", fill=(180, 60, 60))
    return img.filter(ImageFilter.GaussianBlur(0.5))


if __name__ == "__main__":
    print("Generating cv-19 samples...")
    save(good_part(), "sample_good.jpg")
    save(scratch(), "sample_scratch.jpg")
    save(crack(), "sample_crack.jpg")
    save(dent(), "sample_dent.jpg")
    save(hole(), "sample_hole.jpg")
    save(contamination(), "sample_contamination.jpg")
    print("Done — 6 images in samples/")
