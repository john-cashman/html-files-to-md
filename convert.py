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

        processed_elements.add(element)  # Mark element as processed *immediately*

        if element.name == "title":
            title = element.get_text(strip=True)
            return ""  # Title handled separately

        elif element.name is None:  # Text node
            text = element.strip()
            return text if text else ""

        elif re.match("^h[1-6]$", element.name):
            level = element.name[1]
            heading_text = element.get_text(strip=True)
            return f"{'#' * int(level)} {heading_text}\n" if heading_text else ""

        elif element.name == "p":
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

        elif element.name in ["ul", "ol"]:
            list_items = []
            for li in element.find_all("li"):
                list_item_content = process_element(li)  # Recursive call for list items
                if list_item_content:
                    list_items.append(list_item_content)

            if list_items:
                list_type = "- " if element.name == "ul" else "1. "
                return "\n".join(f"{list_type}{item}" for item in list_items) + "\n"
            return ""

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
                    return f"![{alt_text}](media/{os.path.basename(src)})\n"
                else:
                    return f"![{alt_text}](image-not-found)\n"
            return ""

        elif element.name == "div" and "note" in element.get("class", []):
            content = ""
            for child in element.descendants:
                child_text = process_element(child)
                if child_text:
                    content += child_text + " "
            content = content.strip()
            return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n" if content else ""

        elif element.name not in ['html', 'body', 'head']:  # Handle other elements
            text = element.get_text(strip=True)
            return text + "\n" if text else ""

        return ""  # Important: Return empty string if no match

    title = soup.title.string if soup.title else "Untitled"
    markdown_content += f"# {title}\n\n"

    # Exclude navheader and navfooter content
    for child in soup.body.children:  # Iterate through DIRECT children of the body
        if not (child.has_attr('class') and child['class'] in ['navheader', 'navfooter']):
            markdown_content += process_element(child)  # Process the non-nav elements

    return markdown_content, title


def process_html_zip(uploaded_zip):
    # ... (This function remains the same)
    pass # Placeholder for brevity

def main():
    # ... (This function remains the same)
    pass # Placeholder for brevity

if __name__ == "__main__":
    main()
