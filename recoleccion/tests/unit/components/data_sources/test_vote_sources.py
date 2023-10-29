from django.test import TestCase
from recoleccion.components.data_sources.votes_source import (
    SenateVotesSource,
    DeputyVotesSource,
    VoteTypes,
    VoteChoices,
)
from bs4 import BeautifulSoup


class DeputyVotesSourceTestCase(TestCase):
    def test_get_vote_info_parses_vote_correctly_for_afirmative_votes(self):
        cells_data = """
            <td style="vertical-align: middle; text-align: center">
            <div id="container-A4608">
                <a class="example-image-link" data-lightbox="AGUIRRE, HILDA CLELIA" data-title="AGUIRRE, HILDA CLELIA" href="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" id="A4608-a">
                <img alt="AGUIRRE,HILDA CLELIA" data-toggle="tooltip" id="A4608-img" onerror="this.src='/bundles/app/images/img-perfil.png'" src="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" style="padding: 0px !important;width: 50px !important; height: 50px !important" title="AGUIRRE, HILDA CLELIA" />
                </a>
            </div>
            </td>, <td data-order="aguirre, hilda clelia" style="vertical-align: middle">
            <!-- aguirre, hilda clelia--> AGUIRRE, HILDA CLELIA
            </td>, <td data-order="frente de todos" style="vertical-align: middle">
            <!-- frente de todos --> Frente De Todos
            </td>, <td data-order="la rioja" style="vertical-align: middle">
            <!-- la rioja --> La Rioja
            </td>, <td style=" vertical-align: middle">
            <center>
                <span class="label label-success col-sm-9 force-square">AFIRMATIVO</span>
            </center>
            </td>, <td data-order="z" style="vertical-align: middle">
            <center>

            </center>
            </td>
        """
        rows_data = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = DeputyVotesSource.get_vote_info(rows_data)

        self.assertEqual(vote["vote"], VoteChoices.POSITIVE)
        self.assertEqual(vote["name"], "Hilda Clelia")
        self.assertEqual(vote["last_name"], "Aguirre")
        self.assertEqual(vote["party"], "Frente De Todos")
        self.assertEqual(vote["province"].label, "La Rioja")

    def test_get_vote_info_parses_vote_correctly_for_negative_vote(self):
        cells_data = """
            <td style="vertical-align: middle; text-align: center">
            <div id="container-A4608">
                <a class="example-image-link" data-lightbox="AGUIRRE, HILDA CLELIA" data-title="AGUIRRE, HILDA CLELIA" href="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" id="A4608-a">
                <img alt="AGUIRRE,HILDA CLELIA" data-toggle="tooltip" id="A4608-img" onerror="this.src='/bundles/app/images/img-perfil.png'" src="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" style="padding: 0px !important;width: 50px !important; height: 50px !important" title="AGUIRRE, HILDA CLELIA" />
                </a>
            </div>
            </td>, <td data-order="aguirre, hilda clelia" style="vertical-align: middle">
            <!-- aguirre, hilda clelia--> AGUIRRE, HILDA CLELIA
            </td>, <td data-order="frente de todos" style="vertical-align: middle">
            <!-- frente de todos --> Frente De Todos
            </td>, <td data-order="la rioja" style="vertical-align: middle">
            <!-- la rioja --> La Rioja
            </td>, <td style=" vertical-align: middle">
            <center>
                <span class="label label-success col-sm-9 force-square">NEGATIVO</span>
            </center>
            </td>, <td data-order="z" style="vertical-align: middle">
            <center>

            </center>
        </td>
        """
        rows_data = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = DeputyVotesSource.get_vote_info(rows_data)

        self.assertEqual(vote["vote"], VoteChoices.NEGATIVE)
        self.assertEqual(vote["name"], "Hilda Clelia")
        self.assertEqual(vote["last_name"], "Aguirre")
        self.assertEqual(vote["party"], "Frente De Todos")
        self.assertEqual(vote["province"].label, "La Rioja")

    def test_get_vote_info_parses_vote_correctly_for_absent_vote(self):
        cells_data = """
            <td style="vertical-align: middle; text-align: center">
            <div id="container-A4608">
                <a class="example-image-link" data-lightbox="AGUIRRE, HILDA CLELIA" data-title="AGUIRRE, HILDA CLELIA" href="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" id="A4608-a">
                <img alt="AGUIRRE,HILDA CLELIA" data-toggle="tooltip" id="A4608-img" onerror="this.src='/bundles/app/images/img-perfil.png'" src="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" style="padding: 0px !important;width: 50px !important; height: 50px !important" title="AGUIRRE, HILDA CLELIA" />
                </a>
            </div>
            </td>, <td data-order="aguirre, hilda clelia" style="vertical-align: middle">
            <!-- aguirre, hilda clelia--> AGUIRRE, HILDA CLELIA
            </td>, <td data-order="frente de todos" style="vertical-align: middle">
            <!-- frente de todos --> Frente De Todos
            </td>, <td data-order="la rioja" style="vertical-align: middle">
            <!-- la rioja --> La Rioja
            </td>, <td style=" vertical-align: middle">
            <center>
                <span class="label label-success col-sm-9 force-square">AUSENTE</span>
            </center>
            </td>, <td data-order="z" style="vertical-align: middle">
            <center>

            </center>
        </td>
        """
        rows_data = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = DeputyVotesSource.get_vote_info(rows_data)

        self.assertEqual(vote["vote"], VoteChoices.ABSENT)
        self.assertEqual(vote["name"], "Hilda Clelia")
        self.assertEqual(vote["last_name"], "Aguirre")
        self.assertEqual(vote["party"], "Frente De Todos")
        self.assertEqual(vote["province"].label, "La Rioja")

    def test_get_vote_info_parses_vote_correctly_for_absention_vote(self):
        cells_data = """
            <td style="vertical-align: middle; text-align: center">
            <div id="container-A4608">
                <a class="example-image-link" data-lightbox="AGUIRRE, HILDA CLELIA" data-title="AGUIRRE, HILDA CLELIA" href="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" id="A4608-a">
                <img alt="AGUIRRE,HILDA CLELIA" data-toggle="tooltip" id="A4608-img" onerror="this.src='/bundles/app/images/img-perfil.png'" src="https://votaciones.hcdn.gob.ar/public/diputados/images/A4608.jpg" style="padding: 0px !important;width: 50px !important; height: 50px !important" title="AGUIRRE, HILDA CLELIA" />
                </a>
            </div>
            </td>, <td data-order="aguirre, hilda clelia" style="vertical-align: middle">
            <!-- aguirre, hilda clelia--> AGUIRRE, HILDA CLELIA
            </td>, <td data-order="frente de todos" style="vertical-align: middle">
            <!-- frente de todos --> Frente De Todos
            </td>, <td data-order="la rioja" style="vertical-align: middle">
            <!-- la rioja --> La Rioja
            </td>, <td style=" vertical-align: middle">
            <center>
                <span class="label label-success col-sm-9 force-square">ABSTENCION</span>
            </center>
            </td>, <td data-order="z" style="vertical-align: middle">
            <center>

            </center>
        </td>
        """
        rows_data = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = DeputyVotesSource.get_vote_info(rows_data)

        self.assertEqual(vote["vote"], VoteChoices.ABSTENTION)
        self.assertEqual(vote["name"], "Hilda Clelia")
        self.assertEqual(vote["last_name"], "Aguirre")
        self.assertEqual(vote["party"], "Frente De Todos")
        self.assertEqual(vote["province"].label, "La Rioja")


class SenateVotesSourceTestCase(TestCase):
    def test_get_vote_info_parses_vote_correctly_for_afirmative_votes(self):
        headers = {
            "Foto": 0,
            "Senador": 1,
            "Bloque": 2,
            "Provincia": 3,
            "¿Cómo votó?": 4,
        }
        vote_date = "30/06/2022"
        vote_type = VoteTypes.GENERAL
        cells_data = """
            <td style="width: 100px;">
              <img alt="Foto de la Senador Nacional no disponible" src="/bundles/senadosenadores/images/fsenaG/noDisponible.png" title="Foto de la Senador Nacional no disponible"/>
            </td>, 
            <td>POGGI, CLAUDIO JAVIER</td>, 
            <td class="ocultar">AVANZAR SAN LUIS</td>, 
            <td class="ocultar">SAN LUIS</td>, 
            <td> 
              <span style="display:none; color=#6cc39f">positivo</span>
              <div style="color:#6cc39f;">AFIRMATIVO</div>
            </td>
        """
        cells = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = SenateVotesSource.get_vote_info(
            vote_date=vote_date, vote_type=vote_type, headers=headers, cells=cells
        )

        self.assertEqual(vote["vote"], VoteChoices.POSITIVE)
        self.assertEqual(vote["vote_type"], vote_type)
        self.assertEqual(vote["date"], vote_date)
        self.assertEqual(vote["name"], "Claudio Javier")
        self.assertEqual(vote["last_name"], "Poggi")
        self.assertEqual(vote["party"], "AVANZAR SAN LUIS")
        self.assertEqual(vote["province"].label, "San Luis")

    def test_get_vote_info_parses_vote_correctly_for_abstent_vote(self):
        headers = {
            "Foto": 0,
            "Senador": 1,
            "Bloque": 2,
            "Provincia": 3,
            "¿Cómo votó?": 4,
        }
        vote_date = "30/06/2022"
        vote_type = VoteTypes.GENERAL
        cells_data = """
            <td style="width: 100px;">
              <img alt="Foto de la Senador Nacional no disponible" src="/bundles/senadosenadores/images/fsenaG/noDisponible.png" title="Foto de la Senador Nacional no disponible"/>
            </td>, 
            <td>POGGI, CLAUDIO JAVIER</td>, 
            <td class="ocultar">AVANZAR SAN LUIS</td>, 
            <td class="ocultar">SAN LUIS</td>, 
            <td> 
              <span style="display:none; color=#6cc39f">ausente</span>
              <div style="color:#6cc39f;">AUSENTE</div>
            </td>
        """
        cells = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = SenateVotesSource.get_vote_info(
            vote_date=vote_date, vote_type=vote_type, headers=headers, cells=cells
        )

        self.assertEqual(vote["vote"], VoteChoices.ABSENT)
        self.assertEqual(vote["vote_type"], vote_type)
        self.assertEqual(vote["date"], vote_date)
        self.assertEqual(vote["name"], "Claudio Javier")
        self.assertEqual(vote["last_name"], "Poggi")
        self.assertEqual(vote["party"], "AVANZAR SAN LUIS")
        self.assertEqual(vote["province"].label, "San Luis")

    def test_get_vote_info_parses_vote_correctly_for_negative_vote(self):
        headers = {
            "Foto": 0,
            "Senador": 1,
            "Bloque": 2,
            "Provincia": 3,
            "¿Cómo votó?": 4,
        }
        vote_date = "30/06/2022"
        vote_type = VoteTypes.GENERAL
        cells_data = """
            <td style="width: 100px;">
              <img alt="Foto de la Senador Nacional no disponible" src="/bundles/senadosenadores/images/fsenaG/noDisponible.png" title="Foto de la Senador Nacional no disponible"/>
            </td>, 
            <td>POGGI, CLAUDIO JAVIER</td>, 
            <td class="ocultar">AVANZAR SAN LUIS</td>, 
            <td class="ocultar">SAN LUIS</td>, 
            <td> 
              <span style="display:none; color=#6cc39f">negativo</span>
              <div style="color:#6cc39f;">NEGATIVO</div>
            </td>
        """
        cells = BeautifulSoup(cells_data, "html.parser").find_all("td")
        vote = SenateVotesSource.get_vote_info(
            vote_date=vote_date, vote_type=vote_type, headers=headers, cells=cells
        )

        self.assertEqual(vote["vote"], VoteChoices.NEGATIVE)
        self.assertEqual(vote["vote_type"], vote_type)
        self.assertEqual(vote["date"], vote_date)
        self.assertEqual(vote["name"], "Claudio Javier")
        self.assertEqual(vote["last_name"], "Poggi")
        self.assertEqual(vote["party"], "AVANZAR SAN LUIS")
        self.assertEqual(vote["province"].label, "San Luis")
