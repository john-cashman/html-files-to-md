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

    def process_element(element):
        """Recursively process an element and convert it to Markdown."""
        if element in processed_elements or element is None:
            return ""
        processed_elements.add(element)

        if element.name is None:  # Text node
            return element.strip()

        elif re.match("^h[1-6]$", element.name):  # Headings
            level = element.name[1]
            return f"{'#' * int(level)} {element.get_text(strip=True)}\n"

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
        return paragraph if paragraph not in processed_elements else ""

        elif element.name in ["ul", "ol"]:  # Lists
            items = []
            for li in element.find_all("li"):
                prefix = "- " if element.name == "ul" else "1. "
                list_item = f"{prefix}{li.get_text(strip=True)}"
                if list_item not in processed_elements:
                    items.append(list_item)
                    processed_elements.add(list_item)
            return "\n".join(items) + "\n"

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
                    return f"![{alt_text}](media/{os.path.basename(src)})"
                else:
                    return f"![{alt_text}](image-not-found)"

        elif element.name == "div" and "note" in element.get("class", []):  # Convert <div class="note"> to hint block
            content = element.get_text(strip=True)
            processed_elements.add(element)  # The fix is here
            return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n"

        return ""

    for child in soup.body.descendants:
        md_text = process_element(child)
        if md_text.strip() and md_text not in processed_elements:
            markdown_content.append(md_text)
            processed_elements.add(md_text)

    return "\n\n".join(markdown_content)

# ... (rest of the code remains the same)

def process_html_zip(uploaded_zip):
    # ... (this function remains the same)

def main():
    # ... (this function remains the same)

if __name__ == "__main__":
    main()
