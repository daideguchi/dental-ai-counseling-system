#!/usr/bin/env python3
"""
簡易XLSX解析モジュール - 外部依存なし
XLSXファイルからテキストコンテンツを抽出します。
openpyxl等の外部ライブラリが利用できない環境での代替実装。
"""

import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import List, Dict, Any, Optional
import re


class SimpleXLSXParser:
    """シンプルなXLSX解析クラス（外部依存なし）"""
    
    def __init__(self, file_content: bytes):
        """XLSXファイルの内容を受け取って初期化"""
        self.file_content = file_content
        self.shared_strings = []
        self.sheets_data = {}
    
    def parse(self) -> Dict[str, Any]:
        """XLSXファイルを解析してテキスト内容を抽出"""
        try:
            with zipfile.ZipFile(BytesIO(self.file_content), 'r') as xlsx_zip:
                # 共有文字列テーブルを読み込み
                self._load_shared_strings(xlsx_zip)
                
                # ワークシート一覧を取得
                sheets = self._get_sheet_list(xlsx_zip)
                
                # 各シートのデータを抽出
                all_text_content = []
                for sheet_name, sheet_path in sheets.items():
                    sheet_text = self._extract_sheet_text(xlsx_zip, sheet_path)
                    if sheet_text:
                        all_text_content.extend(sheet_text)
                
                # 結果をまとめて返す
                return {
                    "success": True,
                    "text_content": "\n".join(all_text_content),
                    "line_count": len(all_text_content),
                    "sheets_found": len(sheets),
                    "extraction_method": "simple_zip_xml_parsing"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text_content": "",
                "line_count": 0,
                "sheets_found": 0,
                "extraction_method": "failed"
            }
    
    def _load_shared_strings(self, xlsx_zip: zipfile.ZipFile):
        """共有文字列テーブルを読み込み"""
        try:
            shared_strings_xml = xlsx_zip.read('xl/sharedStrings.xml')
            root = ET.fromstring(shared_strings_xml)
            
            # 名前空間を考慮した要素検索
            for si in root.iter():
                if 't' in si.tag:  # <t>要素（テキスト）
                    text = si.text or ""
                    if text.strip():
                        self.shared_strings.append(text.strip())
                        
        except (KeyError, ET.ParseError):
            # sharedStrings.xmlが存在しない、または解析できない場合
            self.shared_strings = []
    
    def _get_sheet_list(self, xlsx_zip: zipfile.ZipFile) -> Dict[str, str]:
        """ワークシート一覧を取得"""
        sheets = {}
        try:
            workbook_xml = xlsx_zip.read('xl/workbook.xml')
            root = ET.fromstring(workbook_xml)
            
            # ワークシート情報を抽出
            for sheet in root.iter():
                if 'sheet' in sheet.tag.lower():
                    name = sheet.get('name', 'Sheet')
                    sheet_id = sheet.get('sheetId', '1')
                    sheets[name] = f'xl/worksheets/sheet{sheet_id}.xml'
                    
        except (KeyError, ET.ParseError):
            # デフォルトでSheet1を試す
            sheets['Sheet1'] = 'xl/worksheets/sheet1.xml'
            
        return sheets
    
    def _extract_sheet_text(self, xlsx_zip: zipfile.ZipFile, sheet_path: str) -> List[str]:
        """個別シートからテキストを抽出"""
        try:
            sheet_xml = xlsx_zip.read(sheet_path)
            root = ET.fromstring(sheet_xml)
            
            extracted_text = []
            
            # セル内容を順次処理
            for cell in root.iter():
                if 'c' in cell.tag:  # <c>要素（セル）
                    cell_text = self._extract_cell_text(cell)
                    if cell_text and cell_text.strip():
                        extracted_text.append(cell_text.strip())
            
            return extracted_text
            
        except (KeyError, ET.ParseError):
            return []
    
    def _extract_cell_text(self, cell_element) -> str:
        """個別セルからテキストを抽出"""
        cell_type = cell_element.get('t', '')
        
        # 値要素を探す
        for child in cell_element:
            if 'v' in child.tag:  # <v>要素（値）
                value = child.text or ""
                
                # 共有文字列参照の場合
                if cell_type == 's':
                    try:
                        index = int(value)
                        if 0 <= index < len(self.shared_strings):
                            return self.shared_strings[index]
                    except (ValueError, IndexError):
                        pass
                
                # 直接値の場合
                return value
        
        return ""


def parse_xlsx_file(file_content: bytes) -> Dict[str, Any]:
    """XLSXファイルを解析してテキスト内容を返す"""
    parser = SimpleXLSXParser(file_content)
    return parser.parse()


def format_as_conversation(xlsx_result: Dict[str, Any]) -> str:
    """XLSX解析結果を会話形式に整形"""
    if not xlsx_result.get("success", False):
        return f"XLSX解析エラー: {xlsx_result.get('error', '不明なエラー')}"
    
    text_content = xlsx_result.get("text_content", "")
    if not text_content.strip():
        return "XLSXファイルからテキストコンテンツを抽出できませんでした。"
    
    # 基本的な整形（行ごとに分割し、空行を除去）
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
    # 会話っぽい形式に変換する簡単な処理
    formatted_lines = []
    for line in lines:
        # 時刻らしきパターンがある場合は発話者として扱う
        if re.match(r'\d{1,2}:\d{2}', line) or '：' in line or ':' in line:
            formatted_lines.append(line)
        else:
            # 内容が短すぎる場合はスキップ
            if len(line) > 2:
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines) if formatted_lines else text_content