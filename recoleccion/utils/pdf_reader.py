import pypdfium2 as pdfium

# from pypdf import PdfReader
# from pdfminer.high_level import extract_text


class Pdf:
    pdf = None

    def __init__(self, content):
        self.pdf = pdfium.PdfDocument(content)

    # Get text pypdf
    # def get_text(self):
    #     text_pages = [page.extract_text() for page in self.reader.pages]
    #     full_text = " ".join(text_pages)
    #     return full_text

    # Get text pdfminer
    # def get_text2(self):
    #     return extract_text(self.pdf)

    def get_text(self):
        text_pages = []
        for page in self.pdf:
            textpage = page.get_textpage()
            text_all = textpage.get_text_range()
            text_pages.append(text_all)
        full_text = " ".join(text_pages)
        return full_text

    def close(self):
        self.pdf.close()

    def get_text_and_close(self):
        text = self.get_text()
        self.close()
        return text
