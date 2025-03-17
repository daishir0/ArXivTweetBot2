#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import PyPDF2
import logging

def extract_text_from_pdf(pdf_path, output_dir):
    """
    PDFからテキストを抽出し、テキストファイルに保存する
    
    Args:
        pdf_path (str): PDFファイルのパス
        output_dir (str): 出力先ディレクトリ
    
    Returns:
        str: 抽出したテキストを保存したファイルのパス
    """
    # ファイル名を取得（拡張子なし）
    filename = os.path.basename(pdf_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    # 出力ファイルパス
    output_path = os.path.join(output_dir, f"{filename_without_ext}.txt")
    
    try:
        # PDFファイルを開く
        logging.info(f"PDFファイルを開いています: {pdf_path}")
        import time
        start_time = time.time()
        
        with open(pdf_path, 'rb') as file:
            # PDFReaderオブジェクトを作成
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            logging.info(f"PDFファイルを読み込みました（ページ数: {num_pages}ページ）")
            
            # テキストを抽出
            logging.info(f"PDFからテキストを抽出中...")
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n\n"
                if (i + 1) % 10 == 0 or i + 1 == num_pages:
                    logging.info(f"  {i + 1}/{num_pages}ページ処理完了")
            
            text_length = len(text)
            logging.info(f"テキスト抽出完了（文字数: {text_length}文字）")
            
            # テキストファイルに保存
            logging.info(f"抽出したテキストをファイルに保存中: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text)
            
            end_time = time.time()
            processing_time = end_time - start_time
            logging.info(f"テキスト抽出・保存完了: {pdf_path} -> {output_path}（所要時間: {processing_time:.2f}秒）")
            return output_path
    
    except Exception as e:
        logging.error(f"テキスト抽出エラー: {pdf_path} - {str(e)}")
        return None