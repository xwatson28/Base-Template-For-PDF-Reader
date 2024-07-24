import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import io
import os
import re
import streamlit as st

st.title("Application for Wasif Khan")

def extract_content_from_pdf(input_pdf_path):
    content = []
    date_time_pattern = re.compile(r'\d{2}/\d{2}/\d{4}, \d{2}:\d{2}.*', re.DOTALL)
    
    try:
        doc = fitz.open(input_pdf_path)
        print(f"Opened PDF: {input_pdf_path}")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")

            # Remove date, time, and everything after it
            text = date_time_pattern.sub('', text)
            
            content.append(("text", text, page_num + 1))

            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                content.append(("image", image, page_num + 1))
                
    except Exception as e:
        print(f"Error extracting content: {e}")
    
    return content

def create_pdf_with_selected_images_and_text(content, selected_image_indices, output_pdf_path):
    try:
        c = canvas.Canvas(output_pdf_path, pagesize=letter)
        width, height = letter
        
        previous_image_index = -1
        
        for item_index in selected_image_indices:
            y_position = height - 40
            text_before_image = ""
            
            if previous_image_index != -1:
                for text_item_index in range(previous_image_index + 1, item_index):
                    if content[text_item_index][0] == "text":
                        text_before_image = content[text_item_index][1]
                        break
            else:
                for text_item_index in range(item_index):
                    if content[text_item_index][0] == "text":
                        text_before_image = content[text_item_index][1]
                        break

            if text_before_image:
                # Add text to the page
                text_lines = text_before_image.split('\n')
                for line in text_lines:
                    if y_position < 50:
                        c.showPage()
                        y_position = height - 40
                    c.drawString(30, y_position, line)
                    y_position -= 15

            # Add image to the page
            img = content[item_index][1]
            img_width, img_height = img.size
            aspect_ratio = img_height / img_width
            resized_width = width - 60
            resized_height = int(resized_width * aspect_ratio)

            if resized_height > (y_position - 50):
                resized_height = y_position - 50
                resized_width = int(resized_height / aspect_ratio)

            img = img.resize((int(resized_width), int(resized_height)))
            temp_image_path = f"temp_image_{item_index}.png"
            img.save(temp_image_path)

            x = (width - resized_width) / 2
            c.drawImage(temp_image_path, x, y_position - resized_height - 20, resized_width, resized_height)
            c.showPage()  # Move to the next page after adding the image

            os.remove(temp_image_path)
            previous_image_index = item_index

        c.save()
        print(f"Saved PDF: {output_pdf_path}")
        
    except Exception as e:
        print(f"Error creating PDF: {e}")

def main():
    st.title("PDF Content Extractor")

    input_pdf_file = st.file_uploader("Upload your PDF file", type="pdf")
    if input_pdf_file is not None:
        input_pdf_file_path = os.path.join("temp_input.pdf")
        with open(input_pdf_file_path, "wb") as f:
            f.write(input_pdf_file.read())

        extracted_content = extract_content_from_pdf(input_pdf_file_path)
        
        selected_images = []
        selected_image_indices = []
        for item_index, (item_type, item, page_num) in enumerate(extracted_content):
            if item_type == "text":
                st.text(item)
            elif item_type == "image":
                st.image(item)
                if st.checkbox(f"Include image {item_index + 1} from page {page_num}", key=f"image_{item_index}"):
                    selected_image_indices.append(item_index)

        if st.button("Create PDF"):
            output_pdf_file_path = "output.pdf"
            create_pdf_with_selected_images_and_text(extracted_content, selected_image_indices, output_pdf_file_path)
            st.success("PDF created successfully!")
            with open(output_pdf_file_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="extracted_images.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
