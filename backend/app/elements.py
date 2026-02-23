import re

import pandas as pd
import requests

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

url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"


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


def _get_periodic_table_df():
    from app.firebase import get_periodic_table
    return pd.DataFrame(get_periodic_table())


def get_abMax():
    datas = _get_periodic_table_df().set_index('AtomicNumber')
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
    datas = _get_periodic_table_df().set_index('Symbol')
    datas["elf"] = datas["ElectronConfiguration"].apply(
        lambda x: re.split(r"\d+", x.replace("(predicted)", "").strip())[-2]
    )
    if element:
        return {element: datas.loc[element]["elf"]}
    return datas["elf"].to_dict()


def get_characteristic(element=None):
    datas = _get_periodic_table_df().set_index('Symbol')
    if element:
        return {element: datas.loc[element]["GroupBlock"]}
    return datas["GroupBlock"].to_dict()
