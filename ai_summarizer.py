#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from openai import OpenAI

def generate_summary(client, text, prompt_template, output_dir, paper_title, arxiv_id=None):
    """
    論文テキストから120文字の紹介文を生成する
    
    Args:
        client (OpenAI): OpenAIクライアント
        text (str): 論文テキスト
        prompt_template (str): プロンプトテンプレート
        output_dir (str): 出力先ディレクトリ
        paper_title (str): 論文タイトル
        arxiv_id (str, optional): arXiv ID
    
    Returns:
        dict: 生成された要約と挨拶文
    """
    # ファイル名を作成（arXiv IDがある場合はそれを使用）
    if arxiv_id:
        output_path = os.path.join(output_dir, f"{arxiv_id}_summary.json")
    else:
        filename = paper_title.replace(" ", "_").replace("/", "_")[:50]
        output_path = os.path.join(output_dir, f"{filename}.json")
    
    try:
        # プロンプトを作成
        logging.info(f"論文 '{paper_title}' のプロンプトを作成中...")
        prompt = prompt_template.replace("{論文テキスト}", text)
        logging.info(f"プロンプト作成完了（文字数: {len(prompt)}文字）")
        
        # OpenAI APIを呼び出し - リトライロジックを追加
        max_retries = 3
        retry_count = 0
        backoff_time = 2  # 初期バックオフ時間（秒）
        while retry_count < max_retries:
            try:
                logging.info(f"OpenAI APIを呼び出し中... (試行: {retry_count + 1}/{max_retries})")
                api_start_time = time.time()
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "あなたは研究論文を中学生向けにわかりやすく紹介するゆるキャラです。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300
                )
                
                api_end_time = time.time()
                api_duration = api_end_time - api_start_time
                logging.info(f"OpenAI API呼び出し完了（所要時間: {api_duration:.2f}秒）")
                break  # 成功したらループを抜ける
                break  # 成功したらループを抜ける
            except Exception as api_error:
                retry_count += 1
                if retry_count >= max_retries:
                    raise  # 最大リトライ回数に達したら例外を再スロー
                
                # エラーの種類に応じてバックオフ時間を調整
                if hasattr(api_error, 'status_code') and api_error.status_code == 429:
                    logging.warning(f"API制限エラー（429）が発生しました。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                else:
                    logging.warning(f"APIエラーが発生しました: {str(api_error)}。{backoff_time}秒後にリトライします。({retry_count}/{max_retries})")
                
                time.sleep(backoff_time)
                backoff_time *= 2  # 指数バックオフ
        # 応答から要約を取得
        logging.info("APIレスポンスから要約を抽出中...")
        summary_text = response.choices[0].message.content.strip()
        logging.info(f"要約抽出完了（文字数: {len(summary_text)}文字）")
        summary_text = response.choices[0].message.content.strip()
        
        # 要約の文字数制限を削除
        # 元々は120文字に制限していたが、全文を保持するように変更
        
        # 投稿文を作成
        logging.info("Twitter投稿用テキストを作成中...")
        post_text = f"C(・ω・ )つ みんなー！{summary_text}"
        
        # 文字数制限（280文字）
        original_length = len(post_text)
        if original_length > 130:
            post_text = post_text[:277] + "..."
            logging.info(f"投稿テキストを短縮しました（{original_length}文字 → {len(post_text)}文字）")
        else:
            logging.info(f"投稿テキスト作成完了（文字数: {len(post_text)}文字）")
        
        # 結果を辞書にまとめる
        result = {
            "title": paper_title,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary_text,
            "post_text": post_text
        }
        
        # arXiv IDがある場合は追加
        if 'arxiv_id' in locals() or 'arxiv_id' in globals():
            result["arxiv_id"] = arxiv_id
        
        # 結果をJSONファイルに保存
        logging.info(f"要約結果をファイルに保存中: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logging.info(f"要約生成・保存完了: {output_path}")
        return result
    
    except Exception as e:
        logging.error(f"要約生成エラー: {str(e)}")
        return None