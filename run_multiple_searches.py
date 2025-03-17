#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import time
import subprocess
import logging
import shutil
import json
from datetime import datetime

def load_config():
    """設定ファイルを読み込む"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"設定ファイルの読み込みエラー: {str(e)}")
        return None

def generate_pdf_dir_name(keywords):
    """キーワードからPDFディレクトリ名を生成する"""
    if keywords:
        dir_name = '_'.join(keywords)
        return f"./pdf/{dir_name}"
    return f"./pdf/search_{int(time.time())}"

def setup_pdf_directory(keywords):
    """PDFディレクトリを設定する"""
    pdf_dir = generate_pdf_dir_name(keywords)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # シンボリックリンクを作成（既存のdlディレクトリをPDFディレクトリにリンク）
    dl_dir = "./dl"
    if os.path.exists(dl_dir):
        if os.path.islink(dl_dir):
            os.unlink(dl_dir)
        else:
            shutil.rmtree(dl_dir)
    
    os.symlink(pdf_dir, dl_dir)
    logging.info(f"PDFディレクトリを設定: {pdf_dir}")
    
    return pdf_dir

def get_timestamp_file_path():
    """タイムスタンプファイルのパスを取得する"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_run_timestamp.json")

def load_timestamps():
    """前回の実行タイムスタンプを読み込む"""
    timestamp_file = get_timestamp_file_path()
    if os.path.exists(timestamp_file):
        try:
            with open(timestamp_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"タイムスタンプファイルの読み込みエラー: {str(e)}")
    return {}

def save_timestamps(timestamps):
    """実行タイムスタンプを保存する"""
    timestamp_file = get_timestamp_file_path()
    try:
        with open(timestamp_file, 'w') as f:
            json.dump(timestamps, f, indent=2)
    except Exception as e:
        logging.error(f"タイムスタンプファイルの保存エラー: {str(e)}")

def get_processed_ids_file_path():
    """処理済み論文IDファイルのパスを取得する"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_paper_ids.txt")

def load_processed_ids():
    """処理済み論文IDを読み込む"""
    processed_ids_file = get_processed_ids_file_path()
    processed_ids = set()
    if os.path.exists(processed_ids_file):
        try:
            with open(processed_ids_file, 'r') as f:
                processed_ids = set(f.read().splitlines())
            logging.info(f"{len(processed_ids)}件の処理済み論文IDを読み込みました。")
        except Exception as e:
            logging.error(f"処理済み論文IDファイルの読み込みエラー: {str(e)}")
    return processed_ids

def save_processed_ids(processed_ids):
    """処理済み論文IDを保存する"""
    processed_ids_file = get_processed_ids_file_path()
    try:
        with open(processed_ids_file, 'w') as f:
            f.write('\n'.join(processed_ids))
        logging.info(f"{len(processed_ids)}件の処理済み論文IDを保存しました。")
    except Exception as e:
        logging.error(f"処理済み論文IDファイルの保存エラー: {str(e)}")

def run_search_set(keywords, output_dir, max_results=100, tweet_enabled=True, timestamps=None, processed_ids=None, search_set_id=None):
    """検索セットを実行する"""
    # PDFディレクトリを設定
    pdf_dir = setup_pdf_directory(keywords)
    
    # 検索セット専用のログディレクトリを作成
    # キーワードからログディレクトリ名を生成（特殊文字を除去）
    import re
    # 特殊文字を除去し、英数字とアンダースコアのみにする
    safe_keywords = [re.sub(r'[^a-zA-Z0-9]', '_', kw) for kw in keywords]
    keywords_str = '_'.join(safe_keywords)
    log_dir = f"./logs/{keywords_str}"
    os.makedirs(log_dir, exist_ok=True)
    
    # 検索キーワードを文字列に変換
    keywords_str = ' '.join(keywords)
    
    # 前回の実行タイムスタンプを取得
    since_timestamp = None
    last_paper_id = None
    if timestamps and search_set_id in timestamps:
        since_timestamp = timestamps[search_set_id].get('timestamp')
        last_paper_id = timestamps[search_set_id].get('last_paper_id')
    
    # 現在のタイムスタンプを記録
    current_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # 処理済み論文IDを一時ファイルに保存
    processed_ids_file = None
    if processed_ids:
        processed_ids_file = f"./temp_processed_ids_{search_set_id}.txt"
        with open(processed_ids_file, 'w') as f:
            f.write('\n'.join(processed_ids))
    
    # 新しく処理した論文IDを保存するファイル
    new_processed_ids_file = f"./new_processed_ids_{search_set_id}.txt"
    
    # arxiv_downloader.pyを実行
    cmd = [
        'python3', 'arxiv_downloader.py',
        *keywords,  # キーワードを展開
        '--max-results', str(max_results),
        '--max-process', '9999',  # 実質無制限
        '--log-dir', log_dir  # ログディレクトリを指定
    ]
    
    # 詳細モードの場合は--verboseオプションを追加
    if config.get('verbose', False):
        cmd.append('--verbose')
    
    # タイムスタンプフィルタを追加
    if since_timestamp:
        cmd.extend(['--since-timestamp', since_timestamp])
        logging.info(f"タイムスタンプフィルタを適用: {since_timestamp} 以降")
    
    # 最後の論文IDフィルタを追加
    if last_paper_id:
        cmd.extend(['--last-paper-id', last_paper_id])
        logging.info(f"論文IDフィルタを適用: {last_paper_id} 以降")
    
    # 処理済み論文IDを渡す
    if processed_ids_file:
        cmd.extend(['--processed-ids-file', processed_ids_file])
    
    # 処理した論文IDを出力するファイルを指定
    cmd.extend(['--output-processed-ids', new_processed_ids_file])
    
    # Twitter投稿が無効の場合、オプションを追加
    if not tweet_enabled:
        cmd.append('--skip-twitter')
    
    logging.info(f"検索実行: {keywords_str}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 一時ファイルを削除
    if processed_ids_file and os.path.exists(processed_ids_file):
        os.remove(processed_ids_file)
    
    if result.returncode != 0:
        logging.error(f"arxiv_downloaderの実行エラー: {result.stderr}")
        return False, set()
    
    logging.info(result.stdout)
    
    # 新しく処理した論文IDを読み込む
    new_processed_ids = set()
    if os.path.exists(new_processed_ids_file):
        with open(new_processed_ids_file, 'r') as f:
            new_processed_ids = set(f.read().splitlines())
        os.remove(new_processed_ids_file)
    
    # タイムスタンプを更新
    if timestamps is not None and search_set_id is not None:
        timestamps[search_set_id] = {
            'timestamp': current_timestamp,
            'last_paper_id': None  # 最後の論文IDは現在未実装
        }
    
    # web_generator.pyを実行
    web_cmd = [
        'python3', 'web_generator.py',
        '--log-dir', log_dir,  # ログディレクトリを指定
        '--output-dir', output_dir
    ]
    
    # 現在の日付のページのみを生成するかどうか
    if config.get('current_only', True):
        web_cmd.append('--current-only')
        logging.info(f"Webページ生成（現在の日付のみ）: {output_dir}")
    else:
        logging.info(f"Webページ生成（全ての日付）: {output_dir}")
    
    web_result = subprocess.run(web_cmd, capture_output=True, text=True)
    
    if web_result.returncode != 0:
        logging.error(f"web_generatorの実行エラー: {web_result.stderr}")
        return False, new_processed_ids
    
    logging.info(web_result.stdout)
    logging.info(f"検索セット完了: {keywords_str}")
    return True, new_processed_ids

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    import argparse
    parser = argparse.ArgumentParser(description='複数の検索セットを実行します。')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--current-only', action='store_true', help='現在の日付のページのみを生成します（デフォルト）')
    group.add_argument('--all-pages', action='store_true', help='全ての日付のページを生成します')
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示します')
    args = parser.parse_args()
    
    # ロギングを設定
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # ログレベルを設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # ログフォーマットを設定
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # ログハンドラーを設定
    handlers = [
        logging.FileHandler(os.path.join(log_dir, f"multiple_searches_{time.strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
    
    # ロギングを設定
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    if args.verbose:
        logging.info("詳細モードで実行します")
    
    # 設定を読み込む
    global config
    config = load_config()
    if not config:
        logging.error("設定ファイルの読み込みに失敗しました。")
        return
    # コマンドライン引数から現在の日付のページのみを生成するかどうかを設定
    if args.all_pages:
        config['current_only'] = False
    else:
        config['current_only'] = True
    
    # 詳細モードの設定
    config['verbose'] = args.verbose
    
    # 前回の実行タイムスタンプを読み込む
    timestamps = load_timestamps()
    
    # 処理済み論文IDを読み込む
    processed_ids = load_processed_ids()
    
    # 検索セットを取得
    search_sets = config.get('search_sets', [])
    if not search_sets:
        logging.error("検索セットが定義されていません。")
        return
    
    # 待機時間を取得
    wait_time = config.get('execution', {}).get('wait_between_sets', 10)
    
    # 新しく処理した論文IDを追跡
    all_new_processed_ids = set()
    
    # 各検索セットを実行
    for i, search_set in enumerate(search_sets):
        keywords = search_set.get('keywords', [])
        output_dir = search_set.get('output_dir', '')
        max_results = search_set.get('max_results', 100)  # デフォルト: 100
        tweet_enabled = search_set.get('tweet_enabled', True)  # デフォルト: True
        
        if not keywords or not output_dir:
            logging.warning(f"検索セット {i+1} はキーワードまたは出力先ディレクトリが定義されていません。スキップします。")
            continue
        
        # 検索セットのIDを生成
        search_set_id = '_'.join(keywords)
        
        logging.info(f"検索セット {i+1}/{len(search_sets)} を開始: {' '.join(keywords)}")
        logging.info(f"  最大検索結果数: {max_results}, Twitter投稿: {'有効' if tweet_enabled else '無効'}")
        
        try:
            success, new_processed_ids = run_search_set(
                keywords, 
                output_dir, 
                max_results, 
                tweet_enabled,
                timestamps,
                processed_ids,
                search_set_id
            )
            
            # 処理済み論文IDを更新
            all_new_processed_ids.update(new_processed_ids)
            
            if not success:
                logging.warning(f"検索セット {i+1} の実行が失敗しました。次のセットに進みます。")
        except Exception as e:
            logging.error(f"検索セット {i+1} の実行中にエラーが発生しました: {str(e)}")
        
        # 最後のセット以外は待機
        if i < len(search_sets) - 1:
            logging.info(f"{wait_time}秒待機中...")
            time.sleep(wait_time)
    
    # 処理済み論文IDを更新して保存
    processed_ids.update(all_new_processed_ids)
    save_processed_ids(processed_ids)
    
    # タイムスタンプを保存
    save_timestamps(timestamps)
    
    logging.info(f"すべての検索セットの実行が完了しました。{len(all_new_processed_ids)}件の新しい論文を処理しました。")

if __name__ == "__main__":
    main()