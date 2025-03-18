# ArXivTweetBot2

## Overview

![screen shot](image.png)

ArXivTweetBot2 is an automated system that searches for research papers on arXiv based on specified keywords, downloads them, generates easy-to-understand summaries using OpenAI's GPT models, and posts these summaries to Twitter. It also creates a web interface to browse all the summarized papers, organized by date.

The system is designed to run daily via a cron job, searching for new papers matching your configured keywords, and making cutting-edge research accessible to a broader audience through simplified explanations.

## System Architecture

ArXivTweetBot2 consists of several components that work together to automate the process of finding, summarizing, and sharing research papers:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  run_daily.sh   │────▶│run_multiple_    │────▶│arxiv_downloader.│
│  (Main script)  │     │searches.py      │     │py               │
└─────────────────┘     │(Search manager) │     │(Paper processor)│
        │               └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       ▼
        │                       │               ┌─────────────────┐
        │                       │               │  OpenAI API     │
        │                       │               │  (Summarization)│
        │                       │               └─────────────────┘
        │                       │                       │
        │                       ▼                       ▼
        │               ┌─────────────────┐     ┌─────────────────┐
        └──────────────▶│twitter_log_     │     │  Twitter API    │
                        │analyzer.py      │     │  (Posting)      │
                        │(Analytics)      │     └─────────────────┘
                        └─────────────────┘             │
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Summary        │     │  web_generator. │
                        │  Reports        │     │  py             │
                        └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  Web Interface  │
                                                │  (HTML/CSS/JS)  │
                                                └─────────────────┘
```

### Data Flow

1. `run_daily.sh` is triggered by a cron job and sets up the environment
2. `run_multiple_searches.py` reads the configuration and manages multiple search sets
3. `arxiv_downloader.py` searches arXiv, downloads papers, generates summaries, and posts to Twitter
4. `web_generator.py` creates HTML pages to browse the papers
5. `twitter_log_analyzer.py` analyzes posting logs and generates reports

## Core Components

### arxiv_downloader.py

This is the main workhorse of the system that:

- Searches arXiv API for papers matching specified keywords
- Downloads PDF files of matching papers
- Extracts text from PDFs
- Generates summaries using OpenAI's GPT models
- Posts summaries to Twitter
- Logs all activities and results

**Key Features:**
- Filtering by date and already processed papers
- Customizable summary templates
- Rate limiting for API calls
- Error handling and retry logic
- Detailed logging

**Usage Example:**
```bash
python arxiv_downloader.py "quantum computing" "machine learning" --max-results 20 --since-timestamp "2023-01-01T00:00:00Z"
```

### run_multiple_searches.py

This script manages the execution of multiple search sets defined in the configuration file:

- Reads search sets from config.yaml
- Executes each search set with appropriate parameters
- Manages timestamps to avoid reprocessing papers
- Tracks processed paper IDs across search sets
- Triggers web interface generation

**Key Features:**
- Sequential processing of search sets with configurable delays
- Timestamp-based filtering to only process new papers
- Shared tracking of processed papers across search sets
- Detailed logging of each search set's execution

**Usage Example:**
```bash
python run_multiple_searches.py --all-pages --verbose
```

### web_generator.py

Creates a browsable web interface for all processed papers:

- Generates HTML pages organized by date
- Creates index pages with filtering capabilities
- Includes paper summaries, links to original papers, and Twitter posts
- Supports customizable templates and styling

**Key Features:**
- Responsive design for mobile and desktop viewing
- Search and filter functionality
- Customizable templates
- Support for generating current day only or all historical pages

**Usage Example:**
```bash
python web_generator.py --log-dir ./logs --output-dir /var/www/html/arxiv --template-dir ./templates
```

### twitter_log_analyzer.py

Analyzes Twitter posting logs to generate statistics and reports:

- Processes JSON log files of Twitter posts
- Generates daily and overall posting statistics
- Creates markdown reports and CSV data exports
- Tracks successful and failed posts

**Key Features:**
- Daily posting counts and trends
- Success/failure analysis
- Exportable data in multiple formats
- Customizable report templates

**Usage Example:**
```bash
python twitter_log_analyzer.py --output summary.md --csv data.csv
```

### run_daily.sh

The main shell script that orchestrates the daily execution:

- Sets up the Anaconda environment
- Manages command-line options for execution modes
- Executes the Python scripts in the correct sequence
- Logs all execution steps and results
- Handles errors and reports issues

**Key Features:**
- Support for different execution modes (current day only, all pages, verbose)
- Comprehensive logging
- Environment setup and validation
- Error handling and reporting

**Usage Example:**
```bash
./run_daily.sh --all-pages --verbose
```

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

## Configuration File Details

The `config.yaml` file is the central configuration for the system. Here's a detailed explanation of its structure:

```yaml
# API Keys and Authentication
api:
  openai:
    api_key: "your-openai-api-key"
  twitter:
    consumer_key: "your-twitter-consumer-key"
    consumer_secret: "your-twitter-consumer-secret"
    access_token: "your-twitter-access-token"
    access_token_secret: "your-twitter-access-token-secret"

# Execution Settings
execution:
  wait_between_sets: 30  # Seconds to wait between search sets
  current_only: true     # Generate only current day's pages by default

# Search Sets
search_sets:
  - name: "Machine Learning"
    keywords: ["machine learning", "deep learning", "neural network"]
    output_dir: "/var/www/html/llm_rag"
    max_results: 50
    tweet_enabled: true
    
  - name: "Quantum Computing"
    keywords: ["quantum computing", "quantum algorithm"]
    output_dir: "/var/www/html/quantum"
    max_results: 30
    tweet_enabled: true

# Summary Settings
summary:
  model: "gpt-4"          # OpenAI model to use
  temperature: 0.7        # Creativity level (0.0-1.0)
  max_tokens: 500         # Maximum tokens in summary
  language: "en"          # Summary language (en, ja, etc.)
  
# Web Interface Settings
web:
  title: "ArXiv Research Summaries"
  description: "Daily summaries of the latest research papers"
  theme: "light"          # light or dark
  items_per_page: 20
```

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

## Advanced Usage Examples

### Specialized Research Field Configuration

For AI Safety research:

```yaml
search_sets:
  - name: "AI Safety"
    keywords: ["AI safety", "AI alignment", "AI ethics", "AI governance"]
    output_dir: "/var/www/html/ai_safety"
    max_results: 100
    tweet_enabled: true
    custom_prompt: "Summarize this AI safety paper with focus on practical implications and potential risks."
```

### Custom Summary Templates

You can customize the summary templates in the configuration:

```yaml
summary_templates:
  default: |
    Title: {title}
    Authors: {authors}
    
    TL;DR: {tldr}
    
    Key points:
    {bullet_points}
    
    #arXiv #Research #AI
  
  technical: |
    📑 {title}
    👩‍🔬 {authors}
    
    💡 Summary: {tldr}
    
    🔑 Technical details:
    {technical_details}
    
    🔗 {url}
    #arXiv #TechResearch
```

## Troubleshooting

### Common Issues

#### Python Version Errors

If you see syntax errors like:
```
SyntaxError: invalid syntax
```
with f-strings, ensure you're using Python 3.6+. In cron jobs, explicitly specify the Python path:

```bash
# In run_daily.sh
PYTHON_CMD="python3"  # Instead of just "python"
```

#### API Rate Limiting

If you encounter rate limiting:
```
Error: Rate limit exceeded for OpenAI API
```

Solution: Adjust the execution settings to add delays between requests:
```yaml
execution:
  api_request_delay: 5  # Seconds between API calls
```

#### PDF Processing Errors

If PDF text extraction fails:
```
Error processing PDF: Unable to extract text
```

Solution: Install additional dependencies:
```bash
apt-get install poppler-utils
pip install pdfminer.six
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

## システムアーキテクチャ

ArXivTweetBot2は、研究論文の検索、要約、共有のプロセスを自動化するために連携して動作するいくつかのコンポーネントで構成されています：

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  run_daily.sh   │────▶│run_multiple_    │────▶│arxiv_downloader.│
│  (メインスクリプト)  │     │searches.py      │     │py               │
└─────────────────┘     │(検索マネージャー)   │     │(論文プロセッサー)  │
        │               └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       ▼
        │                       │               ┌─────────────────┐
        │                       │               │  OpenAI API     │
        │                       │               │  (要約生成)      │
        │                       │               └─────────────────┘
        │                       ▼                       ▼
        │               ┌─────────────────┐     ┌─────────────────┐
        └──────────────▶│twitter_log_     │     │  Twitter API    │
                        │analyzer.py      │     │  (投稿)         │
                        │(分析)           │     └─────────────────┘
                        └─────────────────┘             │
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  サマリー        │     │  web_generator. │
                        │  レポート        │     │  py             │
                        └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  Webインターフェース │
                                                │  (HTML/CSS/JS)  │
                                                └─────────────────┘
```

### データフロー

1. `run_daily.sh`はcronジョブによってトリガーされ、環境をセットアップします
2. `run_multiple_searches.py`は設定を読み込み、複数の検索セットを管理します
3. `arxiv_downloader.py`はarXivを検索し、論文をダウンロードし、要約を生成し、Twitterに投稿します
4. `web_generator.py`は論文を閲覧するためのHTMLページを作成します
5. `twitter_log_analyzer.py`は投稿ログを分析し、レポートを生成します

## 主要コンポーネント

### arxiv_downloader.py

このシステムの主要な作業を行うスクリプトで、以下の機能があります：

- 指定されたキーワードに一致する論文をarXiv APIで検索
- 一致する論文のPDFファイルをダウンロード
- PDFからテキストを抽出
- OpenAIのGPTモデルを使用して要約を生成
- 要約をTwitterに投稿
- すべての活動と結果をログに記録

**主な機能：**
- 日付と既に処理済みの論文によるフィルタリング
- カスタマイズ可能な要約テンプレート
- APIコールのレート制限
- エラー処理とリトライロジック
- 詳細なログ記録

**使用例：**
```bash
python arxiv_downloader.py "量子コンピューティング" "機械学習" --max-results 20 --since-timestamp "2023-01-01T00:00:00Z"
```

### run_multiple_searches.py

このスクリプトは設定ファイルで定義された複数の検索セットの実行を管理します：

- config.yamlから検索セットを読み込み
- 適切なパラメータで各検索セットを実行
- 論文の再処理を避けるためのタイムスタンプを管理
- 検索セット間で処理済み論文IDを追跡
- Webインターフェース生成をトリガー

**主な機能：**
- 設定可能な遅延を持つ検索セットの順次処理
- 新しい論文のみを処理するためのタイムスタンプベースのフィルタリング
- 検索セット間での処理済み論文の共有追跡
- 各検索セットの実行の詳細なログ記録

**使用例：**
```bash
python run_multiple_searches.py --all-pages --verbose
```

### web_generator.py

処理されたすべての論文のブラウズ可能なWebインターフェースを作成します：

- 日付ごとに整理されたHTMLページを生成
- フィルタリング機能を持つインデックスページを作成
- 論文の要約、元の論文へのリンク、Twitterの投稿を含む
- カスタマイズ可能なテンプレートとスタイリングをサポート

**主な機能：**
- モバイルとデスクトップ表示のためのレスポンシブデザイン
- 検索とフィルタリング機能
- カスタマイズ可能なテンプレート
- 現在の日付のみまたはすべての履歴ページの生成のサポート

**使用例：**
```bash
python web_generator.py --log-dir ./logs --output-dir /var/www/html/arxiv --template-dir ./templates
```

### twitter_log_analyzer.py

Twitter投稿ログを分析して統計とレポートを生成します：

- Twitter投稿のJSONログファイルを処理
- 日次および全体の投稿統計を生成
- マークダウンレポートとCSVデータエクスポートを作成
- 成功した投稿と失敗した投稿を追跡

**主な機能：**
- 日次投稿数とトレンド
- 成功/失敗分析
- 複数のフォーマットでエクスポート可能なデータ
- カスタマイズ可能なレポートテンプレート

**使用例：**
```bash
python twitter_log_analyzer.py --output summary.md --csv data.csv
```

### run_daily.sh

日次実行を調整するメインシェルスクリプト：

- Anaconda環境をセットアップ
- 実行モードのコマンドラインオプションを管理
- 正しい順序でPythonスクリプトを実行
- すべての実行ステップと結果をログに記録
- エラーを処理し、問題を報告

**主な機能：**
- 異なる実行モードのサポート（現在の日のみ、すべてのページ、詳細モード）
- 包括的なログ記録
- 環境のセットアップと検証
- エラー処理と報告

**使用例：**
```bash
./run_daily.sh --all-pages --verbose
```

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

## 設定ファイルの詳細

`config.yaml`ファイルはシステムの中心的な設定です。以下はその構造の詳細な説明です：

```yaml
# APIキーと認証
api:
  openai:
    api_key: "あなたのOpenAI-APIキー"
  twitter:
    consumer_key: "あなたのTwitterコンシューマーキー"
    consumer_secret: "あなたのTwitterコンシューマーシークレット"
    access_token: "あなたのTwitterアクセストークン"
    access_token_secret: "あなたのTwitterアクセストークンシークレット"

# 実行設定
execution:
  wait_between_sets: 30  # 検索セット間の待機秒数
  current_only: true     # デフォルトでは現在の日のページのみを生成

# 検索セット
search_sets:
  - name: "機械学習"
    keywords: ["機械学習", "深層学習", "ニューラルネットワーク"]
    output_dir: "/var/www/html/llm_rag"
    max_results: 50
    tweet_enabled: true
    
  - name: "量子コンピューティング"
    keywords: ["量子コンピューティング", "量子アルゴリズム"]
    output_dir: "/var/www/html/quantum"
    max_results: 30
    tweet_enabled: true

# 要約設定
summary:
  model: "gpt-4"          # 使用するOpenAIモデル
  temperature: 0.7        # 創造性レベル（0.0-1.0）
  max_tokens: 500         # 要約の最大トークン数
  language: "ja"          # 要約言語（en、ja、など）
  
# Webインターフェース設定
web:
  title: "arXiv研究要約"
  description: "最新の研究論文の日次要約"
  theme: "light"          # lightまたはdark
  items_per_page: 20
```

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

## 高度な使用例

### 専門研究分野の設定

AI安全性研究の場合：

```yaml
search_sets:
  - name: "AI安全性"
    keywords: ["AI安全性", "AIアライメント", "AI倫理", "AIガバナンス"]
    output_dir: "/var/www/html/ai_safety"
    max_results: 100
    tweet_enabled: true
    custom_prompt: "この AI 安全性論文を要約し、実用的な意味と潜在的なリスクに焦点を当ててください。"
```

### カスタム要約テンプレート

設定で要約テンプレートをカスタマイズできます：

```yaml
summary_templates:
  default: |
    タイトル: {title}
    著者: {authors}
    
    要約: {tldr}
    
    ポイント:
    {bullet_points}
    
    #arXiv #研究 #AI
  
  technical: |
    📑 {title}
    👩‍🔬 {authors}
    
    💡 要約: {tldr}
    
    🔑 技術的詳細:
    {technical_details}
    
    🔗 {url}
    #arXiv #技術研究
```

## トラブルシューティング

### 一般的な問題

#### Pythonバージョンエラー

次のような構文エラーが表示される場合：
```
SyntaxError: invalid syntax
```
f-stringを使用している場合は、Python 3.6以上を使用していることを確認してください。cronジョブでは、Pythonパスを明示的に指定します：

```bash
# run_daily.shで
PYTHON_CMD="python3"  # "python"だけではなく
```

#### APIレート制限

レート制限に遭遇した場合：
```
Error: Rate limit exceeded for OpenAI API
```

解決策：リクエスト間に遅延を追加するように実行設定を調整します：
```yaml
execution:
  api_request_delay: 5  # APIコール間の秒数
```

#### PDF処理エラー

PDFテキスト抽出が失敗した場合：
```
Error processing PDF: Unable to extract text
```

解決策：追加の依存関係をインストールします：
```bash
apt-get install poppler-utils
pip install pdfminer.six
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