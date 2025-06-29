import streamlit as st
from bs4 import BeautifulSoup
import re
import json
import logging

# ------------------ Logger Setup ------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


# ------------------ Utility Functions ------------------
def parse_html(html, config):
    soup = BeautifulSoup(html, "html.parser")

    # Book title (from <title>)
    title_tag = soup.title
    book_title = title_tag.string.split()[0] if title_tag else "未知书名"
    logger.info(f"[Book Title]: {book_title}")

    # Chapter title (from configurable id)
    chapter_id = config.get("chapter_title_id", "ChapterTitle")
    chapter_tag = soup.find(id=chapter_id)
    chapter_title = chapter_tag.get_text(strip=True) if chapter_tag else "未知章节"
    logger.info(f"[Chapter Title]: {chapter_title}")

    # Main content (from configurable div id)
    content_div_id = config.get("content_div_id", "Lab_Contents")
    content_div = soup.find(id=content_div_id)
    if content_div:
        logger.info(f"[Content]: Extracting paragraphs from #{content_div_id}")
        paragraphs = [p.get_text(strip=True) for p in content_div.find_all("p")]
        full_text = "\n".join(paragraphs)
    else:
        logger.warning(f"[Content]: #{content_div_id} not found!")
        full_text = ""

    return {
        "book_title": book_title,
        "chapter_title": chapter_title,
        "main_content": full_text,
        "table_of_contents": None,  # future expansion
    }


def save_config(config, path="extractor_config.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_config(path="extractor_config.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"content_div_id": "Lab_Contents", "chapter_title_id": "ChapterTitle"}


# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="📘 Web Novel HTML Extractor", layout="wide")

st.title("📖 Chinese Web Novel Extractor")

uploaded = st.file_uploader("Upload a saved HTML chapter page", type="html")

# Config Panel in Sidebar (for content div id and chapter title id)
with st.sidebar:
    st.header("⚙️ Extraction Config")
    config = load_config()
    content_div_id = st.text_input(
        "Content Div ID", value=config.get("content_div_id", "Lab_Contents")
    )
    chapter_title_id = st.text_input(
        "Chapter Title ID", value=config.get("chapter_title_id", "ChapterTitle")
    )
    config["content_div_id"] = content_div_id
    config["chapter_title_id"] = chapter_title_id
    if st.button("💾 Save Config", key="save_config_btn"):
        save_config(config)
        st.success("Configuration saved!")

# ------------------ HTML Processing ------------------
if uploaded:
    html = uploaded.read().decode("utf-8")
    extracted = parse_html(html, config)

    with st.expander(f"📘 Book Title: {extracted['book_title']}"):
        st.write(extracted["book_title"])
    with st.expander(f"📄 Chapter Title: {extracted['chapter_title']}"):
        st.write(extracted["chapter_title"])

    with st.expander("📄 View Extracted Content"):
        st.code(extracted["main_content"], language="markdown")
        st.download_button(
            "📥 Download .txt", extracted["main_content"], file_name="chapter.txt"
        )

    # Download button at the bottom with book/chapter title and content
    download_text = f"Book: {extracted['book_title']}\nChapter: {extracted['chapter_title']}\n\n{extracted['main_content']}"
    st.download_button(
        "📥 Download Book + Chapter + Content (.txt)",
        download_text,
        file_name=f"{extracted['book_title']}_{extracted['chapter_title']}.txt".replace(
            "/", "_"
        ).replace("\\", "_"),
    )

# Footer
st.markdown("---")
st.caption("Built for offline Chinese web novel extraction.")
