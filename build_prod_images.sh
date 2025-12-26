# 1. イメージのビルド（イメージ名タグを指定してビルドします）
docker build -t drug-order-frontend:latest ./frontend
docker build -t drug-order-backend:latest ./backend

# 2. 外部イメージ（MySQL, Nginx）のプル（念のため最新を取得）
docker pull mysql:8.4
docker pull nginx:1.25

# 3. イメージをtarファイルに保存
# まとめて1つのファイルにするか、個別に分けることができます。ここでは個別にします。
docker save -o frontend.tar drug-order-frontend:latest
docker save -o backend.tar drug-order-backend:latest
docker save -o mysql.tar mysql:8.4
docker save -o nginx.tar nginx:1.25