import streamlit as st
from PIL import Image, ImageDraw
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

# --- Arrange on A4 with custom QR slots ---
def arrange_on_a4(qr_images):
    A4_WIDTH, A4_HEIGHT = 2480, 3508  # A4 at 300 DPI
    qr_height = 300   # 1 inch
    slot_width = 750  # 2.5 inches
    margin = 100
    spacing = 50

    sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    draw = ImageDraw.Draw(sheet)

    x = margin
    y = margin

    for idx, (label, img) in enumerate(qr_images):
        # Keep QR square inside slot (300x300 px)
        qr_square_size = qr_height
        img_resized = img.resize((qr_square_size, qr_square_size))

        # Paste QR on the left side of slot
        sheet.paste(img_resized, (x, y))

        # Draw label on right side of slot (centered vertically)
        text_x = x + qr_square_size + 20
        text_y = y + (qr_square_size // 2) - 10
        draw.text((text_x, text_y), label, fill="black")

        # Move down vertically
        y += qr_height + spacing

        # If bottom exceeded, go to next column
        if y + qr_height > A4_HEIGHT - margin:
            y = margin
            x += slot_width + spacing

    return sheet

# --- Streamlit UI ---
st.title("📦 Sample Room - QR Splitter")
st.write("Generate a new QR code or upload an existing QR code to split it into multiple QR codes, with fixed slot size (2.5 × 1 inch).")

mode = st.radio("Select mode:", ("Upload & Split", "Generate & Split"))

if mode == "Upload & Split":
    uploaded_file = st.file_uploader("Upload your QR code (PNG/JPG)", type=["png", "jpg", "jpeg"])
    count = st.number_input("Number of splits", min_value=1, value=3)

    if uploaded_file:
        image = Image.open(uploaded_file)
        base_text = read_qr_code(image)

        if base_text:
            st.success(f"QR Code content: `{base_text}`")
            if st.button("Generate Split QRs"):
                qr_images = generate_split_qrs(base_text, count)
                sheet = arrange_on_a4(qr_images)

                pdf_buffer = io.BytesIO()
                sheet.save(pdf_buffer, format="PDF")
                pdf_buffer.seek(0)

                st.download_button(
                    label="📄 Download A4 PDF",
                    data=pdf_buffer,
                    file_name="split_qrs.pdf",
                    mime="application/pdf"
                )

                st.image(sheet, caption="Preview of A4 sheet", use_column_width=True)
        else:
            st.error("Could not read QR code from the image.")

elif mode == "Generate & Split":
    text_input = st.text_input("Enter text for QR code:")
    count = st.number_input("Number of splits", min_value=1, value=1)

    if st.button("Generate QR(s)"):
        if text_input.strip() == "":
            st.error("Please enter some text.")
        else:
            qr_images = generate_split_qrs(text_input.strip(), count)
            sheet = arrange_on_a4(qr_images)

            pdf_buffer = io.BytesIO()
            sheet.save(pdf_buffer, format="PDF")
            pdf_buffer.seek(0)

            st.download_button(
                label="📄 Download A4 PDF",
                data=pdf_buffer,
                file_name="generated_qrs.pdf",
                mime="application/pdf"
            )

            st.image(sheet, caption="Preview of A4 sheet", use_column_width=True)

