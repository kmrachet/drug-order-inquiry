# drug-order-inquiry

## ディレクトリ構成

```
drug-order-inquiry/
├── backend/                # Flask API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py              # Flaskエントリーポイント
│   ├── parser.py
│   └── dotdict.py
├── frontend/               # React App
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── nginx/                  # Nginx設定
│   └── default.conf
├── db/                     # DB初期化用
│   └── init/               # 初期SQLファイル置き場
└── compose.yaml
```

## 電文の追加

### API
```shell
curl -X POST -H "Content-Type: application/octet-stream" --data-binary @data/test_denbun.txt http://localhost:5050/api/telegrams/receive | jq
```