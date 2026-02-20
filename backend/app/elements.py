import re

import pandas as pd
import requests

from app.config import settings

url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"

char_groups = [
    "Nonmetal",
    "Alkali metal",
    "Alkaline earth metal",
    "Metalloid",
    "Halogen",
    "Noble gas",
    "Transition metal",
    "Post-transition metal",
    "Lanthanide",
    "Actinide",
]


def _get_db_path():
    uri = settings.DATABASE_URI
    if uri.startswith("sqlite:///"):
        return uri.replace("sqlite:///", "")
    return "elementGroups.db"


def element_info():
    try:
        jsonData = requests.get(url).json()["Table"]
        columns = jsonData["Columns"]["Column"]
        datas = jsonData["Row"]
        elements = []
        for cell in datas:
            cellInfo = cell["Cell"]
            elements.append({col: cellInfo[i] for i, col in enumerate(columns)})
        df = pd.DataFrame(elements)
        return df
    except Exception as e:
        print(f"element_info error, {e}")
        return None


def get_abMax():
    import sqlite3

    con = sqlite3.connect(_get_db_path())
    datas = pd.read_sql_query(
        "SELECT * from PeriodicTable", con=con, index_col=["AtomicNumber"]
    )
    con.close()

    abilities = [
        "MeltingPoint",
        "Electronegativity",
        "AtomicRadius",
        "IonizationEnergy",
        "ElectronAffinity",
        "BoilingPoint",
        "Density",
    ]
    datas = datas[abilities].map(lambda x: eval(x) if x else None)
    abMax = {ability: max(datas[ability]) for ability in abilities}
    return abMax


def get_atomicOrbital(element=None):
    import sqlite3

    con = sqlite3.connect(_get_db_path())
    datas = pd.read_sql_query(
        "SELECT * from PeriodicTable", con=con, index_col=["Symbol"]
    )
    con.close()

    datas["elf"] = datas["ElectronConfiguration"].apply(
        lambda x: re.split(r"\d+", x.replace("(predicted)", "").strip())[-2]
    )
    if element:
        elf = datas.loc[element]["elf"]
        elf = {element: elf}
    else:
        elf = datas["elf"].to_dict()

    return elf


def get_characteristic(element=None):
    import sqlite3

    con = sqlite3.connect(_get_db_path())
    datas = pd.read_sql_query(
        "SELECT * from PeriodicTable", con=con, index_col=["Symbol"]
    )
    con.close()

    if element:
        elf = datas.loc[element]["GroupBlock"]
        elf = {element: elf}
    else:
        elf = datas["GroupBlock"].to_dict()

    return elf
