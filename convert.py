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
        """Recursively process an element and convert it to Markdown."""
        if element.name is None:  # Text node
            return element.strip()

        elif re.match("^h[1-6]$", element.name):  # Headings (h1 - h6)
            level = element.name[1]
            return f"{'#' * int(level)} {element.get_text(strip=True)}\n"

        elif element.name == "p":  # Paragraphs
            return element.get_text(strip=True) + "\n"

        elif element.name == "a":  # Links
            link_text = element.get_text(strip=True)
            link_href = element.get("href", "#")
            return f"[{link_text}]({link_href})"

        elif element.name == "img":  # Images
            alt_text = element.get("alt", "Image")
            src = element.get("src", "")
            if src:
                img_path = os.path.join(base_dir, src) if not os.path.isabs(src) else src
                media_path = os.path.join(base_dir, "media")
                os.makedirs(media_path, exist_ok=True)

                if os.path.exists(img_path):  # Copy image to media folder
                    dest_path = os.path.join(media_path, os.path.basename(src))
                    shutil.copy(img_path, dest_path)
                    return f"![{alt_text}](media/{os.path.basename(src)})"
                else:
                    return f"![{alt_text}](image-not-found)"

        elif element.name == "div" and "callout" in element.get("class", []):  # Callouts
            title = element.find("h4", class_="callout__title")
            content = element.find("p")
            if title and content:
                return f"\n{{% hint style=\"info\" %}}\n**{title.get_text(strip=True)}**\n\n{content.get_text(strip=True)}\n{{% endhint %}}\n"

        elif element.name in ["ul", "ol"]:  # Lists
            items = []
            for li in element.find_all("li"):
                prefix = "- " if element.name == "ul" else "1. "
                items.append(f"{prefix}{li.get_text(strip=True)}")
            return "\n".join(items) + "\n"

        return ""  # Ignore unknown elements

    # Process elements **in order**
    for child in soup.body.children:
        markdown_content.append(process_element(child))

    return "\n\n".join(filter(None, markdown_content))

# Function to process a ZIP file of HTML pages
def process_html_zip(uploaded_zip):
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        temp_dir = "temp_html_project"
        os.makedirs(temp_dir, exist_ok=True)
        zip_ref.extractall(temp_dir)

        html_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".html"):
                    html_files.append(os.path.join(root, file))

        output_zip_buffer = BytesIO()
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as output_zip:
            for html_file in html_files:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                markdown_content = convert_html_to_markdown(html_content, base_dir=os.path.dirname(html_file))
                markdown_filename = os.path.basename(html_file).replace(".html", ".md")
                output_zip.writestr(markdown_filename, markdown_content)

            media_dir = os.path.join(temp_dir, "media")
            if os.path.exists(media_dir):
                for root, _, files in os.walk(media_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        output_zip.write(file_path, arcname)

        shutil.rmtree(temp_dir)
        output_zip_buffer.seek(0)
        return output_zip_buffer

# Streamlit app
def main():
    st.title("HTML to Markdown Converter")

    st.info("""
    Upload a ZIP file containing HTML files and assets (like images).
    The app will convert each HTML file into a Markdown file and bundle them into a ZIP file for download.
    Images will be referenced correctly and included in a `media` folder.
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
