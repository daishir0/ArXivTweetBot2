# ArXivTweetBot2

## Overview
ArXivTweetBot2 is an automated system that searches for research papers on arXiv based on specified keywords, downloads them, generates easy-to-understand summaries using OpenAI's GPT models, and posts these summaries to Twitter. It also creates a web interface to browse all the summarized papers, organized by date.

The system is designed to run daily via a cron job, searching for new papers matching your configured keywords, and making cutting-edge research accessible to a broader audience through simplified explanations.

## Installation

### Prerequisites
- Python 3.6 or higher
- Anaconda (recommended for environment management)
- Twitter Developer Account (for posting to Twitter)
- OpenAI API key

### Step by Step Installation

1. Clone the repository:
```bash
git clone https://github.com/daishir0/ArXivTweetBot2.git
cd ArXivTweetBot2
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a configuration file:
```bash
cp config.sample.yaml config.yaml
```

4. Edit the configuration file with your settings:
```bash
nano config.yaml
```

5. Configure the following in your `config.yaml`:
   - OpenAI API key
   - Twitter API credentials
   - Search keywords and settings
   - Output directories for the web interface

## Usage

### Running a Single Search
To search for papers with specific keywords:

```bash
python arxiv_downloader.py "machine learning" "neural networks" --max-results 50
```

### Running Multiple Search Sets
To run multiple predefined search sets from your config file:

```bash
python run_multiple_searches.py
```

### Setting Up Daily Execution
To set up automatic daily execution:

1. Make the script executable:
```bash
chmod +x run_daily.sh
```

2. Add to crontab to run daily (e.g., at 6 AM):
```bash
crontab -e
# Add the following line:
0 6 * * * /path/to/ArXivTweetBot2/run_daily.sh
```

### Generating Web Interface Only
To regenerate the web interface without searching for new papers:

```bash
python web_generator.py --log-dir ./logs --output-dir /var/www/html/arxiv
```

## Notes
- The system creates several directories for organization:
  - `dl/`: Downloaded PDF files
  - `text/`: Extracted text from PDFs
  - `summary/`: Generated summaries
  - `processed/`: Records of processed papers
  - `logs/`: Execution logs

- Twitter posting can be disabled with the `--skip-twitter` flag if you just want to collect and summarize papers.

- The web interface is generated in the specified output directory and can be served by any web server.

- The system uses a character named "C(・ω・ )つ" as a mascot for the Twitter posts and web interface.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# ArXivTweetBot2

## 概要
ArXivTweetBot2は、指定したキーワードに基づいてarXivから研究論文を検索し、ダウンロードして、OpenAIのGPTモデルを使用して理解しやすい要約を生成し、その要約をTwitterに投稿する自動化システムです。また、要約されたすべての論文を日付ごとに整理して閲覧できるWebインターフェースも作成します。

このシステムはcronジョブを通じて毎日実行されるように設計されており、設定されたキーワードに一致する新しい論文を検索し、簡略化された説明を通じて最先端の研究を幅広い層にアクセス可能にします。

## インストール方法

### 前提条件
- Python 3.6以上
- Anaconda（環境管理に推奨）
- Twitterデベロッパーアカウント（Twitterへの投稿用）
- OpenAI APIキー

### Step by stepのインストール方法

1. リポジトリをクローンします：
```bash
git clone https://github.com/daishir0/ArXivTweetBot2.git
cd ArXivTweetBot2
```

2. 必要な依存関係をインストールします：
```bash
pip install -r requirements.txt
```

3. 設定ファイルを作成します：
```bash
cp config.sample.yaml config.yaml
```

4. 設定ファイルを編集して設定を行います：
```bash
nano config.yaml
```

5. `config.yaml`で以下を設定します：
   - OpenAI APIキー
   - Twitter API認証情報
   - 検索キーワードと設定
   - Webインターフェース用の出力ディレクトリ

## 使い方

### 単一検索の実行
特定のキーワードで論文を検索するには：

```bash
python arxiv_downloader.py "機械学習" "ニューラルネットワーク" --max-results 50
```

### 複数の検索セットの実行
設定ファイルから事前定義された複数の検索セットを実行するには：

```bash
python run_multiple_searches.py
```

### 日次実行の設定
自動日次実行を設定するには：

1. スクリプトを実行可能にします：
```bash
chmod +x run_daily.sh
```

2. crontabに追加して毎日実行します（例：午前6時）：
```bash
crontab -e
# 以下の行を追加：
0 6 * * * /path/to/ArXivTweetBot2/run_daily.sh
```

### Webインターフェースのみの生成
新しい論文を検索せずにWebインターフェースを再生成するには：

```bash
python web_generator.py --log-dir ./logs --output-dir /var/www/html/arxiv
```

## 注意点
- システムは整理のために以下のディレクトリを作成します：
  - `dl/`：ダウンロードしたPDFファイル
  - `text/`：PDFから抽出したテキスト
  - `summary/`：生成された要約
  - `processed/`：処理済み論文の記録
  - `logs/`：実行ログ

- Twitter投稿は`--skip-twitter`フラグで無効にできます（論文の収集と要約のみを行いたい場合）。

- Webインターフェースは指定された出力ディレクトリに生成され、任意のWebサーバーで提供できます。

- システムはTwitter投稿とWebインターフェースのマスコットとして「C(・ω・ )つ」というキャラクターを使用しています。

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。