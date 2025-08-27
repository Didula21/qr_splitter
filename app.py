import qrcode
from PIL import Image, ImageDraw, ImageFont

# -----------------------
# 1. Generate QR codes
# -----------------------
def generate_qr_codes(serial_numbers):
    qr_images = []
    for sn in serial_numbers:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(sn)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_images.append((sn, img))
    return qr_images


# -----------------------
# 2. Create label pages
# -----------------------
def create_label_pages(qr_images):
    DPI = 300
    LABEL_WIDTH = int(1 * DPI)      # 1 inch wide
    LABEL_HEIGHT = int(2.5 * DPI)   # 2.5 inch tall
    qr_size = int(LABEL_WIDTH * 0.7)  # QR fills ~70% of width
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

        # Dynamically set font size based on QR width
        font_size = int(qr_size * 0.35)  # ~35% of QR width
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Get text size
        if hasattr(draw, "textbbox"):  # Newer Pillow
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:  # Older Pillow
            text_w, text_h = draw.textsize(label, font=font)

        # Total content height (QR + text + spacing)
        spacing = 20
        content_height = qr_size + spacing + text_h

        # Start Y so content is vertically centered
        start_y = (LABEL_HEIGHT - content_height) // 2

        # Paste QR centered
        qr_x = (LABEL_WIDTH - qr_size) // 2
        page.paste(qr_resized, (qr_x, start_y))

        # Draw text centered under QR
        text_x = (LABEL_WIDTH - text_w) // 2
        text_y = start_y + qr_size + spacing
        draw.text((text_x, text_y), label, font=font, fill="black")

        pages.append(page)

    return pages


# -----------------------
# 3. Save as multi-page PDF
# -----------------------
def save_as_pdf(pages, filename="labels.pdf"):
    if pages:
        pages[0].save(filename, save_all=True, append_images=pages[1:])
        print(f"✅ PDF saved as {filename}")


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    # Example serial numbers
    serial_numbers = ["SR001", "SR002", "SR003", "SR004"]

    qr_images = generate_qr_codes(serial_numbers)
    pages = create_label_pages(qr_images)
    save_as_pdf(pages, "labels.pdf")



