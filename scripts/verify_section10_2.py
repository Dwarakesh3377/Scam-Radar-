from docx import Document

def dump_docx_to_text(file_path):
    doc = Document(file_path)
    for p in doc.paragraphs:
        print(p.text)

if __name__ == "__main__":
    dump_docx_to_text('d:\\scam-risk-detection2\\Section_10_2_Evaluation.docx')
