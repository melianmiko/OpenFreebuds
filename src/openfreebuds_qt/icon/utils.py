from PIL import Image, ImageDraw


def image_spawn_bg_mask(level: float, size):
    img = Image.new("RGBA", size, color="#ffffff")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, size[0],
                    round(size[1] * (1 - level))), fill="#000000")
    return img


def image_combine_mask(mask: Image.Image, foreground: Image.Image, background: Image.Image) -> Image.Image:
    mask = mask.convert("RGBA")
    mask_data = mask.getdata()
    fg_data = foreground.getdata()

    img_data = list()
    for a, mask_pixel in enumerate(mask_data):
        img_data.append((fg_data[a][0], fg_data[a][1], fg_data[a][2],
                         round((fg_data[a][3] / 255) * mask_pixel[0])))

    generated = Image.new("RGBA", mask.size)

    # noinspection PyTypeChecker
    generated.putdata(img_data)

    out = Image.new("RGBA", mask.size)
    out.alpha_composite(background)
    out.alpha_composite(generated)

    return out
