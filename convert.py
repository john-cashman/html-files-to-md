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

    # Extract title from <title> tag
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else "Untitled"  # Default if no title

    if page_title:  # Add title as top-level heading in Markdown
        markdown_content.append(f"# {page_title}\n\n")  # Add a newline after the title

    def process_element(element):
        if element in processed_elements or element is None:
            return ""

        if element.name is None:  # Text node
            text = element.strip()
            if text and text not in processed_elements:
                processed_elements.add(text)
                return text
            return ""

        elif re.match("^h[1-6]$", element.name):  # Headings
            level = element.name[1]
            heading_text = element.get_text(strip=True)
            if heading_text and heading_text not in processed_elements:  # Check for empty headings
                processed_elements.add(heading_text)
                return f"{'#' * int(level)} {heading_text}\n"
            return ""

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

            # Check if this exact paragraph content has already been processed
            if paragraph and paragraph not in processed_elements:
                processed_elements.add(paragraph)  # Mark the paragraph as processed
                return paragraph + "\n" # Add newline at end of paragraph
            return ""  # Return empty string if already processed or empty


        elif element.name in ["ul", "ol"]:  # Lists
            list_items = []
            for li in element.find_all("li"):
                item_text = li.get_text(strip=True)
                if item_text and item_text not in processed_elements:
                    list_items.append(item_text)
                    processed_elements.add(item_text)  # Process each list item

            if list_items:  # Check for empty lists
                list_type = "- " if element.name == "ul" else "1. "
                return "\n".join(f"{list_type}{item}" for item in list_items) + "\n"  #Newline after list
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
                    return f"![{alt_text}](media/{os.path.basename(src)})\n" #Newline after image
                else:
                    return f"![{alt_text}](image-not-found)\n" #Newline after image
            return ""

        elif element.name == "div" and "note" in element.get("class", []):  # Convert <div class="note"> to hint block
            content = ""
            for child in element.descendants:  # Iterate over all descendants of the div
                child_text = process_element(child)  # Process each child recursively
                if child_text:
                    content += child_text + " "  # Accumulate the content

            content = content.strip()  # Remove leading/trailing spaces from content
            if content and content not in processed_elements:  # Check for empty content or duplicate content
                processed_elements.add(content)
                return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n"  # Newlines around hint
            return ""

        return ""

    for child in soup.body.descendants:
        md_text = process_element(child)
        if md_text.strip():  # Only add non-empty strings
            markdown_content.append(md_text)

    return "".join(markdown_content), page_title  # Return as a single string


def process_html_zip(uploaded_zip):
    # ... (rest of the code is the same)
        markdown_content, _ = convert_html_to_markdown(html_content, base_dir=os.path.dirname(html_file)) #added _ to capture page_title
        markdown_filename = os.path.basename(html_file).replace(".html", ".md") #Filename is same as html
        output_zip.writestr(markdown_filename, markdown_content)
    # ... (rest of the code is the same)
