import streamlit as st
import os
import zipfile
import shutil
from io import BytesIO
from bs4 import BeautifulSoup
import re

# Function to convert HTML to Markdown while preserving structure
def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")
    markdown_content = []

    def process_element(element):
        if element.name is None:  # Text node
            return element.strip()
        elif re.match("^h[1-6]$", element.name):  # Headings
            level = element.name[1]
            return f"{'#' * int(level)} {element.get_text(strip=True)}\n"
        elif element.name == "p":  # Paragraphs (handling inline links correctly)
            text_parts = []
            for content in element.contents:
                if isinstance(content, str):
                    text_parts.append(content.strip())
                elif content.name == "a":
                    link_text = content.get_text(strip=True)
                    link_href = content.get("href", "#")
                    text_parts.append(f"[{link_text}]({link_href})")
            return " ".join(text_parts).strip()
        elif element.name == "div" and "note" in element.get("class", []):  # Convert <div class="note"> to hint block
            hint_content = []
            for content in element.contents:
                if isinstance(content, str):
                    hint_content.append(content.strip())
                elif content.name == "a":
                    link_text = content.get_text(strip=True)
                    link_href = content.get("href", "#")
                    hint_content.append(f"[{link_text}]({link_href})")
            return f"\n{{% hint style=\"info\" %}}\n{' '.join(hint_content).strip()}\n{{% endhint %}}\n"
        return ""

    for child in soup.body.find_all(recursive=False):
        md_text = process_element(child)
        if md_text.strip():
            markdown_content.append(md_text)

    return "\n\n".join(markdown_content)

# Function to process a ZIP file of HTML pages
def process_html_zip(uploaded_zip):
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        temp_dir = "temp_html_project"
        os.makedirs(temp_dir, exist_ok=True)
        zip_ref.extractall(temp_dir)
        
        html_files = [os.path.join(root, file) for root, _, files in os.walk(temp_dir) for file in files if file.endswith(".html")]
        
        output_zip_buffer = BytesIO()
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as output_zip:
            for html_file in html_files:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                markdown_content = convert_html_to_markdown(html_content, base_dir=os.path.dirname(html_file))
                if markdown_content.strip():
                    markdown_filename = os.path.basename(html_file).replace(".html", ".md")
                    output_zip.writestr(markdown_filename, markdown_content)

        shutil.rmtree(temp_dir)
        output_zip_buffer.seek(0)
        return output_zip_buffer

# Streamlit app
def main():
    st.title("HTML to Markdown Converter")
    st.info("""
    Upload a ZIP file containing HTML files and assets (like images).
    The app will convert each HTML file into a Markdown file and bundle them into a ZIP file for download.
    """)

    uploaded_file = st.file_uploader("Upload a ZIP file", type=["zip"])
    if uploaded_file is not None:
        try:
            output_zip = process_html_zip(uploaded_file)
            st.success("Conversion successful! Download your Markdown files below.")
            st.download_button(
                label="Download ZIP file",
                data=output_zip,
                file_name="markdown_files.zip",
                mime="application/zip",
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
