FROM node:25.2.1

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