import streamlit as st
import os
import zipfile
import shutil
from io import BytesIO
from bs4 import BeautifulSoup
import re

# This Function convert sHTML to Markdown using beautiful soup - reference 
def convert_html_to_markdown(html_content, base_dir):
    soup = BeautifulSoup(html_content, "html.parser")
    markdown_content = []

    # Convert headings
    for heading in soup.find_all(re.compile("^h[1-6]$")):
        level = heading.name[1]  # Extract heading level (1-6)
        markdown_content.append(f"{'#' * int(level)} {heading.get_text(strip=True)}")

    # Convert paragraphs
    for paragraph in soup.find_all("p"):
        markdown_content.append(paragraph.get_text(strip=True))

    # Convert links
    for a_tag in soup.find_all("a"):
        link_text = a_tag.get_text(strip=True)
        link_href = a_tag.get("href", "#")
        markdown_content.append(f"[{link_text}]({link_href})")

    # Convert images
    for img in soup.find_all("img"):
        alt_text = img.get("alt", "Image")
        src = img.get("src", "")
        if src:
            # Save images into a media folder
            media_path = os.path.join(base_dir, "media")
            os.makedirs(media_path, exist_ok=True)
            img_file_path = os.path.join(media_path, os.path.basename(src))
            with open(img_file_path, "wb") as f:
                f.write(img["data"])
            markdown_content.append(f"![{alt_text}](media/{os.path.basename(src)})")

    # Convert callouts - this callout is kind aimed at how zendesk do callouts - there's likely a better way to do this
    for div in soup.find_all("div", class_="callout"):
        title = div.find("h4", class_="callout__title")
        content = div.find("p")
        if title and content:
            markdown_content.append(f"\n{{% hint style=\"info\" %}}\n**{title.get_text(strip=True)}**\n\n{content.get_text(strip=True)}\n{{% endhint %}}\n")

    return "\n\n".join(markdown_content)

# Function to process a ZIP file of HTML pages
def process_html_zip(uploaded_zip):
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        temp_dir = "temp_html_project"
        os.makedirs(temp_dir, exist_ok=True)
        zip_ref.extractall(temp_dir)

        # Collect all HTML files in the extracted directory
        html_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".html"):
                    html_files.append(os.path.join(root, file))

        # Create a new ZIP to store Markdown files
        output_zip_buffer = BytesIO()
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as output_zip:
            for html_file in html_files:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Convert HTML to Markdown
                markdown_content = convert_html_to_markdown(html_content, base_dir=os.path.dirname(html_file))

                # Save Markdown file
                markdown_filename = os.path.basename(html_file).replace(".html", ".md")
                output_zip.writestr(markdown_filename, markdown_content)

            # Add media folder to the ZIP if it exists
            media_dir = os.path.join(temp_dir, "media")
            if os.path.exists(media_dir):
                for root, _, files in os.walk(media_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        output_zip.write(file_path, arcname)

        # Clean up temporary directory
        shutil.rmtree(temp_dir)

        output_zip_buffer.seek(0)
        return output_zip_buffer

# Streamlit app
def main():
    st.title("HTML Project to Markdown Converter")

    st.info("""
    Upload a ZIP file containing HTML files and assets (like images). 
    The app will convert each HTML file into a Markdown file and bundle them into a ZIP file for download.
    Images will be referenced correctly and included in a `media` folder.
    """)

    # File uploader
    uploaded_file = st.file_uploader("Upload a ZIP file", type=["zip"])

    if uploaded_file is not None:
        try:
            # Process the uploaded ZIP file
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
