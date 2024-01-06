import random
import pandas as pd
from faker import Faker

fake = Faker("es_AR")

provinces = ["Buenos Aires", "CABA", "Córdoba", "Mendoza", "Santa Fe"]

parties = [
    "Partido De la Derecha",
    "Propuesta Republicana (PRO)",
    "Unión Cívica Radical (UCR)",
    "Frente de Todos",
    "Coalición Cívica ARI (CC-ARI)",
    "Partido Socialista (PS)",
    "Partido Obrero (PO)",
    "Movimiento Socialista de los Trabajadores (MST)",
    "Nuevo MAS (Movimiento al Socialismo)",
    "Partido de los Trabajadores Socialistas (PTS)",
    "Movimiento Evita",
    "Frente Renovador",
    "Partido Comunista (PC)",
    "Partido de la Victoria",
    "Partido Autonomista Nacional (PAN)",
    "Partido Intransigente (PI)",
    "Partido Conservador Popular",
    "Partido Demócrata Cristiano (PDC)",
    "Acción por la República (AR)",
    "Partido Federal",
    "Frente de Izquierda y de Trabajadores (FIT)",
    "Movimiento Libres del Sur",
    "Partido Humanista (PH)",
    "Partido de la Concertación Forja",
    "Partido Vecinalista",
]


def create_fake_df(df_columns: dict, n=100, as_dict: bool = True, **kwargs):
    if "party_unique" in df_columns.values():
        parties_copy = parties.copy()
        kwargs["parties_copy"] = parties_copy
    column_names = list(df_columns.keys())
    column_types = list(df_columns.values())
    fake_data = {}
    for i in range(n):
        new_record = {}
        for column_name, column_type in zip(column_names, column_types):
            new_value = create_fake_value(column_type, n, **kwargs)
            new_record[column_name] = new_value
        fake_data[i] = new_record
    if as_dict:
        return fake_data
    return pd.DataFrame.from_dict(fake_data, orient="index")


def create_fake_value(column_type: str, n: int, **kwargs):
    if column_type == "name":
        return fake.name()
    elif column_type == "last_name":
        return fake.last_name()
    elif column_type == "full_name":
        return fake.last_name() + " " + fake.name()
    elif column_type == "str":
        return fake.text(max_nb_chars=50)
    if column_type == "province":
        return random.choice(provinces)
    elif column_type == "email":
        return fake.email()
    elif column_type == "phone":
        return fake.phone_number()
    elif column_type == "date":
        if kwargs.get("dates_as_str", True):
            return fake.date_of_birth(minimum_age=18, maximum_age=80)
        return fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%Y-%m-%d")
    elif column_type == "int":
        return fake.random_int(min=1, max=n)
    elif column_type == "party":
        return random.choice(parties)
    elif column_type == "party_unique":
        parties_copy = kwargs.get("parties_copy")
        return parties_copy.pop(0)
    else:
        raise ValueError(f"Column type {column_type} not supported")
