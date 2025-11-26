# test.ipynb の実行環境に合わせて Python 3.12 を採用
FROM python:3.14

# 作業ディレクトリの設定
WORKDIR /app

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=UTF-8

# システム依存パッケージのインストール (必要に応じて)
# mysqlclientなどを使う場合はgccやdefault-libmysqlclient-devが必要になることがありますが、
# 今回はピュアPythonのドライバ(mysql-connector-python)を想定して最小限にします。
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードのコピー
# (compose.yaml の volumes でマウントされますが、イメージビルド時にも含めておきます)
COPY . .

# Flaskのデフォルトポートを公開
EXPOSE 5000

# 起動コマンド (compose.yaml で上書きしない場合のデフォルト)
CMD ["flask", "run", "--host=0.0.0.0"]