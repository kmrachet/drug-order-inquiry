# 安定版のNode.jsを使用 (軽量なAlpine版)
FROM node:node:24.11.0-alpine

# 作業ディレクトリの設定
WORKDIR /app

# パッケージ定義ファイルを先にコピー (Dockerのキャッシュを効かせるため)
COPY package*.json ./

# 依存パッケージのインストール
RUN npm install

# ソースコードのコピー
COPY . .

# Reactのデフォルトポートを公開
EXPOSE 3000

# 開発サーバーの起動
CMD ["npm", "start"]