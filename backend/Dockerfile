FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 一個 worker 但用 gevent（issue #28）。
#
# 預設的 sync worker 一次只處理一個請求，`--workers 1` 等於整個網站同時只服務
# 一個人：出現一個慢請求，後面全部排隊。這不是假設——/api/elements/seo 曾經
# 跑 30.3 秒撞上 worker timeout，那段時間整站都沒反應。
#
# 而這個站的請求絕大多數時間是在等 Firebase 回應（每次往返 0.2〜0.3 秒），
# 不是在算東西。gevent 讓那些等待中的請求讓出控制權，一個 process 就能同時
# 服務很多人，記憶體成本遠低於多開 worker（免費方案開多個會 OOM）。
#
# worker-connections 刻意不用建議的 100：回應裡常常夾著 base64 圖片（issue #30），
# 一個請求的峰值可能好幾 MB，併發上限開太大會在 512MB 的免費方案上變成 OOM。
# 這個站的流量用 50 綽綽有餘。
#
# 要知道 gevent 幫不到的地方：浮水印那類 CPU 密集的工作不會讓出控制權，
# 套一張 2048×2048 的圖那半秒鐘還是會擋住其他請求。那是分批處理在解決的問題。
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--worker-class", "gevent", "--workers", "1", "--worker-connections", "50", \
     "run:app"]
