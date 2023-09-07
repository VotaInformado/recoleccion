import random
import pandas as pd
from faker import Faker

fake = Faker()

provinces = ["Buenos Aires", "CABA", "Córdoba", "Mendoza", "Santa Fe"]

def create_fake_df(df_columns: dict, n=100, as_dict: bool = True, **kwargs):
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
    if column_type == "str":
        return fake.name()
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
    else:
        raise ValueError(f"Column type {column_type} not supported")
