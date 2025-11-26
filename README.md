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