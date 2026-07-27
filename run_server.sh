#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home/tgq
exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8443
