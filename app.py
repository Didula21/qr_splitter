import io
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import qrcode
import cv2
import numpy as np

# -----------------------
# Helpers
# -----------------------
def read_qr_code(image: Image.Image):
    """Decode a QR code from a PIL image using OpenCV."""
    img_array = np.array(image.convert("RGB"))
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img_array)
    return data if data else None

def generate_split_qrs(base_text: str, count: int):
    """Generate a list of (label_text, PIL_QR_Image) tuples."""
    out = []
    for i in range(1, count + 1):
        data = f"{base_text}-{i}" if count > 1 else base_text
        qr = qrcode.QRCode(
            version=None,  # let lib pick
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        out.append((data, img))
    return out

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try a reliable TTF first; fallback to default."""
    # DejaVuSans ships with Pillow and is available on Streamlit Cloud
    for name in ["DejaVuSans.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    """Measure text width/height robustly across Pillow versions."""
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    # Fallback
    return draw.textsize(text, font=font)

def create_label_pages(
    qr_images,
    label_width_in=1.0,
    label_height_in=2.5,
    dpi=300,
    border_thickness_px=2,
    qr_width_ratio=0.75,    # QR width as % of label width
    font_width_ratio=0.40,  # starting font height ~ % of QR width
    vertical_spacing_px=20, # space between QR and text
    inner_margin_px=8       # margin from border to content
):
    """
    Build one PIL Image per label (each = one page).
    QR is centered vertically; text below QR.
    Font size scales with QR width and auto-shrinks to fit label width.
    """
    LABEL_W = int(round(label_width_in * dpi))   # 1" => 300 px
    LABEL_H = int(round(label_height_in * dpi))  # 2.5" => 750 px
    qr_size = int(LABEL_W * qr_width_ratio)

    pages = []
    for label_text, qr_img in qr_images:
        page = Image.new("RGB", (LABEL_W, LABEL_H), "white")
        draw = ImageDraw.Draw(page)

        # Border
        for i in range(border_thickness_px):
            draw.rectangle([i, i, LABEL_W - 1 - i, LABEL_H - 1 - i], outline="black")

        # Resize QR & paste
        qr_resized = qr_img.resize((qr_size, qr_size))
        # We'll center the block [QR + spacing + text] vertically:
        # Determine font size starting guess (scaled to QR width)
        base_font_size = max(8, int(qr_size * font_width_ratio))
        font = _load_font(base_font_size)

        # Auto-shrink font to ensure text fits within label width minus margins
        max_text_width = LABEL_W - 2 * inner_margin_px
        tw, th = _text_size(draw, label_text, font)
        while (tw > max_text_width) and (base_font_size > 8):
            base_font_size -= 1
            font = _load_font(base_font_size)
            tw, th = _text_size(draw, label_text, font)

        content_height = qr_size + vertical_spacing_px + th
        start_y = max(inner_margin_px, (LABEL_H - content_height) // 2)

        # Center QR horizontally
        qr_x = (LABEL_W - qr_size) // 2
        qr_y = start_y
        page.paste(qr_resized, (qr_x, qr_y))

        # Draw text centered below QR
        text_x = (LABEL_W - tw) // 2
        text_y = qr_y + qr_size + vertical_spacing_px
        draw.text((text_x, text_y), label_text, font=font, fill="black")

        pages.append(page)

    return pages

def save_pages_to_pdf_bytes(pages, dpi=300) -> bytes:
    """Save a list of PIL Images as a multipage PDF into bytes."""
    if not pages:
        return b""
    buf = io.BytesIO()
    # resolution sets intended physical size mapping (points) in PDF
    pages[0].save(
        buf, format="PDF", save_all=True, append_images=pages[1:], resolution=float(dpi)
    )
    buf.seek(0)
    return buf.getvalue()

# -----------------------
# Streamlit UI
# -----------------------
st.title("🏷️ QR Label PDF (1\" × 2.5\", one per page)")
st.caption("Thin border • QR vertically centered • Text scales with QR width")

mode = st.radio("Mode", ["Upload & Split", "Generate & Split"], horizontal=True)

with st.expander("Advanced layout (optional)"




