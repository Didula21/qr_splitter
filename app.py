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

# --- Arrange as vertical labels ---
def arrange_labels(qr_images):
    DPI = 300
    LABEL_WIDTH = 300   # 1 inch
    LABEL_HEIGHT = 750  # 2.5 inches

    # Final sheet height depends on number of labels
    sheet_height = LABEL_HEIGHT * len(qr_images)
    sheet = Image.new("RGB", (LABEL_WIDTH, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, (label, img) in enumerate(qr_images):
        # Position of the label block
        y_start = idx * LABEL_HEIGHT

        # Resize QR to fit width (leave margin)
        qr_size = LABEL_WIDTH - 40
        img_resized = img.resize((qr_size, qr_size))

        # Center QR
        x_qr = (LABEL_WIDTH - qr_size) // 2
        y_qr = y_start + 50
        sheet.paste(img_resized, (x_qr, y_qr))

        # Draw text (centered under QR)
        text = label
        text_x = LABEL_WIDTH // 2 - (len(text) * 6)  # rough centering
        text_y = y_start + qr_size + 100
        draw.text((text_x, text_y), text, fill="black")

    return sheet

# --- Streamlit UI ---
st.title("Sample Room - QR Splitter ")
st.write("Generate vertical labels (1″ × 2.5″ each) with QR code + text. PDF height adjusts with number of labels.")

mode = st.radio("Select mode:", ("Upload & Split", "Generate & Split"))

if mode == "Upload & Split":
    uploaded_file = st.file_uploader("Upload your QR code (PNG/JPG)", type=["png", "jpg", "jpeg"])
    count = st.number_input("Number of splits", min_value=1, value=2)

    if uploaded_file:
        image = Image.open(uploaded_file)
        base_text = read_qr_code(image)

        if base_text:
            st.success(f"QR Code content: `{base_text}`")
            if st.button("Generate Label QRs"):
                qr_images = generate_split_qrs(base_text, count)
                sheet = arrange_labels(qr_images)

                pdf_buffer = io.BytesIO()
                sheet.save(pdf_buffer, format="PDF", dpi=(300,300))
                pdf_buffer.seek(0)

                st.download_button(
                    label="📄 Download Label PDF",
                    data=pdf_buffer,
                    file_name="labels.pdf",
                    mime="application/pdf"
                )

                st.image(sheet, caption="Preview of Labels", use_column_width=True)
        else:
            st.error("Could not read QR code from the image.")

elif mode == "Generate & Split":
    text_input = st.text_input("Enter text for QR code:")
    count = st.number_input("Number of splits", min_value=1, value=2)

    if st.button("Generate Label QR(s)"):
        if text_input.strip() == "":
            st.error("Please enter some text.")
        else:
            qr_images = generate_split_qrs(text_input.strip(), count)
            sheet = arrange_labels(qr_images)

            pdf_buffer = io.BytesIO()
            sheet.save(pdf_buffer, format="PDF", dpi=(300,300))
            pdf_buffer.seek(0)

            st.download_button(
                label="📄 Download Label PDF",
                data=pdf_buffer,
                file_name="labels.pdf",
                mime="application/pdf"
            )

            st.image(sheet, caption="Preview of Labels", use_column_width=True)

