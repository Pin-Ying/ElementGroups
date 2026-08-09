"""PubChem 化合物查詢。

與週期表資料同一個來源，不需要引入新的服務。查不到時 PubChem 會回 404，
呼叫端據此切換到手動填寫。

注意：PubChem 已把 `CanonicalSMILES` 更名為 `ConnectivitySMILES`，網路上
找到的舊範例會拿不到值，這裡兩個都收。
"""

import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
PROPERTIES = "MolecularFormula,MolecularWeight,IUPACName,ConnectivitySMILES,CanonicalSMILES"
TIMEOUT = 15


def _extract(item):
    return {
        "cid": item.get("CID"),
        "formula": item.get("MolecularFormula", ""),
        "weight": str(item.get("MolecularWeight", "")),
        "iupac_name": item.get("IUPACName", ""),
        "smiles": item.get("ConnectivitySMILES") or item.get("CanonicalSMILES") or "",
    }


def _query(path):
    """回傳結果清單；查不到回空陣列，其他錯誤往上拋。"""
    url = f"{BASE}/{path}/property/{PROPERTIES}/JSON"
    response = requests.get(url, timeout=TIMEOUT)

    if response.status_code == 404:
        return []
    if response.status_code != 200:
        raise RuntimeError(f"PubChem 回應 {response.status_code}")

    items = (response.json().get("PropertyTable") or {}).get("Properties") or []
    return [_extract(item) for item in items]


def lookup_by_name(name):
    return _query(f"name/{requests.utils.quote(str(name).strip(), safe='')}")


def lookup_by_formula(formula, limit=10):
    """以分子式查詢。fastformula 是同步端點，不需要輪詢 ListKey。"""
    cleaned = str(formula).strip()
    if not cleaned:
        return []
    results = _query(f"fastformula/{requests.utils.quote(cleaned, safe='')}")
    return results[:limit]


def structure_image_url(cid):
    """PubChem 提供現成的 2D 結構圖，沒有自訂圖片時可直接用。"""
    return f"{BASE}/cid/{cid}/PNG" if cid else ""
