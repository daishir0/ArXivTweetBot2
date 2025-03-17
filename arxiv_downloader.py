#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import arxiv
import requests
import os
import sys
import time
import argparse
import yaml
import logging
import json
import tweepy
import glob
import shutil
from pathlib import Path
from urllib.parse import urlparse
from openai import OpenAI

# 追加モジュールをインポート
from pdf_processor import extract_text_from_pdf
from ai_summarizer import generate_summary
from twitter_poster import post_thread

def load_config():
    """
    設定ファイルを読み込む
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_directories():
    """
    必要なディレクトリを作成
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = {
        'dl': os.path.join(base_dir, 'dl'),
        'text': os.path.join(base_dir, 'text'),
        'summary': os.path.join(base_dir, 'summary'),
        'processed': os.path.join(base_dir, 'processed'),
        'logs': os.path.join(base_dir, 'logs')
    }
    
    for dir_name, dir_path in dirs.items():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs

def setup_logging(log_dir, verbose=False):
    """
    ロギングを設定
    
    Args:
        log_dir (str): ログディレクトリのパス
        verbose (bool): 詳細モードかどうか
    """
    log_file = os.path.join(log_dir, f"arxiv_downloader_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
    # ログレベルを設定
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # ログフォーマットを設定
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # ログハンドラーを設定
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    
    # ロギングを設定
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    if verbose:
        logging.info("詳細モードで実行します")

def is_processed(arxiv_id, processed_dir, processed_ids=None):
    """
    論文が既に処理済みかどうかを確認
    
    Args:
        arxiv_id (str): 論文のarXiv ID
        processed_dir (str): 処理済みファイルのディレクトリ
        processed_ids (set, optional): 処理済み論文IDのセット
        
    Returns:
        bool: 処理済みかどうか
    """
    # 処理済みIDリストに含まれているかチェック
    if processed_ids and arxiv_id in processed_ids:
        return True
        
    # 処理済みファイルが存在するかチェック
    processed_file = os.path.join(processed_dir, f"{arxiv_id}.json")
    return os.path.exists(processed_file)

def mark_as_processed(arxiv_id, paper_title, processed_dir):
    """
    論文を処理済みとしてマーク
    """
    processed_file = os.path.join(processed_dir, f"{arxiv_id}.json")
    data = {
        "arxiv_id": arxiv_id,
        "title": paper_title,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_arxiv_id(paper):
    """
    論文オブジェクトからarXiv IDを抽出
    
    Args:
        paper (arxiv.Result): 論文情報
        
    Returns:
        str: arXiv ID
    """
    pdf_url = paper.pdf_url
    parsed_url = urlparse(pdf_url)
    path_parts = parsed_url.path.split('/')
    arxiv_id = path_parts[-1]
    if arxiv_id.endswith('.pdf'):
        arxiv_id = arxiv_id[:-4]
    return arxiv_id

def search_arxiv(keywords, max_results=100, use_or=False, since_timestamp=None, last_paper_id=None):
    """
    arXivで指定されたキーワードを使用して論文を検索します。
    
    Args:
        keywords (list): 検索キーワードのリスト
        max_results (int): 取得する最大論文数
        use_or (bool): キーワードをORで結合するかどうか
        since_timestamp (str, optional): 指定したタイムスタンプ以降の論文のみを検索
        last_paper_id (str, optional): 指定したID以降の論文のみを検索
    
    Returns:
        list: 検索結果の論文リスト
    """
    logging.info(f"キーワード '{' '.join(keywords)}' でarXivを検索中...")
    
    # 検索クエリを作成
    if use_or:
        query = ' OR '.join(keywords)
    else:
        query = ' AND '.join(keywords)
    
    # タイムスタンプフィルタを追加
    if since_timestamp:
        date_filter = f" AND submittedDate:[{since_timestamp} TO *]"
        query += date_filter
        logging.info(f"タイムスタンプフィルタを適用: {since_timestamp} 以降")
    
    # arXivクライアントを作成
    client = arxiv.Client(
        page_size=10,  # 一度に取得する論文数を制限
        delay_seconds=3.0,  # リクエスト間の待機時間を3秒に設定
        num_retries=3  # リトライ回数
    )
    
    # 検索オブジェクトを作成
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    # 結果を取得
    results = list(client.results(search))
    
    # 最後に処理した論文ID以降の論文のみをフィルタリング
    if last_paper_id:
        filtered_results = []
        for paper in results:
            paper_id = extract_arxiv_id(paper)
            if paper_id > last_paper_id:
                filtered_results.append(paper)
        
        logging.info(f"{len(results)}件の論文が見つかり、ID {last_paper_id} 以降の {len(filtered_results)}件をフィルタリングしました。")
        return filtered_results
    
    logging.info(f"{len(results)}件の論文が見つかりました。")
    return results

def download_pdf(paper, download_dir, force_download=False):
    """
    論文のPDFをダウンロードします。
    
    Args:
        paper (arxiv.Result): 論文情報
        download_dir (str): ダウンロード先ディレクトリ
        force_download (bool): 既存のファイルを上書きするかどうか
    
    Returns:
        tuple: (成功したかどうか, ダウンロードパス, arXiv ID)
    """
    # PDFのURLを取得
    pdf_url = paper.pdf_url
    
    # ファイル名を作成（arXiv IDを使用）
    parsed_url = urlparse(pdf_url)
    path_parts = parsed_url.path.split('/')
    arxiv_id = path_parts[-1]
    if not arxiv_id.endswith('.pdf'):
        arxiv_id = f"{arxiv_id}.pdf"
    
    # arXiv IDから拡張子を除去（処理済みチェック用）
    arxiv_id_without_ext = os.path.splitext(arxiv_id)[0]
    
    # ダウンロード先のパスを作成
    download_path = os.path.join(download_dir, arxiv_id)
    
    # 既にファイルが存在する場合はスキップ（force_downloadがFalseの場合）
    if os.path.exists(download_path) and not force_download:
        logging.info(f"ファイル {arxiv_id} は既に存在します。スキップします。")
        return True, download_path, arxiv_id_without_ext
    
    try:
        # PDFをダウンロード
        logging.info(f"ダウンロード中: {paper.title} ({arxiv_id})")
        
        # arXivサーバーに負荷をかけないよう、ダウンロード前に待機
        time.sleep(5)  # 5秒待機
        
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        # ファイルに保存
        with open(download_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"ダウンロード完了: {download_path}")
        
        # ダウンロード後も少し待機
        time.sleep(2)  # 2秒待機
        
        return True, download_path, arxiv_id_without_ext
    
    except Exception as e:
        logging.error(f"ダウンロード失敗: {arxiv_id} - エラー: {str(e)}")
        return False, None, arxiv_id_without_ext

def process_paper(paper, dirs, openai_client, config, force_process=False, skip_twitter=False):
    """
    論文を処理する（ダウンロード、テキスト抽出、要約生成、Twitter投稿）
    
    Args:
        paper (arxiv.Result): 論文情報
        dirs (dict): ディレクトリパス
        openai_client (OpenAI): OpenAIクライアント
        config (dict): 設定情報
        force_process (bool): 処理済みの論文も強制的に処理するかどうか
        skip_twitter (bool): Twitter投稿をスキップするかどうか
    
    Returns:
        bool: 処理が成功したかどうか
    """
    # 1. PDFをダウンロード
    logging.info(f"論文 '{paper.title}' のPDFをダウンロード中...")
    start_time = time.time()
    success, pdf_path, arxiv_id = download_pdf(paper, dirs['dl'])
    end_time = time.time()
    if not success:
        logging.error(f"論文 '{paper.title}' のPDFダウンロードに失敗しました")
        return False
    logging.info(f"論文 '{paper.title}' のPDFダウンロードが完了しました（所要時間: {end_time - start_time:.2f}秒）")
    
    # 2. 処理済みかどうかを確認
    if is_processed(arxiv_id, dirs['processed']) and not force_process:
        logging.info(f"論文 {arxiv_id} は既に処理済みです。スキップします。")
        return True
    
    # 3. PDFからテキストを抽出
    logging.info(f"論文 '{paper.title}' のテキスト抽出中...")
    start_time = time.time()
    text_path = extract_text_from_pdf(pdf_path, dirs['text'])
    end_time = time.time()
    if not text_path:
        logging.error(f"論文 '{paper.title}' のテキスト抽出に失敗しました")
        return False
    logging.info(f"論文 '{paper.title}' のテキスト抽出が完了しました（所要時間: {end_time - start_time:.2f}秒）")
    
    # 4. テキストを読み込み
    with open(text_path, 'r', encoding='utf-8') as f:
        paper_text = f.read()
    # 5. 要約を生成
    logging.info(f"論文 '{paper.title}' の要約を生成中...")
    start_time = time.time()
    summary = generate_summary(
        openai_client,
        paper_text,
        config['prompt']['template'],
        dirs['summary'],
        paper.title,
        arxiv_id
    )
    end_time = time.time()
    if not summary:
        logging.error(f"論文 '{paper.title}' の要約生成に失敗しました")
        return False
    
    logging.info(f"論文 '{paper.title}' の要約生成が完了しました（所要時間: {end_time - start_time:.2f}秒）")
    
    # arXiv IDを追加
    summary['arxiv_id'] = arxiv_id
    
    # 投稿テキストを生成（post_textがない場合）
    if 'post_text' not in summary:
        post_text = summary['summary']
        
        # arXivのURLを追加
        if arxiv_id:
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            # URLを追加しても280文字以内に収まるか確認
            if len(post_text) + len(arxiv_url) + 2 <= 280:  # 改行分の2文字を追加
                post_text += f"\n\n{arxiv_url}"
        
        summary['post_text'] = post_text
    
    # 6. Twitterに投稿（スキップオプションがない場合のみ）
    if not skip_twitter:
        success = post_thread(config['twitter'], summary, dirs['logs'])
        if not success:
            logging.error(f"Twitter投稿に失敗しました。処理を中止します: {paper.title}")
            return False
    else:
        logging.info(f"Twitter投稿をスキップしました: {paper.title}")
        
        # Twitter投稿をスキップした場合も、ログファイルを生成
        log_path = os.path.join(dirs['logs'], f"{arxiv_id}_twitter_log.json")
        log_data = {
            "title": paper.title,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary['summary'],
            "post_text": summary['post_text'],
            "arxiv_id": arxiv_id,
            "tweets": []
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    # 7. 処理済みとしてマーク
    mark_as_processed(arxiv_id, paper.title, dirs['processed'])
    
    return True

def copy_pdf_if_exists(arxiv_id, target_dir):
    """
    他の検索セットで既にダウンロードされたPDFをコピー
    
    Args:
        arxiv_id (str): 論文のarXiv ID
        target_dir (str): コピー先ディレクトリ
        
    Returns:
        bool: コピーが成功したかどうか
    """
    # 全てのPDFディレクトリを検索
    pdf_dirs = glob.glob('./pdf/*')
    pdf_filename = f"{arxiv_id}.pdf"
    
    for pdf_dir in pdf_dirs:
        source_path = os.path.join(pdf_dir, pdf_filename)
        if os.path.exists(source_path) and os.path.isfile(source_path):
            target_path = os.path.join(target_dir, pdf_filename)
            # 既にターゲットディレクトリに存在する場合はスキップ
            if os.path.exists(target_path):
                return True
                
            try:
                shutil.copy2(source_path, target_path)
                logging.info(f"PDFをコピーしました: {source_path} -> {target_path}")
                return True
            except Exception as e:
                logging.error(f"PDFのコピーに失敗しました: {str(e)}")
                return False
    
    return False

def main():
    """
    メイン関数
    """
    # コマンドライン引数のパーサーを設定
    parser = argparse.ArgumentParser(
        description='arXivから指定したキーワードで論文を検索し、PDFをダウンロード、要約してTwitterに投稿します。'
    )
    parser.add_argument(
        'keywords',
        nargs='+',
        help='検索キーワード（複数指定可能）'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=200,
        help='取得する最大論文数（デフォルト: 200）'
    )
    parser.add_argument(
        '--use-or',
        action='store_true',
        help='キーワードをORで結合する（デフォルトはAND）'
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='既にダウンロード済みのファイルも再ダウンロードする'
    )
    parser.add_argument(
        '--force-process',
        action='store_true',
        help='既に処理済みの論文も再処理する'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='テストモード：未処理の論文を1つだけ処理する'
    )
    parser.add_argument(
        '--skip-twitter',
        action='store_true',
        help='Twitter投稿をスキップする'
    )
    parser.add_argument(
        '--max-process',
        type=int,
        default=9999,
        help='1回の実行で処理する論文の最大数（デフォルト: 9999）'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        help='ログディレクトリのパス（指定しない場合はデフォルトの logs/ を使用）'
    )
    parser.add_argument(
        '--since-timestamp',
        type=str,
        help='指定したタイムスタンプ以降の論文のみを検索（YYYY-MM-DDThh:mm:ssZ形式）'
    )
    parser.add_argument(
        '--last-paper-id',
        type=str,
        help='指定したID以降の論文のみを検索'
    )
    parser.add_argument(
        '--processed-ids-file',
        type=str,
        help='処理済み論文IDのリストファイル'
    )
    parser.add_argument(
        '--output-processed-ids',
        type=str,
        help='処理した論文IDを出力するファイル'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細な出力を表示します'
    )
    
    # 引数を解析
    args = parser.parse_args()
    
    # ディレクトリを設定
    dirs = setup_directories()
    
    # カスタムログディレクトリが指定されている場合は使用
    if args.log_dir:
        log_dir = args.log_dir
        os.makedirs(log_dir, exist_ok=True)
        dirs['logs'] = log_dir
    
    # ロギングを設定
    setup_logging(dirs['logs'], args.verbose)
    
    if args.verbose:
        logging.debug("コマンドライン引数: %s", args)
    
    # 設定を読み込み
    config = load_config()
    
    # OpenAIクライアントを初期化
    openai_client = OpenAI(api_key=config['openai']['api_key'])
    
    # 処理済み論文IDを読み込む
    processed_ids = set()
    if args.processed_ids_file and os.path.exists(args.processed_ids_file):
        with open(args.processed_ids_file, 'r') as f:
            processed_ids = set(f.read().splitlines())
        logging.info(f"{len(processed_ids)}件の処理済み論文IDを読み込みました。")
    
    # arXivを検索
    papers = search_arxiv(
        args.keywords,
        args.max_results,
        args.use_or,
        args.since_timestamp,
        args.last_paper_id
    )
    
    if not papers:
        logging.info("論文が見つかりませんでした。")
        sys.exit(0)
    
    # 論文情報を表示
    logging.info("\n検索結果:")
    for i, paper in enumerate(papers, 1):
        logging.info(f"{i}. {paper.title} ({paper.published.year})")
        if args.verbose and i <= 5:  # 詳細モードでは最初の5件の詳細情報を表示
            logging.debug(f"  - ID: {paper.entry_id}")
            logging.debug(f"  - 公開日: {paper.published}")
            logging.debug(f"  - 更新日: {paper.updated}")
            logging.debug(f"  - 著者: {', '.join([author.name for author in paper.authors])}")
            logging.debug(f"  - カテゴリ: {', '.join(paper.categories)}")
    
    # 処理する論文の最大数
    max_process_count = 1 if args.test_mode else args.max_process
    
    # 論文を処理
    logging.info("\n論文の処理を開始します...")
    if args.verbose:
        logging.debug(f"処理対象の論文数: {len(papers)}")
        logging.debug(f"最大処理数: {max_process_count}")
    processed_count = 0
    papers_to_process = []
    
    # 新しく処理した論文IDを記録するセット
    newly_processed_ids = set()
    
    # 処理対象の論文を選定
    for i, paper in enumerate(papers):
        if processed_count >= max_process_count:
            break
        
        # arXiv IDを抽出
        arxiv_id = extract_arxiv_id(paper)
        
        # 処理済みかどうかを確認
        if not is_processed(arxiv_id, dirs['processed'], processed_ids) or args.force_process:
            # PDFが他のディレクトリに存在するかチェックし、存在する場合はコピー
            if not copy_pdf_if_exists(arxiv_id, dirs['dl']):
                # コピーできなかった場合はダウンロード
                success, _, _ = download_pdf(paper, dirs['dl'])
                if not success:
                    continue
            
            papers_to_process.append(paper)
            newly_processed_ids.add(arxiv_id)
            processed_count += 1
    
    # 処理対象の論文がない場合
    if not papers_to_process:
        logging.info("処理対象の論文がありません。")
        sys.exit(0)
    
    # 論文を処理（最後の論文以外はTwitter投稿をスキップ）
    for i, paper in enumerate(papers_to_process):
        # 最後の論文以外はTwitter投稿をスキップ
        is_last_paper = (i == len(papers_to_process) - 1)
        current_skip_twitter = args.skip_twitter or not is_last_paper
        
        if current_skip_twitter:
            logging.info(f"論文 {i+1}/{len(papers_to_process)}: {paper.title} - Twitter投稿はスキップします")
        else:
            logging.info(f"論文 {i+1}/{len(papers_to_process)}: {paper.title} - Twitter投稿を行います")
        
        # 論文を処理
        if args.verbose:
            logging.debug(f"論文を処理中: {paper.title}")
            
        success = process_paper(paper, dirs, openai_client, config, args.force_process, current_skip_twitter)
        
        # Twitter投稿の結果をログに記録
        if success and not current_skip_twitter:
            twitter_msg = f"Twitter投稿完了: {paper.title}"
            logging.info(twitter_msg)
            print(twitter_msg)
        
        # arXivのAPIレート制限を回避するために待機
        # 以前は1秒だったが、より長い待機時間に変更
        wait_time = 5  # 5秒待機
        if args.verbose:
            logging.debug(f"{wait_time}秒待機中...")
        time.sleep(wait_time)
    
    # Twitter投稿の有無を確認
    twitter_posted = False
    for i, paper in enumerate(papers_to_process):
        is_last_paper = (i == len(papers_to_process) - 1)
        if not args.skip_twitter and is_last_paper:
            twitter_posted = True
            break
    
    # 処理した論文IDを出力
    if args.output_processed_ids and newly_processed_ids:
        with open(args.output_processed_ids, 'w') as f:
            f.write('\n'.join(newly_processed_ids))
        logging.info(f"{len(newly_processed_ids)}件の処理済み論文IDを出力しました: {args.output_processed_ids}")
    
    logging.info(f"\n処理完了: {processed_count}/{len(papers)}件の論文を処理しました。")
    logging.info(f"Twitter投稿: {'あり' if twitter_posted else 'なし'}")

if __name__ == "__main__":
    main()
