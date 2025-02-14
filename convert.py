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
        if element is None or element in processed_elements: #check for None and then check if already processed
            return ""

        processed_elements.add(element)

        if element.name == "title":  # Title
            title = element.get_text(strip=True)
            return f"# {title}\n\n" if title else ""

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
                list_item = process_element(li) #recursive call for list items
                if list_item: #add to list only if not empty
                  list_items.append(list_item)


            if list_items:  # Check for empty lists
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
                child_text = process_element(child)  # Recursive call for children
                if child_text: #only add if child_text is not None
                    content += child_text + " "
            content = content.strip()
            return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n" if content else ""

        elif element.name not in ['html', 'body', 'head']:  # Handle other elements
            text = element.get_text(strip=True)
            return text + "\n" if text else ""

        return ""

    if soup.body:
      markdown_content += process_element(soup.body)

    return markdown_content



# ... (rest of the code: process_html_zip and main remain the same)
