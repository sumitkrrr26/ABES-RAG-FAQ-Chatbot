import sys
from pathlib import Path
import pymupdf as fitz


# Main folders
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "extracted_txt"

OUTPUT_DIR.mkdir(exist_ok=True)


def extract_pdf(pdf_path):
    """Extract text from every page of a PDF."""

    doc = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text")

        pages.append(
            f"\n\n===== PAGE {page_number} =====\n\n{text}"
        )

    doc.close()

    return "".join(pages)


def main():

    # If PDF names are provided in command line
    if len(sys.argv) > 1:

        pdf_files = [
            Path(file)
            for file in sys.argv[1:]
            if Path(file).suffix.lower() == ".pdf"
        ]

    else:

        # Find ALL PDFs inside all subfolders
        pdf_files = sorted(
            BASE_DIR.rglob("*.pdf")
        )

    if not pdf_files:

        print("❌ No PDF files found.")

        return

    print(f"Found {len(pdf_files)} PDF files.\n")

    for pdf_path in pdf_files:

        print(f"Processing: {pdf_path}")

        try:

            text = extract_pdf(pdf_path)

            # Preserve folder structure
            relative_path = pdf_path.relative_to(BASE_DIR)

            output_path = (
                OUTPUT_DIR
                / relative_path.parent
                / f"{relative_path.stem}.txt"
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            output_path.write_text(
                text,
                encoding="utf-8"
            )

            print(
                f"✅ Saved: {output_path}"
            )

        except Exception as e:

            print(
                f"❌ Error processing {pdf_path}: {e}"
            )

    print("\n🎉 PDF extraction completed!")


if __name__ == "__main__":
    main()