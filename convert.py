import streamlit as st
import os
import zipfile
import shutil
from io import BytesIO
from bs4 import BeautifulSoup
import re

def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")
    markdown_content = ""
    processed_elements = set()

    def process_element(element):
        if element is None or element in processed_elements:
            return ""

        processed_elements.add(element)

        if element.name == "title":  # Title
            title = element.get_text(strip=True)
            return f"# {title}\n\n" if title else ""

        elif element.name is None:  # Text node
            text = element.strip()
            return text if text else ""

        elif re.match("^h[1-6]$", element.name):  # Headings
            level = element.name[1]
            heading_text = element.get_text(strip=True)
            return f"{'#' * int(level)} {heading_text}\n" if heading_text else ""

        elif element.name == "p":  # Paragraphs
            text_parts = []
            for content in element.contents:
                if isinstance(content, str):
                    text_parts.append(content.strip())
                elif content.name == "a":
                    link_text = content.get_text(strip=True)
                    link_href = content.get("href", "#")
                    text_parts.append(f"[{link_text}]({link_href})")
            paragraph = " ".join(text_parts).strip()
            return paragraph + "\n" if paragraph else ""

        elif element.name in ["ul", "ol"]:  # Lists
            list_items = []
            for li in element.find_all("li"):
                list_item_content = process_element(li)
                if list_item_content:
                    list_items.append(list_item_content)

            if list_items:
                list_type = "- " if element.name == "ul" else "1. "
                return "\n".join(f"{list_type}{item}" for item in list_items) + "\n"
            return ""

        elif element.name == "img":  # Images
            alt_text = element.get("alt", "Image")
            src = element.get("src", "")
            if src:
                img_path = os.path.join(base_dir, src) if not os.path.isabs(src) else src
                media_path = os.path.join(base_dir, "media")
                os.makedirs(media_path, exist_ok=True)
                if os.path.exists(img_path):
                    dest_path = os.path.join(media_path, os.path.basename(src))
                    shutil.copy(img_path, dest_path)
                    return f"![{alt_text}](media/{os.path.basename(src)})\n"
                else:
                    return f"![{alt_text}](image-not-found)\n"
            return ""

        elif element.name == "div" and "note" in element.get("class", []):  # Convert <div class="note"> to hint block
            content = ""
            for child in element.descendants:
                child_text = process_element(child)
                if child_text:
                    content += child_text + " "
            content = content.strip()
            return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n" if content else ""

        elif element.name not in ['html', 'body', 'head']:  # Handle other elements
            text = element.get_text(strip=True)
            return text + "\n" if text else "" #ensure newline is returned


        return ""

    if soup.body:
        markdown_content += process_element(soup.body)

    return markdown_content



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
