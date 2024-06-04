from PIL import Image

# https://pillow.readthedocs.io/en/stable/reference/Image.html#dither-modes
DITHER_METHODS = {
    "None": Image.Dither.NONE,
    "Floyd-Steinberg": Image.Dither.FLOYDSTEINBERG
}

#https://pillow.readthedocs.io/en/stable/reference/Image.html#quantization-methods
QUANTIZATION_METHODS = {
    "Median cut": Image.Quantize.MEDIANCUT,
    "Maximum coverage": Image.Quantize.MAXCOVERAGE,
    "Fast octree": Image.Quantize.FASTOCTREE,
    "libimagequant": Image.Quantize.LIBIMAGEQUANT
}


def downscale_image(image: Image, scale: int, preserve_alpha: bool = False, alpha_clip_threshold: float = 0.3) -> Image:
    width, height = image.size
    new_width, new_height = int(width / scale), int(height / scale)

    if not preserve_alpha:
        return image.resize((new_width, new_height), Image.NEAREST)
    else:
        return downscale_image_with_alpha(image, scale, alpha_clip_threshold)

def downscale_image_with_alpha(image: Image, scale: int, alpha_clip_threshold: float = 0.3) -> Image:
    width, height = image.size
    new_width, new_height = int(width / scale), int(height / scale)
    downscaled_image = Image.new("RGBA", (new_width, new_height))

    for i in range(new_width):
        for j in range(new_height):
            sub_image = image.crop(
                (i * scale, j * scale, (i + 1) * scale, (j + 1) * scale)
            )
            A = [pixel[3] for pixel in sub_image.getdata()]
            avg_alpha = sum(A) // len(A)
            R, G, B = sub_image.resize((1, 1), Image.NEAREST).getpixel((0, 0))[:3]
            if avg_alpha / 255 < alpha_clip_threshold:
                avg_alpha = 0
            downscaled_image.putpixel((i, j), (R, G, B, avg_alpha))

    return downscaled_image

def resize_image(image: Image, size) -> Image:
    width, height = size
    resized_image = image.resize((width, height), Image.NEAREST)
    return resized_image


def limit_colors(
        image,
        limit: int=16,
        palette=None,
        palette_colors: int=256,
        quantize: Image.Quantize=Image.Quantize.MEDIANCUT,
        dither: Image.Dither=Image.Dither.NONE,
        use_k_means: bool=False
    ):
    if use_k_means:
        k_means_value = limit
    else:
        k_means_value = 0

    if palette:
        palette_image = palette
        ppalette = palette.getcolors()
        if ppalette:
            color_palette = palette.quantize(colors=len(list(set(ppalette))))
        else:
            colors = len(palette_image.getcolors()) if palette_image.getcolors() else palette_colors
            color_palette = palette_image.quantize(colors, kmeans=colors)
    else:
        # we need to get palette from image, because
        # dither in quantize doesn't work without it
        # https://pillow.readthedocs.io/en/stable/_modules/PIL/Image.html#Image.quantize
        color_palette = image.quantize(colors=limit, kmeans=k_means_value, method=quantize, dither=Image.Dither.NONE)

    new_image = image.quantize(palette=color_palette, dither=dither)

    return new_image


def convert_to_grayscale(image):
    new_image = image.convert("L")
    return new_image.convert("RGB")


def convert_to_black_and_white(image: Image, threshold: int=128, is_inversed: bool=False):
    if is_inversed:
        apply_threshold = lambda x : 255 if x < threshold else 0
    else:
        apply_threshold = lambda x : 255 if x > threshold else 0

    black_and_white_image = image.convert('L', dither=Image.Dither.NONE).point(apply_threshold, mode='1')
    return black_and_white_image.convert("RGB")
