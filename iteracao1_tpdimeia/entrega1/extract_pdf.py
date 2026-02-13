import pypdf
import os

pdf_path = "Rui_Marinho_1171602_2025_12_30_1630.pdf"
md_path = "Rui_Marinho_1171602_2025_12_30_1630.md"

def extract_text_from_pdf(pdf_file_path):
    text = ""
    try:
        with open(pdf_file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                # Add page marker for context (optional, but helpful for long docs)
                text += f"\n\n## Page {page_num + 1}\n\n" 
                text += page_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    return text

if __name__ == "__main__":
    if os.path.exists(pdf_path):
        print(f"Extracting text from {pdf_path}...")
        extracted_text = extract_text_from_pdf(pdf_path)
        
        if extracted_text:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            print(f"Successfully extracted text to {md_path}")
        else:
            print("Failed to extract text.")
    else:
        print(f"File not found: {pdf_path}")
