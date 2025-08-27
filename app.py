# app.py
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
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        out.append((data, img))
    return out

def _load_font(size: int) -> ImageFont.ImageFont:
    """Try a reliable TTF first; fallback to default."""
    for name in ("DejaVuSans.ttf", "arial.ttf"):
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
    return draw.textsize(text, font=font)

def create_label_pages(
    qr_images,
    label_width_in=1.0,
    label_height_in=2.5,
    dpi=300,
    border_thickness_px=2,
    qr_width_ratio=0.75,
    font_width_ratio=0.40,
    vertical_spacing_px=20,
    inner_margin_px=8
):
    LABEL_W = int(round(label_width_in * dpi))
    LABEL_H = int(round(label_height_in * dpi))
    qr_size = int(LABEL_W * qr_width_ratio)

    pages = []
    for label_text, qr_img in qr_images:
        page = Image.new("RGB", (LABEL_W, LABEL_H), "white")
        draw = ImageDraw.Draw(page)

        # Draw thin border
        for i in range(border_thickness_px):
            draw.rectangle([i, i, LABEL_W - 1 - i, LABEL_H - 1 - i], outline="black")

        # Resize QR
        qr_resized = qr_img.resize((qr_size, qr_size))

        # Font sizing and auto-shrink
        base_font_size = max(8, int(qr_size * font_width_ratio))
        font = _load_font(base_font_size)
        max_text_width = LABEL_W - 2 * inner_margin_px
        tw, th = _text_size(draw, label_text, font)
        while (tw > max_text_width) and (base_font_size > 8):
            base_font_size -= 1
            font = _load_font(base_font_size)
            tw, th = _text_size(draw, label_text, font)

        # Vertical centering of [QR + spacing + text]
        content_height = qr_size + vertical_spacing_px + th
        start_y = max(inner_margin_px, (LABEL_H - content_height) // 2)

        # Paste QR centered horizontally
        qr_x = (LABEL_W - qr_size) // 2
        qr_y = start_y
        page.paste(qr_resized, (qr_x, qr_y))

        # Draw text centered under QR
        text_x = (LABEL_W - tw) // 2
        text_y = qr_y + qr_size + vertical_spacing_px
        draw.text((text_x, text_y), label_text, font=font, fill="black")

        pages.append(page)

    return pages

def save_pages_to_pdf_bytes(pages, dpi=300) -> bytes:
    if not pages:
        return b""
    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:], resolution=float(dpi))
    buf.seek(0)
    return buf.getvalue()

# -----------------------
# Streamlit UI
# -----------------------
st.title("🏷️ QR Label PDF (1\" × 2.5\", one per page)")
st.caption("Thin border • QR vertically centered • Text scales with QR width")

# NOTE: Removed `horizontal=True` for compatibility with older Streamlit versions
mode = st.radio("Mode", ["Upload & Split", "Generate & Split"])

with st.expander("Advanced layout (optional)", expanded=False):
    qr_width_ratio = st.slider("QR width (% of label width)", 50, 90, 75, step=1) / 100.0
    font_width_ratio = st.slider("Text height (~% of QR width)", 20, 60, 40, step=1) / 100.0
    border_thickness_px = st.slider("Border thickness (px)", 1, 6, 2, step=1)
    vertical_spacing_px = st.slider("Spacing between QR and text (px)", 0, 60, 20, step=2)

count = st.number_input("Number of splits", min_value=1, value=3, step=1)

if mode == "Upload & Split":
    uploaded = st.file_uploader("Upload a QR image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded:
        pil_img = Image.open(uploaded)
        base_text = read_qr_code(pil_img)

        if base_text:
            st.success(f"Decoded content: `{base_text}`")
            if st.button("Generate PDF"):
                qr_images = generate_split_qrs(base_text, int(count))
                pages = create_label_pages(
                    qr_images,
                    qr_width_ratio=qr_width_ratio,
                    font_width_ratio=font_width_ratio,
                    border_thickness_px=border_thickness_px,
                    vertical_spacing_px=vertical_spacing_px,
                )
                pdf_bytes = save_pages_to_pdf_bytes(pages, dpi=300)

                st.download_button(
                    "📄 Download Labels PDF",
                    data=pdf_bytes,
                    file_name="qr_labels.pdf",
                    mime="application/pdf",
                )
                if pages:
                    st.image(pages[0], caption="Preview: first label", use_column_width=False)
        else:
            st.error("Could not read a QR code from the uploaded image.")

else:  # Generate & Split
    text_input = st.text_input("Enter base text / SR")
    if st.button("Generate PDF"):
        if not text_input.strip():
            st.error("Please enter some text.")
        else:
            qr_images = generate_split_qrs(text_input.strip(), int(count))
            pages = create_label_pages(
                qr_images,
                qr_width_ratio=qr_width_ratio,
                font_width_ratio=font_width_ratio,
                border_thickness_px=border_thickness_px,
                vertical_spacing_px=vertical_spacing_px,
            )
            pdf_bytes = save_pages_to_pdf_bytes(pages, dpi=300)

            st.download_button(
                "📄 Download Labels PDF",
                data=pdf_bytes,
                file_name="qr_labels.pdf",
                mime="application/pdf",
            )
            if pages:
                st.image(pages[0], caption="Preview: first label", use_column_width=False)




