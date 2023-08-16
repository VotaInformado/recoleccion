from django.test import TestCase

from recoleccion.utils.pdf_reader import Pdf


class PdfTestCase(TestCase):
    def test_get_text_has_text_from_both_pages_from_path(self):
        self.pdf = Pdf("recoleccion/tests/test_helpers/files/3050-D-2023.pdf")
        text = self.pdf.get_text()
        self.pdf.close()
        self.assertIn("Cámara de Diputados de la Nación", text)
        self.assertIn("FUNDAMENTOS", text)

    def test_get_text_has_text_from_both_pages_from_io_content(self):
        from io import BytesIO

        with open("recoleccion/tests/test_helpers/files/3050-D-2023.pdf", "rb") as f:
            content = f.read()
            self.pdf = Pdf(BytesIO(content))
        text = self.pdf.get_text()
        self.pdf.close()
        self.assertIn("Cámara de Diputados de la Nación", text)
        self.assertIn("FUNDAMENTOS", text)

    def test_get_text_without_adding_newline_between_every_word(self):
        self.pdf = Pdf("recoleccion/tests/test_helpers/files/3047-D-2023.pdf")
        text = self.pdf.get_text()
        self.pdf.close()
        self.assertIn(
            "INSTITUIR EL 25 DE JULIO COMO DÍA NACIONAL PARA LA PREVENCIÓN", text
        )

    def test_get_text_doesnt_add_innecesary_newlines(self):
        self.pdf = Pdf("recoleccion/tests/test_helpers/files/3008-D-2023.pdf")
        text = self.pdf.get_text()
        self.pdf.close()
        self.assertIn("Reforma Constitucional de la Provincia de Jujuy", text)
        self.assertNotIn("\n\n\n\n", text)

    def test_get_text_separates_words_correctly(self):
        self.pdf = Pdf("recoleccion/tests/test_helpers/files/2875-D-2023.pdf")
        text = self.pdf.get_text()
        self.pdf.close()
        self.assertIn(
            "El Senado y la Cámara de Diputados de la Nación, sancionan con fuerza de Ley",
            text,
        )
        self.assertIn(
            "Artículo 1°: Incorpórase el artículo 290 bis al Código Procesal Penal de la Nación con",
            text,
        )
