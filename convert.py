def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")

    if not soup.body:
        return ""

    markdown_content = ""  # Initialize as a string
    processed_elements = set()

    # Extract title from <title> tag
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else "Untitled"  # Default if no title

    if page_title:  # Add title as top-level heading in Markdown
        markdown_content += f"# {page_title}\n\n"  # Append to string

    def process_element(element):
        if element in processed_elements or element is None:
            return ""

        processed_elements.add(element)  # Add the ELEMENT ITSELF to the set

        if element.name is None:  # Text node
            text = element.strip()
            return text if text else "" #return text if text exists otherwise return empty string

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
                item_text = li.get_text(strip=True)
                list_items.append(item_text)

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
            for child in element.descendants:  # Iterate over all descendants of the div
                child_text = process_element(child)  # Process each child recursively
                if child_text:  # Check if child_text is not None
                    content += child_text + " "  # Accumulate the content

            content = content.strip()  # Remove leading/trailing spaces from content
            return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n" if content else ""

        return ""

    for child in soup.body.descendants:
        md_text = process_element(child)
        if md_text:  # Only add non-empty strings and handle None values
            markdown_content += md_text  # Append to string

    return markdown_content, page_title  # Return as a single string

# ... (rest of the code remains the same)
