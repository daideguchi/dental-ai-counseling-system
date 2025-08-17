from http.server import BaseHTTPRequestHandler
import json
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
import re

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Parse multipart form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Extract XLSX file from multipart data
            xlsx_data = self.extract_xlsx_from_multipart(post_data)
            
            if not xlsx_data:
                raise Exception("XLSX file not found in request")
                
            # Parse XLSX content
            text_content = self.parse_xlsx_content(xlsx_data)
            
            response = {
                "status": "success",
                "text_content": text_content,
                "message": f"XLSX解析完了: {len(text_content)}文字の会話データを抽出"
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "error": str(e),
                "message": "XLSX解析に失敗しました"
            }
            
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def extract_xlsx_from_multipart(self, post_data):
        """Extract XLSX file from multipart form data"""
        try:
            # Simple multipart boundary extraction
            boundary_match = re.search(rb'boundary=([^\r\n]+)', post_data[:500])
            if not boundary_match:
                return None
                
            boundary = boundary_match.group(1)
            parts = post_data.split(b'--' + boundary)
            
            for part in parts:
                if b'filename=' in part and b'.xlsx' in part:
                    # Extract file content after headers
                    header_end = part.find(b'\r\n\r\n')
                    if header_end != -1:
                        return part[header_end + 4:]
            
            return None
        except Exception:
            return None
    
    def parse_xlsx_content(self, xlsx_data):
        """Parse XLSX file and extract conversation text"""
        try:
            with zipfile.ZipFile(BytesIO(xlsx_data), 'r') as zip_file:
                # Read shared strings
                shared_strings = []
                try:
                    with zip_file.open('xl/sharedStrings.xml') as shared_strings_file:
                        shared_strings_tree = ET.parse(shared_strings_file)
                        for si in shared_strings_tree.getroot():
                            t_element = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                            if t_element is not None:
                                shared_strings.append(t_element.text or '')
                except:
                    shared_strings = []
                
                # Read worksheet
                with zip_file.open('xl/worksheets/sheet1.xml') as worksheet_file:
                    worksheet_tree = ET.parse(worksheet_file)
                    
                    conversations = []
                    
                    for row in worksheet_tree.getroot().findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                        row_data = []
                        
                        for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            cell_value = ''
                            v_element = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            
                            if v_element is not None:
                                cell_type = cell.get('t', '')
                                if cell_type == 's':  # Shared string
                                    try:
                                        string_index = int(v_element.text)
                                        if 0 <= string_index < len(shared_strings):
                                            cell_value = shared_strings[string_index]
                                    except (ValueError, IndexError):
                                        cell_value = v_element.text or ''
                                else:
                                    cell_value = v_element.text or ''
                            
                            row_data.append(cell_value)
                        
                        # Skip header row and empty rows
                        if len(row_data) >= 2 and row_data[0] not in ['話者', 'Speaker', 'Start Time']:
                            speaker = row_data[0] if len(row_data) > 0 else ''
                            text = row_data[1] if len(row_data) > 1 else ''
                            
                            if speaker and text:
                                conversations.append(f"{speaker}: {text}")
                    
                    return '\n'.join(conversations)
        
        except Exception as e:
            raise Exception(f"XLSX解析エラー: {str(e)}")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()