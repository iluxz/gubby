from PIL import Image
import math

img = Image.open(r"C:\Users\Can\Downloads\gubby.png").convert("RGBA")
img = img.resize((64, 64), Image.Resampling.LANCZOS)

bounce_range = 15
num_frames = 20
size = 80
bg_color = (1, 1, 1)  # near-black, used as transparent key

frames = []
for i in range(num_frames):
    t = i / num_frames
    offset = int(bounce_range * math.sin(t * math.pi))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - 64) // 2
    y = (size - 64) - offset
    canvas.paste(img, (x, y), img)

    # flatten onto bg_color
    bg = Image.new("RGB", (size, size), bg_color)
    bg.paste(canvas, (0, 0), canvas.split()[3])
    frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))

frames[0].save(
    r"D:\Gubby\gubby_bounce.gif",
    save_all=True,
    append_images=frames[1:],
    duration=50,
    loop=0,
    transparency=frames[0].getpixel((0, 0)),
    disposal=2,
)
print("done")
