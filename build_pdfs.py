import pathlib, html
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

SRC = pathlib.Path("ABES_RAG_DATASET"); OUT = pathlib.Path("ABES_RAG_PDFS")
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=10, leading=14, spaceAfter=4)
head = ParagraphStyle("h", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, spaceAfter=10)
def clean(s):
    for a, b in {"\u2013": "-", "\u2014": "-", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u20b9": "Rs. "}.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")
skip = {"OFFICIAL_PDF_SOURCES.txt"}
for p in sorted(SRC.rglob("*.txt")):
    if "unverified" in p.parts or p.name in skip: continue
    rel = p.relative_to(SRC).with_suffix(".pdf"); dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    title = p.stem.replace("_", " ").upper()
    story = [Paragraph(html.escape(f"ABES Engineering College - {title}"), head)]
    for line in clean(p.read_text(encoding="utf-8")).split("\n"):
        story.append(Spacer(1, 5) if not line.strip() else Paragraph(html.escape(line), body))
    def footer(c, d, name=p.name):
        c.setFont("Helvetica", 8); c.drawString(2*cm, 1.2*cm, f"ABES RAG dataset | {name} | Page {d.page}")
    SimpleDocTemplate(str(dest), pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
                      title=title, author="ABES RAG dataset").build(story, onFirstPage=footer, onLaterPages=footer)
    print("made", dest)
