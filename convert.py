def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")
    
    if not soup.body:
        return ""

    markdown_content = []
    processed_elements = set()  # This set now tracks ALL processed text

    def process_element(element):
        if element in processed_elements or element is None:
            return ""

        if element.name is None:  # Text node
            text = element.strip()
            if text and text not in processed_elements: #Check if the text has already been processed
              processed_elements.add(text) #add the text to processed_elements
              return text
            return ""

        elif re.match("^h[1-6]$", element.name):  # Headings
            level = element.name[1]
            heading_text = element.get_text(strip=True)
            if heading_text not in processed_elements:
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
            if paragraph and paragraph not in processed_elements:
                processed_elements.add(paragraph)
                return paragraph
            return ""

        elif element.name in ["ul", "ol"]:  # Lists
            items = []
            for li in element.find_all("li"):
                list_item = li.get_text(strip=True)
                if list_item and list_item not in processed_elements:
                    items.append(list_item)
                    processed_elements.add(list_item)
            return "\n".join(("- " if element.name == "ul" else "1. ") + item for item in items) + "\n"

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
            return "" #return empty string if no src

        elif element.name == "div" and "note" in element.get("class", []):  # Convert <div class="note"> to hint block
            content = element.get_text(strip=True)
            if content not in processed_elements: #Check if the content has already been processed
                processed_elements.add(content) #add the content to processed_elements
                return f"\n{{% hint style=\"info\" %}}\n{content}\n{{% endhint %}}\n"
            return "" #Return empty string if the content has already been processed

        return ""

    for child in soup.body.descendants:
        md_text = process_element(child)
        if md_text.strip():
            markdown_content.append(md_text)

    return "\n\n".join(markdown_content)
