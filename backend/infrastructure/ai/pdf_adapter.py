import pdfplumber


class PDFExtractionService:
    @staticmethod
    def extract_text(file_stream):
        """
        Extract text from a PDF file stream using pdfplumber.
        - Validates page count (≤ 500 pages per brief).
        - Extracts text page by page, tracking page numbers.
        Returns: (text: str, page_count: int)
        Raises: ValueError for protected/unreadable PDFs or page count exceeded.
        """
        MAX_PAGES = 500

        text_parts = []
        with pdfplumber.open(file_stream) as pdf:
            page_count = len(pdf.pages)

            if page_count == 0:
                raise ValueError("PDF has no pages or is corrupted.")

            if page_count > MAX_PAGES:
                raise ValueError(
                    f"PDF has {page_count} pages, which exceeds the {MAX_PAGES}-page limit."
                )

            for i, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Prefix with page marker so chunks can track page_number
                        text_parts.append(f"[PAGE:{i}]\n{page_text}")
                except Exception as e:  # noqa: BLE001
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(f"Skipped unreadable page {i}: {e}")
                    continue

        return "\n".join(text_parts), page_count
