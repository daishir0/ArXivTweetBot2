#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import tweepy

def post_thread(config, summary, log_dir):
    """
    要約をTwitterに投稿する
    
    Args:
        config (dict): Twitter API設定（APIキー、トークンなど）
        summary (dict): 投稿する要約
        log_dir (str): ログ出力先ディレクトリ
    
    Returns:
        bool: 投稿が成功したかどうか
        
    Note:
        エラーが発生した場合はリトライせずに即座にFalseを返します。
        エラー情報はログファイルに記録されます。
    """
    # ログファイルパス
    # arXiv IDがある場合はそれを使用、ない場合はタイトルを使用
    if 'arxiv_id' in summary and summary['arxiv_id']:
        log_path = os.path.join(log_dir, f"{summary['arxiv_id']}_twitter_log.json")
    else:
        log_path = os.path.join(log_dir, f"{summary['title'].replace(' ', '_')[:30]}_twitter_log.json")
    
    try:
        # Twitter APIの認証情報
        ck = config['api_key']
        cs = config['api_key_secret']
        at = config['access_token']
        ats = config['access_token_secret']
        
        # tweepy Clientを初期化
        client = tweepy.Client(
            consumer_key=ck,
            consumer_secret=cs,
            access_token=at,
            access_token_secret=ats
        )
        
        tweets = []
        
        # arXiv IDを取得
        arxiv_id = None
        if 'arxiv_id' in summary:
            arxiv_id = summary['arxiv_id']
        
        # 投稿テキストを取得
        post_text = summary['post_text']
        
        # arXivのURLを追加
        if arxiv_id:
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            # URLを追加しても280文字以内に収まるか確認
            if len(post_text) + len(arxiv_url) + 2 <= 280:  # 改行分の2文字を追加
                post_text += f"\n\n{arxiv_url}"
        
        logging.info(f"ツイートを投稿中: {post_text}")
        tweet_response = client.create_tweet(text=post_text)
        tweet_id = tweet_response.data['id']
        tweets.append({
            "type": "post",
            "id": tweet_id,
            "text": post_text
        })
        
        # ログを保存
        log_data = {
            "title": summary['title'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary['summary'],
            "tweets": tweets
        }
        
        # arXiv IDがある場合は追加
        if arxiv_id:
            log_data["arxiv_id"] = arxiv_id
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Twitter投稿成功: {summary['title']}")
        # コンソールにも出力
        print(f"Twitter投稿成功: {summary['title']}")
        return True
    
    except Exception as e:
        error_msg = f"Twitter投稿エラー: {str(e)}"
        logging.error(error_msg)
        # コンソールにも出力
        print(error_msg)
        
        # エラーの詳細情報を取得
        if hasattr(e, 'response') and e.response is not None:
            api_error = f"Twitter APIレスポンス: {e.response.text}"
            logging.error(api_error)
            print(api_error)
        
        # エラーログを保存
        error_log = {
            "title": summary['title'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary.get('summary', ''),
            "error": str(e),
            "tweets": tweets if 'tweets' in locals() else []
        }
        
        # arXiv IDがある場合は追加
        if 'arxiv_id' in summary:
            error_log["arxiv_id"] = summary['arxiv_id']
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, ensure_ascii=False, indent=2)
        
        return False