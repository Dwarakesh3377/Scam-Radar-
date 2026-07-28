from docx import Document

def dump_docx_to_text(file_path, output_text_path):
    doc = Document(file_path)
    with open(output_text_path, 'w', encoding='utf-8') as f:
        for i, p in enumerate(doc.paragraphs):
            f.write(f"P{i}: {p.text}\n")

if __name__ == "__main__":
    dump_docx_to_text('d:\\scam-risk-detection2\\Chapter7 EndToEnd Flow.docx', 'd:\\scam-risk-detection2\\chapter7_dump.txt')
