import pdfplumber


class PDFExtractionService:
    @staticmethod
    def extract_text(file_stream):
        """Extract text from a PDF file stream."""
        text = ""
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
