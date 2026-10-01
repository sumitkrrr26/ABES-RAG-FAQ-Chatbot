from pathlib import Path
import re
import json
import shutil


BASE_DIR = Path(__file__).parent

INPUT_DIR = BASE_DIR / "extracted_txt"
OUTPUT_DIR = BASE_DIR / "chunks"

TARGET_SIZE = 600
MAX_SIZE = 750
OVERLAP = 100


def clean_text(text):
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Keep paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def find_break_position(text, target, max_size):

    # Don't go beyond maximum size
    search_area = text[:max_size]

    # Prefer paragraph/line breaks
    positions = [
        search_area.rfind("\n\n", 0, target + 100),
        search_area.rfind("\n", 0, target + 100),

        # Sentence boundaries
        search_area.rfind(". ", 0, target + 100),
        search_area.rfind("? ", 0, target + 100),
        search_area.rfind("! ", 0, target + 100),

        # Other useful boundaries
        search_area.rfind("; ", 0, target + 100),
        search_area.rfind(": ", 0, target + 100),
    ]

    positions = [
        p for p in positions
        if p >= int(target * 0.6)
    ]

    if positions:
        position = max(positions)

        # Include punctuation
        if search_area[position:position + 2] in [
            ". ", "? ", "! ", "; ", ": "
        ]:
            position += 1

        return position

    # Fallback
    return min(target, len(text))


def create_chunks(page_text, page_number):

    page_text = clean_text(page_text)

    if not page_text:
        return []

    chunks = []

    start = 0

    while start < len(page_text):

        remaining = page_text[start:]

        if len(remaining) <= TARGET_SIZE:
            chunk = remaining.strip()

            if chunk:
                chunks.append({
                    "page": page_number,
                    "text": chunk
                })

            break

        break_position = find_break_position(
            remaining,
            TARGET_SIZE,
            MAX_SIZE
        )

        chunk = remaining[:break_position].strip()

        if chunk:
            chunks.append({
                "page": page_number,
                "text": chunk
            })

        # Prevent infinite loop
        if break_position <= 0:
            break

        # Keep overlap
        start = start + break_position - OVERLAP

        if start < 0:
            start = 0

    return chunks


def process_file(txt_file):

    text = txt_file.read_text(
        encoding="utf-8"
    )

    pages = re.split(
        r"===== PAGE (\d+) =====",
        text
    )

    chunks = []

    i = 1

    while i < len(pages):

        page_number = int(pages[i])
        page_text = pages[i + 1]

        page_chunks = create_chunks(
            page_text,
            page_number
        )

        chunks.extend(page_chunks)

        i += 2

    relative_path = txt_file.relative_to(
        INPUT_DIR
    )

    output_file = (
        OUTPUT_DIR
        / relative_path.parent
        / f"{relative_path.stem}_chunks.json"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    final_data = []

    for index, chunk in enumerate(chunks):

        final_data.append({
            "chunk_id": index,
            "source": txt_file.name,
            "page": chunk["page"],
            "text": chunk["text"]
        })

    output_file.write_text(
        json.dumps(
            final_data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        f"✅ {txt_file.name} → "
        f"{len(final_data)} chunks"
    )

    return len(final_data)


def main():

    txt_files = sorted(
        INPUT_DIR.rglob("*.txt")
    )

    if not txt_files:
        print("❌ No TXT files found.")
        return

    # Remove old chunks
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    print(
        f"Found {len(txt_files)} text files.\n"
    )

    total_chunks = 0

    for txt_file in txt_files:

        total_chunks += process_file(
            txt_file
        )

    print("\n===================================")
    print("🎉 Chunking completed!")
    print(f"📄 Text files: {len(txt_files)}")
    print(f"🧩 Total chunks: {total_chunks}")
    print(f"📏 Target size: {TARGET_SIZE}")
    print(f"📏 Maximum size: {MAX_SIZE}")
    print(f"🔁 Overlap: {OVERLAP}")
    print("===================================")


if __name__ == "__main__":
    main()