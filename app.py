import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import qrcode
import cv2
import numpy as np
import io

# --- Read QR code using OpenCV ---
def read_qr_code(image):
    img_array = np.array(image.convert("RGB"))
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img_array)
    return data if data else None

# --- Generate split QRs ---
def generate_split_qrs(base_text, count):
    qr_images = []
    for i in range(1, count + 1):
        data = f"{base_text}-{i}" if count > 1 else base_text
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_images.append((data, img))
    return qr_images

# --- Create label pages (1 per page) ---
def create_label_pages(qr_images):
    DPI = 300
    LABEL_WIDTH = int(1 * DPI)      # 1 inch wide
    LABEL_HEIGHT = int(2.5 * DPI)   # 2.5 inch tall
    qr_size = 220                   # QR inside label
    border_thickness = 3            # thin border

    pages = []
    for label, qr_img in qr_images:
        # Create blank label page
        page = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
        draw = ImageDraw.Draw(page)

        # Draw border
        for i in range(border_thickness):
            draw.rectangle([i, i, LABEL_WIDTH - i - 1, LABEL_HEIGHT - i - 1], outline="black")

        # Resize QR
        qr_resized = qr_img.resize((qr_size, qr_size))

        # Paste QR centered at top
        qr_x = (LABEL_WIDTH - qr_size) // 2
        qr_y = 50
        page.paste(qr_resized, (qr_x, qr_y))

        # Add text below QR
        try:
            font = ImageFont.truetype("arial.ttf", 48)  # Larger text
        except:
            font = ImageFont.load_default()

        # Get text size safely
        if hasattr(draw, "textbbox"):  # Pillow >= 8.0
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:  # older Pillow
            text_w, text_h = draw.textsize(label, font=font)

        text_x = (LABEL_WIDTH - text_w) // 2
        text_y = qr_y + qr_size + 30
        draw.text((text_x, text_y), label, font=font, fill="black")

        pages.append(page)

    return pages

# --- Streamlit UI ---
st.title("🏷️ QR Code Label Generator")
st.write("Generate or split QR codes into **individual label pages (1 inch x 2.5 inch)** with borders.")

mode = st.radio("Select mode:", ("Upload & Split", "Generate & Split"))

if mode == "Upload & Split":
    uploaded_file = st.file_uploader("Upload your QR code (PNG/JPG)", type=["png", "jpg", "jpeg"])
    count = st.number_input("Number of splits", min_value=1, value=3)

    if uploaded_file:
        image = Image.open(uploaded_file)
        base_text = read_qr_code(image)

        if base_text:
            st.success(f"QR Code content: `{base_text}`")
            if st.button("Generate Label Pages"):
                qr_images = generate_split_qrs(base_text, count)
                pages = create_label_pages(qr_images)

                # Save multipage PDF
                pdf_buffer = io.BytesIO()
                pages[0].save(pdf_buffer, format="PDF", save_all=True, append_images=pages[1:])
                pdf_buffer.seek(0)

                st.download_button(
                    label="📄 Download Labels PDF",
                    data=pdf_buffer,
                    file_name="qr_labels.pdf",
                    mime="application/pdf"
                )

                st.image(pages[0], caption="Preview of first label", use_column_width=True)
        else:
            st.error("Could not read QR code from the image.")

elif mode == "Generate & Split":
    text_input = st.text_input("Enter text for QR code:")
    count = st.number_input("Number of splits", min_value=1, value=1)

    if st.button("Generate Label Pages"):
        if text_input.strip() == "":
            st.error("Please enter some text.")
        else:
            qr_images = generate_split_qrs(text_input.strip(), count)
            pages = create_label_pages(qr_images)

            # Save multipage PDF
            pdf_buffer = io.BytesIO()
            pages[0].save(pdf_buffer, format="PDF", save_all=True, append_images=pages[1:])
            pdf_buffer.seek(0)

            st.download_button(
                label="📄 Download Labels PDF",
                data=pdf_buffer,
                file_name="qr_labels.pdf",
                mime="application/pdf"
            )

            st.image(pages[0], caption="Preview of first label", use_column_width=True)



