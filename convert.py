import streamlit as st
import os
import zipfile
import shutil
from io import BytesIO
from bs4 import BeautifulSoup
import re

def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")
    
    if not soup.body:
        return ""

    markdown_content = []
    processed_elements = set()

    def process_element(element, inside_hint_block=False, inside_list=False):
        if element is None or element.get_text(strip=True) is None:
            return ""
        
        if element.name is None:
            return element.strip()

        elif re.match("^h[1-6]$", element.name):
            level = element.name[1]
            return f"{'#' * int(level)} {element.get_text(strip=True)}\n"

        elif element.name in ["p", "li"]:
            text_parts = []
            for content in element.contents:
                if isinstance(content, str):
                    text_parts.append(content.strip())
                elif content.name == "a":
                    link_text = content.get_text(strip=True) if content.get_text(strip=True) else "Untitled"
                    link_href = content.get("href", "#").replace(".html", ".md")
                    text_parts.append(f"[{link_text}]({link_href})")
            paragraph_text = " ".join(text_parts).strip()
            
            if inside_list:
                return paragraph_text  # Keep list items properly formatted
            
            processed_elements.add(paragraph_text)
            return paragraph_text

        elif element.name in ["ul", "ol"]:
            items = []
            for li in element.find_all("li", recursive=False):
                prefix = "- " if element.name == "ul" else "1. "
                list_item_content = process_element(li, inside_list=True)
                if list_item_content.strip():
                    items.append(f"{prefix}{list_item_content}")
            return "\n".join(items) + "\n"

        elif element.name == "img":
            alt_text = element.get("alt", "Image")
            src = element.get("src", "")
            if src:
                img_path = os.path.join(base_dir, src) if not os.path.isabs(src) else src
                media_path = os.path.join(base_dir, "media")
                os.makedirs(media_path, exist_ok=True)
                if os.path.exists(img_path):
                    dest_path = os.path.join(media_path, os.path.basename(src))
                    shutil.copy(img_path, dest_path)
                    return f"![{alt_text}](media/{os.path.basename(src)})"
                else:
                    return f"![{alt_text}](image-not-found)"

        elif element.name == "div" and "note" in element.get("class", []):
            note_image = ""
            img_tag = element.find("img")
            if img_tag:
                note_image = process_element(img_tag)
            
            content_parts = []
            for child in element.find_all("p", recursive=True):
                content_parts.append(process_element(child, inside_hint_block=True))
            
            content = "\n".join(filter(None, content_parts)).strip()
            
            return f"\n{{% hint style=\"info\" %}}\n{note_image}\n{content}\n{{% endhint %}}\n"

        return ""

def generate_summary_md(index_html_path):
    """Generate a SUMMARY.md file from index-en.html."""
    with open(index_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    summary_lines = ["# Summary", ""]
    links_found = False
    
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True) if link.get_text() else "Untitled"
        href = link.get("href", "").replace(".html", ".md")
        if href:
            summary_lines.append(f"- [{text}]({href})")
            links_found = True
    
    return "\n".join(summary_lines) if links_found else ""

def process_html_zip(uploaded_zip):
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        temp_dir = "temp_html_project"
        os.makedirs(temp_dir, exist_ok=True)
        zip_ref.extractall(temp_dir)

        html_files = [os.path.join(root, file) for root, _, files in os.walk(temp_dir) for file in files if file.endswith(".html")]
        index_html_path = os.path.join(temp_dir, "index-en.html")

        output_zip_buffer = BytesIO()
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as output_zip:
            for html_file in html_files:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                markdown_content = convert_html_to_markdown(html_content, base_dir=os.path.dirname(html_file))
                markdown_filename = os.path.basename(html_file).replace(".html", ".md")
                
                if markdown_content.strip():
                    output_zip.writestr(markdown_filename, markdown_content)
                else:
                    print(f"Skipping empty Markdown file: {markdown_filename}")
            
            if os.path.exists(index_html_path):
                summary_md_content = generate_summary_md(index_html_path)
                if summary_md_content.strip():
                    output_zip.writestr("SUMMARY.md", summary_md_content)
            
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
    If `index-en.html` is found, a `SUMMARY.md` will be generated as a table of contents.
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
