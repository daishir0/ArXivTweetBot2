#!/bin/bash

# 日次実行スクリプト
# cronで毎日特定の時間に実行するためのスクリプト

# デフォルト設定
CURRENT_ONLY=true  # デフォルトでは本日分のみ生成
VERBOSE=false      # デフォルトでは詳細モードは無効

# コマンドラインオプションの解析
while [[ $# -gt 0 ]]; do
  case $1 in
    --all-pages)
      CURRENT_ONLY=false
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "使用方法: $0 [オプション]"
      echo "オプション:"
      echo "  --all-pages    全ての日付のページを生成します"
      echo "  --verbose      詳細な出力を表示します"
      echo "  --help         このヘルプメッセージを表示します"
      exit 0
      ;;
    *)
      echo "不明なオプション: $1"
      echo "ヘルプを表示するには: $0 --help"
      exit 1
      ;;
  esac
done

# Anaconda環境の設定
# Anacondaのパスを設定（必要に応じて変更）
CONDA_PATH="/home/ec2-user/anaconda3"
CONDA_PROFILE="$CONDA_PATH/etc/profile.d/conda.sh"

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 日付を取得
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M:%S")

# スクリプトの絶対パスを取得
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ログディレクトリ（絶対パス）
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 実行ログファイル
EXEC_LOG="$LOG_DIR/execution_$DATE.log"

# 開始メッセージ
echo "===== ArXivTweetBot 日次実行 =====" | tee -a "$EXEC_LOG"
echo "日時: $DATE $TIME" | tee -a "$EXEC_LOG"
echo "" | tee -a "$EXEC_LOG"

# Anaconda環境を有効化
echo "Anaconda環境を有効化中..." | tee -a "$EXEC_LOG"
if [ -f "$CONDA_PROFILE" ]; then
    # conda.shが存在する場合はそれを使用
    source "$CONDA_PROFILE"
    conda activate base 2>&1 | tee -a "$EXEC_LOG"
    PYTHON_CMD="python"
    echo "Anaconda環境を有効化しました。" | tee -a "$EXEC_LOG"
else
    # conda.shが見つからない場合は直接パスを指定
    PYTHON_CMD="$CONDA_PATH/bin/python"
    echo "conda.shが見つかりません。直接Pythonパスを使用します: $PYTHON_CMD" | tee -a "$EXEC_LOG"
fi

# Pythonバージョンを確認
echo "Pythonバージョン:" | tee -a "$EXEC_LOG"
$PYTHON_CMD --version 2>&1 | tee -a "$EXEC_LOG"
echo "" | tee -a "$EXEC_LOG"

# 複数の検索セットを実行
echo "複数の検索セットを実行中..." | tee -a "$EXEC_LOG"
if [ "$CURRENT_ONLY" = true ]; then
  echo "本日分のページのみを生成します..." | tee -a "$EXEC_LOG"
  if [ "$VERBOSE" = true ]; then
    echo "詳細モードで実行します..." | tee -a "$EXEC_LOG"
    $PYTHON_CMD "$SCRIPT_DIR/run_multiple_searches.py" --current-only --verbose 2>&1 | tee -a "$EXEC_LOG"
  else
    $PYTHON_CMD "$SCRIPT_DIR/run_multiple_searches.py" --current-only 2>&1 | tee -a "$EXEC_LOG"
  fi
else
  echo "全ての日付のページを生成します..." | tee -a "$EXEC_LOG"
  if [ "$VERBOSE" = true ]; then
    echo "詳細モードで実行します..." | tee -a "$EXEC_LOG"
    $PYTHON_CMD "$SCRIPT_DIR/run_multiple_searches.py" --all-pages --verbose 2>&1 | tee -a "$EXEC_LOG"
  else
    $PYTHON_CMD "$SCRIPT_DIR/run_multiple_searches.py" --all-pages 2>&1 | tee -a "$EXEC_LOG"
  fi
fi

# 実行結果のサマリーを生成
echo "" | tee -a "$EXEC_LOG"
echo "Twitter投稿ログの分析中..." | tee -a "$EXEC_LOG"
$PYTHON_CMD "$SCRIPT_DIR/twitter_log_analyzer.py" --output "$LOG_DIR/twitter_summary_$DATE.md" --csv "$LOG_DIR/twitter_posts_$DATE.csv" 2>&1 | tee -a "$EXEC_LOG"

# 完了メッセージ
echo "" | tee -a "$EXEC_LOG"
echo "処理が完了しました。" | tee -a "$EXEC_LOG"
echo "サマリー: $LOG_DIR/twitter_summary_$DATE.md" | tee -a "$EXEC_LOG"
echo "CSVデータ: $LOG_DIR/twitter_posts_$DATE.csv" | tee -a "$EXEC_LOG"
echo "Webページ:" | tee -a "$EXEC_LOG"
echo "  - /var/www/html/llm_rag/index.html" | tee -a "$EXEC_LOG"
echo "  - /var/www/html/2050/index.html" | tee -a "$EXEC_LOG"
echo "===== 終了 =====" | tee -a "$EXEC_LOG"