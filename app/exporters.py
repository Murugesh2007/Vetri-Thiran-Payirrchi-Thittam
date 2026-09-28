
"""
Creates a downloadable PDF from ComicCraft panel images and text.
"""

import os
from datetime import datetime

from fpdf import FPDF

from app.config import EXPORT_FOLDER, FONT_PATH


class ComicPDF(FPDF):
    """PDF helper for ComicCraft."""

    def __init__(self):
        super().__init__()

        self.unicode_font_loaded = False

        if FONT_PATH.exists():
            try:
                self.add_font(
                    "DejaVu",
                    "",
                    str(FONT_PATH),
                    uni=True,
                )
                self.unicode_font_loaded = True

            except Exception as e:
                print(
                    f"Could not load custom font: {e}"
                )

    def base_font(self):
        if self.unicode_font_loaded:
            return "DejaVu"

        return "Helvetica"


def save_pdf(layout):
    """
    Create a PDF from a list of comic panel dictionaries.

    Each panel should contain:
        panel
        title
        image_path
        text
    """

    if not isinstance(layout, list):
        raise ValueError(
            "PDF layout must be a list of panels."
        )

    pdf = ComicPDF()

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    font_name = pdf.base_font()

    for index, panel in enumerate(layout, start=1):

        if not isinstance(panel, dict):
            continue

        image_path = panel.get(
            "image_path",
            "",
        )

        title = panel.get(
            "title",
            f"Panel {index}",
        )

        story_text = panel.get(
            "text",
            "",
        )

        pdf.add_page()

        # -----------------------------
        # Panel title
        # -----------------------------

        pdf.set_font(
            font_name,
            "",
            16,
        )

        pdf.cell(
            0,
            12,
            f"Panel {index}: {title}",
            ln=True,
            align="C",
        )

        # -----------------------------
        # Panel image
        # -----------------------------

        y_image = 30

        if (
            image_path
            and os.path.isfile(str(image_path))
        ):

            pdf.image(
                str(image_path),
                x=10,
                y=y_image,
                w=pdf.w - 20,
            )

        else:

            pdf.set_y(y_image)

            pdf.set_font(
                font_name,
                "",
                12,
            )

            pdf.multi_cell(
                0,
                10,
                "Image not found.",
            )

        # -----------------------------
        # Story text
        # -----------------------------

        pdf.set_y(210)

        pdf.set_font(
            font_name,
            "",
            12,
        )

        if story_text is None:
            story_text = ""

        story_text = str(
            story_text
        ).strip()

        # Avoid characters that Helvetica
        # cannot handle.
        if not pdf.unicode_font_loaded:

            story_text = (
                story_text
                .encode(
                    "latin-1",
                    "replace",
                )
                .decode("latin-1")
            )

        if story_text:

            pdf.multi_cell(
                0,
                8,
                story_text,
            )

    # -----------------------------
    # Save PDF
    # -----------------------------

    os.makedirs(
        str(EXPORT_FOLDER),
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"comic_{timestamp}.pdf"
    )

    pdf_path = os.path.join(
        str(EXPORT_FOLDER),
        filename,
    )

    pdf.output(pdf_path)

    return pdf_path

