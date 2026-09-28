from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def build_comic_layout(panel_paths, output_path=None, title=None):
    """
    Build a single comic page from panel images.
    """

    if not panel_paths:
        raise ValueError("No panel images were provided.")

    images = []

    for panel_path in panel_paths:
        path = Path(panel_path)

        if not path.exists():
            continue

        try:
            image = Image.open(path).convert("RGB")
            images.append(image)
        except Exception:
            continue

    if not images:
        raise ValueError("No valid panel images were found.")

    width = max(image.width for image in images)

    resized_images = []

    for image in images:
        if image.width != width:
            new_height = int(image.height * width / image.width)
            image = image.resize((width, new_height))

        resized_images.append(image)

    spacing = 20

    total_height = sum(image.height for image in resized_images)
    total_height += spacing * (len(resized_images) - 1)

    title_height = 0

    if title:
        title_height = 80
        total_height += title_height

    canvas = Image.new(
        "RGB",
        (width, total_height),
        "white",
    )

    y = 0

    if title:
        draw = ImageDraw.Draw(canvas)

        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        draw.text(
            (20, 20),
            str(title),
            fill="black",
            font=font,
        )

        y = title_height

    for image in resized_images:
        canvas.paste(image, (0, y))
        y += image.height + spacing

    if output_path:
        output_path = Path(output_path)

        if output_path.suffix.lower() not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ]:
            output_path = output_path.with_suffix(".png")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        canvas.save(output_path)

        return output_path

    return canvas