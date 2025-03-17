#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
import time
import logging
from datetime import datetime
import shutil
from collections import defaultdict

def classify_logs_by_date(log_files):
    """
    ログファイルを日付ごとに分類する
    
    Args:
        log_files (list): ログファイルのパスのリスト
        
    Returns:
        dict: 日付ごとのログデータのリスト
    """
    date_logs = defaultdict(list)
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # タイムスタンプを解析
            timestamp = log_data.get('timestamp')
            if timestamp:
                date = timestamp.split()[0]  # YYYY-MM-DD
                
                # 論文情報を作成
                paper_info = process_log_data(log_file, log_data)
                if paper_info:
                    date_logs[date].append(paper_info)
        except Exception as e:
            logging.error(f"ログファイル {log_file} の解析エラー: {str(e)}")
    
    return date_logs

def process_log_data(log_file, log_data):
    """
    ログデータから論文情報を抽出する
    
    Args:
        log_file (str): ログファイルのパス
        log_data (dict): ログデータ
        
    Returns:
        dict: 論文情報
    """
    try:
        # タイムスタンプを解析
        timestamp = log_data.get('timestamp')
        if not timestamp:
            return None
        
        # 日時オブジェクトに変換
        try:
            date_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            formatted_date = date_obj.strftime("%Y年%m月%d日 %H:%M")
        except ValueError:
            formatted_date = timestamp
        
        # arXiv IDを取得
        arxiv_id = log_data.get('arxiv_id')
        
        # ログデータにarXiv IDがない場合は、ツイート内容から抽出を試みる
        if not arxiv_id:
            import re
            
            # ツイート内容から抽出
            if 'tweets' in log_data and log_data['tweets']:
                for tweet in log_data['tweets']:
                    if 'text' in tweet:
                        # ツイート内容からarXiv URLを検索
                        url_match = re.search(r'https://arxiv\.org/abs/(\d+\.\d+v\d+)', tweet['text'])
                        if url_match:
                            arxiv_id = url_match.group(1)
                            break
            
            # post_textから抽出
            if not arxiv_id and 'post_text' in log_data:
                url_match = re.search(r'https://arxiv\.org/abs/(\d+\.\d+v\d+)', log_data['post_text'])
                if url_match:
                    arxiv_id = url_match.group(1)
        
        # 論文情報を追加
        paper_info = {
            'title': log_data.get('title', 'Unknown'),
            'timestamp': timestamp,
            'formatted_date': formatted_date,
            'arxiv_id': arxiv_id,
        }
        
        # 要約文を取得（エラーの有無にかかわらず）
        if 'summary' in log_data:
            paper_info['summary'] = log_data['summary']
        elif 'tweets' in log_data and log_data['tweets']:
            # 古い形式のログからツイート内容を取得
            for tweet in log_data['tweets']:
                if tweet.get('type') == 'post' or tweet.get('type') == 'greeting':
                    paper_info['summary'] = tweet.get('text', '')
                    break
        
        # 要約情報がない場合はデフォルトメッセージを設定
        if 'summary' not in paper_info:
            paper_info['summary'] = '要約情報がありません。'
        
        # エラーがない場合は投稿成功とみなす
        if 'error' not in log_data:
            paper_info['status'] = 'Success'
            
            # ツイート情報を取得
            if 'tweets' in log_data and log_data['tweets']:
                for tweet in log_data['tweets']:
                    if 'id' in tweet:
                        paper_info['tweet_id'] = tweet['id']
                        break
        else:
            # エラーがある場合
            paper_info['status'] = 'Failed'
            paper_info['error'] = log_data.get('error', 'Unknown error')
        
        return paper_info
    
    except Exception as e:
        logging.error(f"ログファイル {log_file} の処理中にエラーが発生しました: {str(e)}")
        return None

def generate_daily_page(date, papers, output_dir):
    """
    日付ごとのページを生成する
    
    Args:
        date (str): 日付（YYYY-MM-DD）
        papers (list): 論文データのリスト
        output_dir (str): 出力先ディレクトリのパス
        
    Returns:
        str: 生成されたファイルのパス
    """
    # 年月日を分解
    year, month, day = date.split('-')
    
    # ナビゲーションリンクを作成
    nav_html = f"""
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="index.html">ホーム</a></li>
        <li class="breadcrumb-item"><a href="{year}.html">{year}年</a></li>
        <li class="breadcrumb-item"><a href="{year}-{month}.html">{year}年{month}月</a></li>
        <li class="breadcrumb-item active" aria-current="page">{year}年{month}月{day}日</li>
      </ol>
    </nav>
    """
    
    # HTMLを生成
    html = generate_html_template(f"{year}年{month}月{day}日の論文要約", papers, nav_html)
    
    # ファイルに保存
    file_path = os.path.join(output_dir, f"{date}.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return file_path

def generate_monthly_index(year, month, date_logs, output_dir):
    """
    月別インデックスページを生成する
    
    Args:
        year (str): 年（YYYY）
        month (str): 月（MM）
        date_logs (dict): 日付ごとのログデータ
        output_dir (str): 出力先ディレクトリのパス
        
    Returns:
        str: 生成されたファイルのパス
    """
    # 月内の日付リンクリスト
    date_links = []
    for date in sorted([d for d in date_logs.keys() if d.startswith(f"{year}-{month}")], reverse=True):
        y, m, d = date.split('-')
        date_links.append(f'<li><a href="{date}.html">{y}年{m}月{d}日</a> ({len(date_logs[date])}件)</li>')
    
    # ナビゲーションリンクを作成
    nav_html = f"""
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="index.html">ホーム</a></li>
        <li class="breadcrumb-item"><a href="{year}.html">{year}年</a></li>
        <li class="breadcrumb-item active" aria-current="page">{year}年{month}月</li>
      </ol>
    </nav>
    """
    
    # HTMLを生成
    html = f"""<!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{year}年{month}月の論文要約</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="css/custom.css">
    </head>
    <body>
        <div class="container py-4">
            <header class="pb-3 mb-4 border-bottom">
                <div class="d-flex align-items-center text-dark text-decoration-none">
                    <span class="fs-4">{year}年{month}月の論文要約</span>
                    <span class="ms-auto">最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</span>
                </div>
            </header>
            
            {nav_html}
            
            <div class="alert alert-info">
                <p><strong>C(・ω・ )つ みんなー！</strong> {year}年{month}月の論文要約一覧だよ！</p>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            日別アーカイブ
                        </div>
                        <div class="card-body">
                            <ul>
                                {"".join(date_links)}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script src="js/custom.js"></script>
    </body>
    </html>
    """
    
    # ファイルに保存
    file_path = os.path.join(output_dir, f"{year}-{month}.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return file_path

def generate_yearly_index(year, date_logs, output_dir):
    """
    年別インデックスページを生成する
    
    Args:
        year (str): 年（YYYY）
        date_logs (dict): 日付ごとのログデータ
        output_dir (str): 出力先ディレクトリのパス
        
    Returns:
        str: 生成されたファイルのパス
    """
    # 年内の月を抽出
    months = sorted(set([d.split('-')[1] for d in date_logs.keys() if d.startswith(f"{year}-")]), reverse=True)
    
    # 月別リンクリスト
    month_links = []
    for month in months:
        # 月内の論文数をカウント
        month_papers_count = sum(len(date_logs[d]) for d in date_logs.keys() if d.startswith(f"{year}-{month}"))
        month_links.append(f'<li><a href="{year}-{month}.html">{year}年{month}月</a> ({month_papers_count}件)</li>')
    
    # ナビゲーションリンクを作成
    nav_html = f"""
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="index.html">ホーム</a></li>
        <li class="breadcrumb-item active" aria-current="page">{year}年</li>
      </ol>
    </nav>
    """
    
    # HTMLを生成
    html = f"""<!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{year}年の論文要約</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="css/custom.css">
    </head>
    <body>
        <div class="container py-4">
            <header class="pb-3 mb-4 border-bottom">
                <div class="d-flex align-items-center text-dark text-decoration-none">
                    <span class="fs-4">{year}年の論文要約</span>
                    <span class="ms-auto">最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</span>
                </div>
            </header>
            
            {nav_html}
            
            <div class="alert alert-info">
                <p><strong>C(・ω・ )つ みんなー！</strong> {year}年の論文要約一覧だよ！</p>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            月別アーカイブ
                        </div>
                        <div class="card-body">
                            <ul>
                                {"".join(month_links)}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script src="js/custom.js"></script>
    </body>
    </html>
    """
    
    # ファイルに保存
    file_path = os.path.join(output_dir, f"{year}.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return file_path

def generate_main_index(date_logs, output_dir):
    """
    メインインデックスページを生成する
    
    Args:
        date_logs (dict): 日付ごとのログデータ
        output_dir (str): 出力先ディレクトリのパス
        
    Returns:
        str: 生成されたファイルのパス
    """
    # 最新の日付を取得
    latest_dates = sorted(date_logs.keys(), reverse=True)[:5]  # 最新5日分
    
    # 年のリストを作成
    years = sorted(set([d.split('-')[0] for d in date_logs.keys()]), reverse=True)
    
    # 最新の論文を取得
    latest_papers = []
    for date in latest_dates:
        latest_papers.extend(date_logs[date])
    
    # 最新10件に制限
    latest_papers = sorted(latest_papers, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    # アーカイブリンクを作成
    archive_html = '<div class="card mt-4"><div class="card-header">アーカイブ</div><div class="card-body">'
    
    # 年別リンク
    for year in years:
        # 年内の論文数をカウント
        year_papers_count = sum(len(date_logs[d]) for d in date_logs.keys() if d.startswith(f"{year}-"))
        archive_html += f'<h5><a href="{year}.html">{year}年</a> ({year_papers_count}件)</h5>'
        
        # 月別リンク（最新の年のみ表示）
        if year == years[0]:
            archive_html += '<ul>'
            months = sorted(set([d.split('-')[1] for d in date_logs.keys() if d.startswith(f"{year}-")]), reverse=True)
            for month in months:
                # 月内の論文数をカウント
                month_papers_count = sum(len(date_logs[d]) for d in date_logs.keys() if d.startswith(f"{year}-{month}"))
                archive_html += f'<li><a href="{year}-{month}.html">{year}年{month}月</a> ({month_papers_count}件)</li>'
            archive_html += '</ul>'
    
    archive_html += '</div></div>'
    
    # HTMLを生成
    html = generate_html_template("arXiv論文要約", latest_papers, "", archive_html)
    
    # ファイルに保存
    file_path = os.path.join(output_dir, "index.html")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return file_path

def generate_html_template(title, papers, navigation="", archive=""):
    """
    基本的なHTMLテンプレートを生成する
    
    Args:
        title (str): ページタイトル
        papers (list): 論文データのリスト
        navigation (str): ナビゲーションHTML
        archive (str): アーカイブHTML
        
    Returns:
        str: 生成されたHTML
    """
    html = f"""<!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="css/custom.css">
    </head>
    <body>
        <!-- コピー成功モーダル -->
        <div class="modal fade" id="copyModal" tabindex="-1" aria-labelledby="copyModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-sm modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center py-4">
                        <h5 class="mb-0">コピーしました</h5>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container py-4">
            <header class="pb-3 mb-4 border-bottom">
                <div class="d-flex align-items-center text-dark text-decoration-none">
                    <span class="fs-4">{title}</span>
                    <span class="ms-auto">最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</span>
                </div>
            </header>
            
            {navigation}
            
            <div class="alert alert-info">
                <p><strong>C(・ω・ )つ みんなー！</strong> 最新の論文要約をお届けします！</p>
            </div>
            
            <div class="row">
                {generate_paper_cards(papers)}
            </div>
            
            {archive}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script src="js/custom.js"></script>
    </body>
    </html>
    """
    
    return html

def generate_paper_cards(papers):
    """
    論文カードのHTMLを生成する
    
    Args:
        papers (list): 論文データのリスト
        
    Returns:
        str: 生成されたHTML
    """
    cards_html = ""
    
    for paper in papers:
        # arXivリンク
        arxiv_url = ""
        arxiv_link_small = ""
        arxiv_link_button = ""
        
        # arXiv IDがある場合のみURLを表示
        if paper.get('arxiv_id'):
            arxiv_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"
            arxiv_link_small = f'<div class="arxiv-link"><a href="javascript:void(0);" class="copy-url" data-url="{arxiv_url}">{arxiv_url}</a></div>'
            arxiv_link_button = f'<a href="{arxiv_url}" class="btn btn-sm btn-outline-primary">arXiv</a>'
        
        # Twitterリンク
        twitter_link = ""
        if paper.get('tweet_id'):
            twitter_link = f'<a href="https://twitter.com/user/status/{paper["tweet_id"]}" target="_blank" class="btn btn-sm btn-outline-info ms-2">Twitter</a>'
        
        # 要約文
        summary = paper.get('summary', '要約情報がありません。')
        
        cards_html += f"""
        <div class="col-md-6 mb-4">
            <div class="card paper-card h-100">
                <div class="card-body">
                    <h5 class="paper-title">{paper['title']}</h5>
                    <!-- {arxiv_link_small} -->
                    <h6 class="card-subtitle mb-2 text-muted">{paper.get('formatted_date', '')}</h6>
                    <div class="card-text mt-3">
                        <p class="summary-text">{arxiv_url} C(・ω・ )つ みんなー！{summary}</p>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    {arxiv_link_button}
                    {twitter_link}
                </div>
            </div>
        </div>
        """
    
    return cards_html

def generate_webpage(log_dir, output_dir, current_only=False, current_date=None, verbose=False):
    """
    Twitter投稿ログからWebページを生成する
    
    Args:
        log_dir (str): ログディレクトリのパス
        output_dir (str): 出力先ディレクトリのパス
        current_only (bool): 現在の日付のページのみを生成するかどうか
        current_date (str): 現在の日付（YYYY-MM-DD形式）
    
    Returns:
        bool: 生成が成功したかどうか
    """
    try:
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # CSSとJSディレクトリを作成
        css_dir = os.path.join(output_dir, "css")
        js_dir = os.path.join(output_dir, "js")
        os.makedirs(css_dir, exist_ok=True)
        os.makedirs(js_dir, exist_ok=True)
        
        # ログファイルを取得
        log_files = glob.glob(os.path.join(log_dir, "*_twitter_log.json"))
        if verbose:
            logging.debug(f"{len(log_files)}件のログファイルを検出しました")
        
        if not log_files:
            logging.warning("ログファイルが見つかりません。")
            return False
        
        # 日付ごとにログを分類
        date_logs = classify_logs_by_date(log_files)
        
        if not date_logs:
            logging.warning("処理可能なログデータが見つかりません。")
            return False
        
        # 現在の日付の情報を取得
        if current_only and current_date:
            current_year, current_month, current_day = current_date.split('-')
        
        # 日付ごとのページを生成
        if current_only:
            # 現在の日付のページのみを生成
            if current_date in date_logs:
                if verbose:
                    logging.debug(f"現在の日付 {current_date} のページを生成します（{len(date_logs[current_date])}件の論文）")
                
                start_time = time.time()
                file_path = generate_daily_page(current_date, date_logs[current_date], output_dir)
                end_time = time.time()
                
                logging.info(f"日付別ページを生成しました: {current_date}.html（所要時間: {end_time - start_time:.2f}秒）")
                if verbose:
                    logging.debug(f"生成されたファイル: {file_path}（サイズ: {os.path.getsize(file_path)}バイト）")
            else:
                logging.warning(f"現在の日付 ({current_date}) のログデータが見つかりません。")
        else:
            # 全ての日付のページを生成
            for date, papers in date_logs.items():
                generate_daily_page(date, papers, output_dir)
                logging.info(f"日付別ページを生成しました: {date}.html")
        
        # 年月のリストを作成
        years = set()
        year_months = defaultdict(set)
        
        for date in date_logs.keys():
            year, month, _ = date.split('-')
            years.add(year)
            year_months[year].add(month)
        
        # 月別インデックスを生成
        if current_only:
            # 現在の月のインデックスのみを生成
            if current_year in year_months and current_month in year_months[current_year]:
                if verbose:
                    logging.debug(f"現在の月 {current_year}-{current_month} のインデックスを生成します")
                
                start_time = time.time()
                file_path = generate_monthly_index(current_year, current_month, date_logs, output_dir)
                end_time = time.time()
                
                logging.info(f"月別インデックスを生成しました: {current_year}-{current_month}.html（所要時間: {end_time - start_time:.2f}秒）")
                if verbose:
                    logging.debug(f"生成されたファイル: {file_path}（サイズ: {os.path.getsize(file_path)}バイト）")
            else:
                logging.warning(f"現在の月 ({current_year}-{current_month}) のログデータが見つかりません。")
        else:
            # 全ての月のインデックスを生成
            for year in years:
                for month in year_months[year]:
                    generate_monthly_index(year, month, date_logs, output_dir)
                    logging.info(f"月別インデックスを生成しました: {year}-{month}.html")
        
        # 年別インデックスを生成
        if current_only:
            # 現在の年のインデックスのみを生成
            if current_year in years:
                if verbose:
                    logging.debug(f"現在の年 {current_year} のインデックスを生成します")
                
                start_time = time.time()
                file_path = generate_yearly_index(current_year, date_logs, output_dir)
                end_time = time.time()
                
                logging.info(f"年別インデックスを生成しました: {current_year}.html（所要時間: {end_time - start_time:.2f}秒）")
                if verbose:
                    logging.debug(f"生成されたファイル: {file_path}（サイズ: {os.path.getsize(file_path)}バイト）")
            else:
                logging.warning(f"現在の年 ({current_year}) のログデータが見つかりません。")
        else:
            # 全ての年のインデックスを生成
            for year in years:
                generate_yearly_index(year, date_logs, output_dir)
                logging.info(f"年別インデックスを生成しました: {year}.html")
        
        # メインインデックスを生成
        if verbose:
            logging.debug(f"メインインデックスを生成します")
        
        start_time = time.time()
        index_path = generate_main_index(date_logs, output_dir)
        end_time = time.time()
        
        logging.info(f"メインインデックスを生成しました: index.html（所要時間: {end_time - start_time:.2f}秒）")
        if verbose:
            logging.debug(f"生成されたファイル: {index_path}（サイズ: {os.path.getsize(index_path)}バイト）")
        
        # CSSとJSファイルをコピー
        css_dir = os.path.join(output_dir, "css")
        js_dir = os.path.join(output_dir, "js")
        os.makedirs(css_dir, exist_ok=True)
        os.makedirs(js_dir, exist_ok=True)
        
        # カスタムCSSを作成
        custom_css = """
        .paper-card {
            margin-bottom: 20px;
            transition: transform 0.2s;
        }
        .paper-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .summary-text {
            cursor: pointer;
        }
        .paper-title {
            cursor: pointer;
        }
        .arxiv-link {
            font-size: 0.8rem;
            color: #6c757d;
            margin-top: -5px;
            margin-bottom: 10px;
            display: block;
        }
        .arxiv-link a {
            color: #6c757d;
            text-decoration: none;
            cursor: pointer;
        }
        .arxiv-link a:hover {
            text-decoration: underline;
        }
        @media (max-width: 768px) {
            .container {
                padding-left: 10px;
                padding-right: 10px;
            }
        }
        """
        
        with open(os.path.join(css_dir, "custom.css"), 'w', encoding='utf-8') as f:
            f.write(custom_css)
        
        # カスタムJSを作成
        custom_js = """
        document.addEventListener('DOMContentLoaded', function() {
            // クリップボードにコピーする関数
            function copyToClipboard(text) {
                // テキストエリアを作成
                const textarea = document.createElement('textarea');
                textarea.value = text;
                
                // スタイルを設定して画面外に配置
                textarea.style.position = 'fixed';
                textarea.style.opacity = 0;
                document.body.appendChild(textarea);
                
                // テキストを選択してコピー
                textarea.select();
                let success = false;
                
                try {
                    // execCommandを試す
                    success = document.execCommand('copy');
                } catch (err) {
                    console.error('コピーに失敗しました:', err);
                }
                
                // テキストエリアを削除
                document.body.removeChild(textarea);
                
                // 新しいClipboard APIも試す（execCommandが失敗した場合）
                if (!success && navigator.clipboard) {
                    navigator.clipboard.writeText(text).catch(err => {
                        console.error('Clipboard APIでのコピーに失敗しました:', err);
                    });
                    success = true;
                }
                
                return success;
            }
            
            // 成功メッセージを表示
            function showCopySuccess(element) {
                if (!element) return;
                
                element.classList.add('show');
                setTimeout(() => {
                    element.classList.remove('show');
                }, 2000);
            }
            
            // モーダルを表示する関数
            function showCopyModal() {
                const copyModal = new bootstrap.Modal(document.getElementById('copyModal'));
                copyModal.show();
                
                // 2秒後に自動的に閉じる
                setTimeout(() => {
                    copyModal.hide();
                }, 2000);
            }
            
            // 要約文のクリップボードコピー機能
            document.querySelectorAll('.summary-text').forEach(function(element) {
                element.addEventListener('click', function() {
                    const text = this.textContent;
                    const success = copyToClipboard(text);
                    
                    if (success) {
                        showCopyModal();
                    } else {
                        console.error('要約文のコピーに失敗しました。');
                    }
                });
            });
            
            // タイトルのクリップボードコピー機能
            document.querySelectorAll('.paper-title').forEach(function(element) {
                element.addEventListener('click', function() {
                    const text = this.textContent;
                    const success = copyToClipboard(text);
                    
                    if (success) {
                        showCopyModal();
                    } else {
                        console.error('タイトルのコピーに失敗しました。');
                    }
                });
            });
            
            // URLのクリップボードコピー機能
            document.querySelectorAll('.copy-url').forEach(function(element) {
                element.addEventListener('click', function(e) {
                    e.preventDefault();
                    const url = this.getAttribute('data-url');
                    const success = copyToClipboard(url);
                    
                    if (success) {
                        showCopyModal();
                    } else {
                        console.error('URLのコピーに失敗しました。');
                    }
                });
            });
        });
        """
        
        with open(os.path.join(js_dir, "custom.js"), 'w', encoding='utf-8') as f:
            f.write(custom_js)
        
        logging.info(f"Webページを生成しました: {index_path}")
        return True
    
    except Exception as e:
        logging.error(f"Webページ生成エラー: {str(e)}")
        return False

def generate_html(papers):
    """
    論文データからHTMLを生成する
    
    Args:
        papers (list): 論文データのリスト
    
    Returns:
        str: 生成されたHTML
    """
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>arXiv論文要約</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/custom.css">
</head>
<body>
    <!-- コピー成功モーダル -->
    <div class="modal fade" id="copyModal" tabindex="-1" aria-labelledby="copyModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-sm modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body text-center py-4">
                    <h5 class="mb-0">コピーしました</h5>
                </div>
            </div>
        </div>
    </div>

    <div class="container py-4">
        <header class="pb-3 mb-4 border-bottom">
            <div class="d-flex align-items-center text-dark text-decoration-none">
                <span class="fs-4">arXiv論文要約</span>
                <span class="ms-auto">最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</span>
            </div>
        </header>
        
        <div class="row">
"""
    
    for paper in papers:
        # arXivリンク（フッターとタイトル下の両方に表示）
        arxiv_url = ""
        arxiv_link_small = ""
        arxiv_link_button = ""
        
        # arXiv IDがある場合のみURLを表示
        if paper.get('arxiv_id'):
            arxiv_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"
            arxiv_link_small = f'<div class="arxiv-link"><a href="javascript:void(0);" class="copy-url" data-url="{arxiv_url}">{arxiv_url}</a></div>'
            arxiv_link_button = f'<a href="{arxiv_url}" class="btn btn-sm btn-outline-primary">arXiv</a>'
        
        # Twitterリンク
        twitter_link = ""
        if paper.get('tweet_id'):
            twitter_link = f'<a href="https://twitter.com/user/status/{paper["tweet_id"]}" target="_blank" class="btn btn-sm btn-outline-info ms-2">Twitter</a>'
        
        # 要約文
        summary = paper.get('summary', '要約情報がありません。')
        
        html += f"""
        <div class="col-md-6 mb-4">
            <div class="card paper-card h-100">
                <div class="card-body">
                    <h5 class="paper-title">{paper['title']}</h5>
                    {arxiv_link_small}
                    <h6 class="card-subtitle mb-2 text-muted">{paper['formatted_date']}</h6>
                    <div class="card-text mt-3">
                        <p><strong>C(・ω・ )つ みんなー！</strong> この論文はこんな内容だよ：</p>
                        <p class="summary-text">{summary}</p>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    {arxiv_link_button}
                    {twitter_link}
                </div>
            </div>
        </div>
"""
    
    html += """
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/custom.js"></script>
</body>
</html>
"""
    
    return html

def main():
    """
    メイン関数
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Twitter投稿ログからWebページを生成します。'
    )
    parser.add_argument(
        '--log-dir',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'),
        help='ログディレクトリのパス（デフォルト: logs/）'
    )
    parser.add_argument(
        '--output-dir',
        default='/var/www/html/arxiv',
        help='出力先ディレクトリのパス（デフォルト: /var/www/html/arxiv/）'
    )
    parser.add_argument(
        '--current-only',
        action='store_true',
        help='現在の日付、月、年のページのみを生成します（デフォルト: 全ページ生成）'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細な出力を表示します'
    )
    
    args = parser.parse_args()
    
    # ロギングを設定
    # ログレベルを設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # ロギングを設定
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.verbose:
        logging.info("詳細モードで実行します")
    
    # 現在の日付を取得
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_year, current_month, current_day = current_date.split('-')
    
    if args.current_only:
        logging.info(f"現在の日付 ({current_date}) のページのみを生成します")
    
    # Webページを生成
    success = generate_webpage(args.log_dir, args.output_dir, args.current_only, current_date)
    
    if success:
        if args.current_only:
            print(f"現在の日付 ({current_date}) のWebページを生成しました: {os.path.join(args.output_dir, 'index.html')}")
        else:
            print(f"全てのWebページを生成しました: {os.path.join(args.output_dir, 'index.html')}")
    else:
        print("Webページの生成に失敗しました。")

if __name__ == "__main__":
    main()