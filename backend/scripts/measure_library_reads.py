"""量測前台端點各自從 _libraries 讀了多少資料（issue #30 第一步）。

背景：_libraries 一個節點裝著所有圖庫的所有圖片 base64。原本 7 個公開端點
都是 `show_fdb(LIBRARIES_NODE)` 整包讀下來，只為了取出其中一張圖。

這支腳本用假的資料層（8 個圖庫、每個 3 張 200KB 的圖，共 4.58MB）跑真的
Flask 路由，印出每個端點實際讀了多少。改動前全部是 100%。

    docker run --rm -v "$PWD/backend:/app" elementgroups-backend \
        python scripts/measure_library_reads.py

不需要 Firebase 憑證——資料層整個是假的，測的是「讀取範圍」而不是內容。
"""
import sys, os, types, json
ROOT='/app'; sys.path.insert(0, ROOT)
pkg=types.ModuleType('app'); pkg.__path__=[os.path.join(ROOT,'app')]; sys.modules['app']=pkg

BIG = 'x'*200_000                      # 模擬一張 200KB 的 base64 圖
def lib(bt, bid, n=3):
    return {"name":f"{bt}-{bid}","bind_type":bt,"bind_id":bid,"default_image":"i0",
            "images":{f"i{k}":{"name":f"n{k}","img_data":BIG,"order":k} for k in range(n)}}
DB={"_libraries":{}}
for bt,ids in [("group",["1A","2A","7A"]),("particle",["electron","proton"]),
               ("molecule",["water"]),("element",["H","O"])]:
    for i in ids: DB["_libraries"][f"{bt}-{i}"]=lib(bt,i)
DB["_element_groups"]={"1A":{"name":"鹼金屬","description":"d"}}
DB["_particles"]={"electron":{"name":"電子","slug":"electron","published":True,"order":0}}
DB["_molecules"]={"water":{"name":"水","published":True,"formula":"H2O"}}
DB["_pages"]={"p1":{"title":"P","published":True,
    "blocks":[{"type":"image","data":{"image_ref":{"library":"group-1A","image":"i0"}}}]}}
DB["_layers"]={"H":{}}

READ=[0]
def _get(path):
    node=DB
    for part in [p for p in (path or '').split('/') if p]:
        node=node.get(part) if isinstance(node,dict) else None
        if node is None: return None
    return node

fake=types.ModuleType('app.firebase')
def show_fdb(element=None):
    d=_get(element); READ[0]+=len(json.dumps(d)) if d else 0; return d
def show_fdb_where(node, key, value):
    d=_get(node) or {}
    out={k:v for k,v in d.items() if isinstance(v,dict) and v.get(key)==value}
    READ[0]+=len(json.dumps(out)); return out
fake.show_fdb=show_fdb; fake.show_fdb_where=show_fdb_where
fake.get_periodic_table=lambda: []
fake.get_element_by_symbol=lambda s: {"Symbol":s,"Name":"H"}
fake.get_element_by_atomic_number=lambda n: None
fake.get_image_bytes=lambda s:(None,None)
class _N:
    def child(self,*a): return self
    def get(self,*a): return None
    def set(self,*a): return None
fake.fdb=_N(); fake.auth_pyrebase=None
sys.modules['app.firebase']=fake

from flask import Flask
from app.routes.public import public_bp
app=Flask(__name__); app.secret_key='t'
from flask_login import LoginManager
lm=LoginManager(); lm.init_app(app)
@lm.user_loader
def _u(i): return None
app.register_blueprint(public_bp)
c=app.test_client()

TOTAL=len(json.dumps(DB["_libraries"]))
print(f"整包 _libraries = {TOTAL/1024/1024:.2f} MB\n")
print(f"{'端點':32} {'讀取量':>12}  {'佔整包':>7}")
print("-"*56)
for name,url in [("/element-groups","/api/element-groups"),
                 ("/element-groups/1A","/api/element-groups/1A"),
                 ("/particles","/api/particles"),
                 ("/molecules/water","/api/molecules/water"),
                 ("/elements/H/gallery","/api/elements/H/gallery"),
                 ("/elements/H/layers","/api/elements/H/layers"),
                 ("/pages/p1","/api/pages/p1")]:
    READ[0]=0
    r=c.get(url)
    kb=READ[0]/1024
    print(f"{name:32} {kb:9.0f} KB  {READ[0]/TOTAL*100:6.1f}%   [{r.status_code}]")
