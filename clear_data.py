#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import glob
import logging
import argparse

def setup_logging():
    """
    ロギングを設定
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def clear_directory(directory, keep_dir=True):
    """
    ディレクトリ内のファイルを削除
    
    Args:
        directory (str): 削除対象のディレクトリパス
        keep_dir (bool): ディレクトリ自体は残すかどうか
    """
    if not os.path.exists(directory):
        logging.info(f"ディレクトリが存在しません: {directory}")
        return
    
    if keep_dir:
        # ディレクトリ内のファイルのみを削除
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                    logging.info(f"ファイルを削除しました: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logging.info(f"ディレクトリを削除しました: {item_path}")
            except Exception as e:
                logging.error(f"削除中にエラーが発生しました: {item_path} - {str(e)}")
    else:
        # ディレクトリごと削除して再作成
        try:
            shutil.rmtree(directory)
            logging.info(f"ディレクトリを削除しました: {directory}")
            os.makedirs(directory, exist_ok=True)
            logging.info(f"ディレクトリを再作成しました: {directory}")
        except Exception as e:
            logging.error(f"ディレクトリの削除/再作成中にエラーが発生しました: {directory} - {str(e)}")

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(
        description='ArXivHitokotoBotのデータをクリアします。'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='すべてのデータをクリア（PDFs, テキスト, 要約, 処理済み記録, ログ）'
    )
    parser.add_argument(
        '--pdfs',
        action='store_true',
        help='ダウンロードしたPDFファイルをクリア'
    )
    parser.add_argument(
        '--texts',
        action='store_true',
        help='抽出したテキストファイルをクリア'
    )
    parser.add_argument(
        '--summaries',
        action='store_true',
        help='生成した要約ファイルをクリア'
    )
    parser.add_argument(
        '--processed',
        action='store_true',
        help='処理済み記録をクリア'
    )
    parser.add_argument(
        '--logs',
        action='store_true',
        help='ログファイルをクリア'
    )
    
    args = parser.parse_args()
    
    # ロギングを設定
    setup_logging()
    
    # ベースディレクトリを取得
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ディレクトリパスを設定
    dirs = {
        'dl': os.path.join(base_dir, 'dl'),
        'text': os.path.join(base_dir, 'text'),
        'summary': os.path.join(base_dir, 'summary'),
        'processed': os.path.join(base_dir, 'processed'),
        'logs': os.path.join(base_dir, 'logs')
    }
    
    # 引数に基づいてクリア対象を決定
    clear_all = args.all
    
    if clear_all or args.pdfs:
        logging.info("PDFファイルをクリアしています...")
        clear_directory(dirs['dl'])
    
    if clear_all or args.texts:
        logging.info("テキストファイルをクリアしています...")
        clear_directory(dirs['text'])
    
    if clear_all or args.summaries:
        logging.info("要約ファイルをクリアしています...")
        clear_directory(dirs['summary'])
    
    if clear_all or args.processed:
        logging.info("処理済み記録をクリアしています...")
        clear_directory(dirs['processed'])
    
    if clear_all or args.logs:
        logging.info("ログファイルをクリアしています...")
        clear_directory(dirs['logs'])
    
    # 引数が指定されていない場合は、ヘルプを表示
    if not (clear_all or args.pdfs or args.texts or args.summaries or args.processed or args.logs):
        parser.print_help()
    else:
        logging.info("クリア処理が完了しました。")
        print("クリア処理が完了しました。")

if __name__ == "__main__":
    main()