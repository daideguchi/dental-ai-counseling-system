"""
FastAPI メインアプリケーション
RESTful APIエンドポイントの定義
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import os
from datetime import datetime

# 内部モジュールのインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_processor import DataProcessor
from core.patient_matcher import PatientMatcher
from core.soap_generator import SOAPGenerator, SOAPFormatter
from database.models import DatabaseManager

app = FastAPI(
    title="歯科カウンセリング音声記録AIツール",
    description="音声記録からSOAP形式カルテを自動生成するAPI",
    version="1.0.0"
)

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# グローバルインスタンス
data_processor = DataProcessor()
patient_matcher = PatientMatcher()
soap_generator = SOAPGenerator()
soap_formatter = SOAPFormatter()
db_manager = DatabaseManager()

# データベース初期化
db_manager.create_tables()


# Pydanticモデル
class SessionStartRequest(BaseModel):
    doctor_id: str
    appointment_csv_path: Optional[str] = None


class SessionStopRequest(BaseModel):
    session_id: str


class SOAPUpdateRequest(BaseModel):
    session_id: str
    soap_note: Dict[str, str]
    confidence_score: Optional[float] = None


class OutcomeRequest(BaseModel):
    session_id: str
    outcome_type: str  # contracted, declined, pending
    contract_amount: Optional[float] = 0.0
    follow_up_scheduled: Optional[bool] = False
    notes: Optional[str] = ""


# APIエンドポイント

@app.get("/", response_class=HTMLResponse)
async def root():
    """ルートページ - Web UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>歯科カウンセリング音声記録AIツール</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .button:hover { background: #0056b3; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            textarea { width: 100%; height: 200px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>歯科カウンセリング音声記録AIツール</h1>
            
            <div class="section">
                <h2>録音制御</h2>
                <input type="text" id="doctorId" placeholder="医師ID (例: D001)" style="margin: 5px;">
                <br>
                <button class="button" onclick="startRecording()">録音開始</button>
                <button class="button" onclick="stopRecording()">録音停止</button>
                <div id="recordingStatus" class="status"></div>
            </div>
            
            <div class="section">
                <h2>ファイルアップロード</h2>
                <input type="file" id="audioFile" accept=".txt,.csv,.docx,.mp3,.wav">
                <button class="button" onclick="uploadFile()">ファイル処理</button>
                <div id="uploadStatus" class="status"></div>
            </div>
            
            <div class="section">
                <h2>SOAP確認・編集</h2>
                <textarea id="soapContent" placeholder="SOAP形式のカルテがここに表示されます"></textarea>
                <button class="button" onclick="updateSOAP()">SOAP更新</button>
                <button class="button" onclick="submitToRececon()">レセコンに送信</button>
                <div id="soapStatus" class="status"></div>
            </div>
            
            <div class="section">
                <h2>セッション一覧</h2>
                <button class="button" onclick="loadSessions()">セッション読み込み</button>
                <div id="sessionsList"></div>
            </div>
        </div>
        
        <script>
            let currentSessionId = null;
            
            async function startRecording() {
                const doctorId = document.getElementById('doctorId').value;
                if (!doctorId) {
                    alert('医師IDを入力してください');
                    return;
                }
                
                try {
                    const response = await fetch('/api/sessions/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({doctor_id: doctorId})
                    });
                    
                    const result = await response.json();
                    currentSessionId = result.session_id;
                    
                    document.getElementById('recordingStatus').innerHTML = 
                        `<div class="success">録音開始: ${result.session_id}</div>`;
                } catch (error) {
                    document.getElementById('recordingStatus').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            async function stopRecording() {
                if (!currentSessionId) {
                    alert('録音セッションが開始されていません');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/sessions/stop/${currentSessionId}`, {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('recordingStatus').innerHTML = 
                        `<div class="success">録音停止・処理完了</div>`;
                    
                    // SOAP表示
                    if (result.soap_note) {
                        displaySOAP(result);
                    }
                } catch (error) {
                    document.getElementById('recordingStatus').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            async function uploadFile() {
                const fileInput = document.getElementById('audioFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('ファイルを選択してください');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('doctor_id', document.getElementById('doctorId').value || 'D001');
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    currentSessionId = result.session_id;
                    
                    document.getElementById('uploadStatus').innerHTML = 
                        `<div class="success">ファイル処理完了</div>`;
                    
                    // SOAP表示
                    if (result.soap_note) {
                        displaySOAP(result);
                    }
                } catch (error) {
                    document.getElementById('uploadStatus').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            function displaySOAP(data) {
                const soapText = formatSOAPForDisplay(data.soap_note);
                document.getElementById('soapContent').value = soapText;
            }
            
            function formatSOAPForDisplay(soapNote) {
                return `S（主観的情報）：
${soapNote.S}

O（客観的情報）：
${soapNote.O}

A（評価・診断）：
${soapNote.A}

P（計画）：
${soapNote.P}`;
            }
            
            async function updateSOAP() {
                if (!currentSessionId) {
                    alert('セッションが選択されていません');
                    return;
                }
                
                const soapText = document.getElementById('soapContent').value;
                const soapNote = parseSOAPFromText(soapText);
                
                try {
                    const response = await fetch('/api/sessions/soap', {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            session_id: currentSessionId,
                            soap_note: soapNote
                        })
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('soapStatus').innerHTML = 
                        `<div class="success">SOAP更新完了</div>`;
                } catch (error) {
                    document.getElementById('soapStatus').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            function parseSOAPFromText(text) {
                const sections = text.split(/[SOAP]（[^）]+）：/);
                return {
                    S: sections[1] ? sections[1].trim() : '',
                    O: sections[2] ? sections[2].trim() : '',
                    A: sections[3] ? sections[3].trim() : '',
                    P: sections[4] ? sections[4].trim() : ''
                };
            }
            
            async function submitToRececon() {
                if (!currentSessionId) {
                    alert('セッションが選択されていません');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/sessions/${currentSessionId}/submit-to-rececon`, {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('soapStatus').innerHTML = 
                        `<div class="success">レセコン送信完了（実際の送信は未実装）</div>`;
                } catch (error) {
                    document.getElementById('soapStatus').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            async function loadSessions() {
                const doctorId = document.getElementById('doctorId').value || 'D001';
                
                try {
                    const response = await fetch(`/api/sessions?doctor_id=${doctorId}`);
                    const sessions = await response.json();
                    
                    let html = '<h3>最近のセッション</h3>';
                    sessions.forEach(session => {
                        html += `<div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
                            <strong>ID:</strong> ${session.id}<br>
                            <strong>患者ID:</strong> ${session.patient_id}<br>
                            <strong>開始時刻:</strong> ${session.start_time}<br>
                            <strong>ステータス:</strong> ${session.status}<br>
                            <button onclick="loadSession('${session.id}')">読み込み</button>
                        </div>`;
                    });
                    
                    document.getElementById('sessionsList').innerHTML = html;
                } catch (error) {
                    document.getElementById('sessionsList').innerHTML = 
                        `<div class="error">エラー: ${error.message}</div>`;
                }
            }
            
            async function loadSession(sessionId) {
                try {
                    const response = await fetch(`/api/sessions/${sessionId}`);
                    const session = await response.json();
                    
                    currentSessionId = sessionId;
                    if (session.soap_note) {
                        displaySOAP(session);
                    }
                } catch (error) {
                    alert(`セッション読み込みエラー: ${error.message}`);
                }
            }
        </script>
    </body>
    </html>
    """


@app.post("/api/sessions/start")
async def start_session(request: SessionStartRequest):
    """録音セッション開始"""
    try:
        session_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # セッションデータの初期化
        session_data = {
            'recording_id': session_id,
            'doctor_id': request.doctor_id,
            'start_time': datetime.now().isoformat(),
            'status': 'recording'
        }
        
        # データベースに保存
        db_manager.save_counseling_session(session_data)
        
        return {
            'status': 'success',
            'session_id': session_id,
            'message': '録音を開始しました'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/stop/{session_id}")
async def stop_session(session_id: str):
    """録音セッション停止・処理実行"""
    try:
        # セッション情報を取得
        session = db_manager.get_counseling_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # ダミーの文字起こしデータ（実際の実装では音声ファイルから生成）
        transcript_data = {
            'recording_id': session_id,
            'transcript': '''患者: おはようございます。右上の奥歯が痛くて来ました。
医師: おはようございます。いつ頃からの痛みでしょうか？
患者: 2週間くらい前からです。冷たいものを飲むとしみるんです。
医師: そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。''',
            'speaker_segments': [
                {'speaker': 'patient', 'text': 'おはようございます。右上の奥歯が痛くて来ました。'},
                {'speaker': 'doctor', 'text': 'おはようございます。いつ頃からの痛みでしょうか？'},
                {'speaker': 'patient', 'text': '2週間くらい前からです。冷たいものを飲むとしみるんです。'},
                {'speaker': 'doctor', 'text': 'そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。'}
            ]
        }
        
        # SOAP生成
        soap_result = soap_generator.generate_soap(transcript_data)
        
        # データベース更新
        db_manager.update_soap_note(
            session_id, 
            soap_result['soap_note'], 
            soap_result['confidence_score']
        )
        
        return {
            'status': 'success',
            'session_id': session_id,
            'soap_note': soap_result['soap_note'],
            'confidence_score': soap_result['confidence_score'],
            'message': '録音停止・SOAP生成完了'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), doctor_id: str = Form("D001")):
    """ファイルアップロード・処理"""
    try:
        # ファイル保存
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # データ処理
        processed_data = data_processor.process_file(file_path)
        processed_data['doctor_id'] = doctor_id
        
        # 患者特定（予約データがある場合）
        appointments_csv = "sample_appointments.csv"
        if os.path.exists(appointments_csv):
            match_result = patient_matcher.match_patient_doctor(processed_data, appointments_csv)
            if match_result['status'] == 'matched':
                processed_data.update({
                    'patient_id': match_result['patient_id'],
                    'appointment_id': match_result['appointment_id']
                })
        
        # SOAP生成
        soap_result = soap_generator.generate_soap(processed_data)
        
        # データベース保存
        session_data = {
            'recording_id': processed_data['recording_id'],
            'patient_id': processed_data.get('patient_id'),
            'doctor_id': doctor_id,
            'appointment_id': processed_data.get('appointment_id'),
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'audio_file_path': file_path,
            'transcript': processed_data['transcript'],
            'soap_note': soap_result['soap_note'],
            'confidence_score': soap_result['confidence_score'],
            'status': 'completed'
        }
        
        session_id = db_manager.save_counseling_session(session_data)
        
        return {
            'status': 'success',
            'session_id': session_id,
            'soap_note': soap_result['soap_note'],
            'confidence_score': soap_result['confidence_score'],
            'patient_match': processed_data.get('patient_id') is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """セッション詳細取得"""
    session = db_manager.get_counseling_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    return session


@app.get("/api/sessions")
async def get_sessions(doctor_id: str = "D001", limit: int = 10):
    """セッション一覧取得"""
    sessions = db_manager.get_sessions_by_doctor(doctor_id, limit)
    return sessions


@app.put("/api/sessions/soap")
async def update_soap(request: SOAPUpdateRequest):
    """SOAP更新"""
    try:
        success = db_manager.update_soap_note(
            request.session_id, 
            request.soap_note, 
            request.confidence_score
        )
        
        if success:
            return {'status': 'success', 'message': 'SOAP更新完了'}
        else:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/submit-to-rececon")
async def submit_to_rececon(session_id: str):
    """レセコンへの送信（ダミー実装）"""
    try:
        session = db_manager.get_counseling_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # レセコン用フォーマット生成
        rececon_format = soap_formatter.format_for_rececon({
            'soap_note': session['soap_note'],
            'confidence_score': session['confidence_score']
        })
        
        # 実際の実装では、ここでレセコンAPIを呼び出すか、CSVファイルを生成
        print("レセコン送信データ:")
        print(rececon_format)
        
        return {
            'status': 'success',
            'message': 'レセコンに送信しました（ダミー実装）',
            'rececon_format': rececon_format
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outcomes")
async def save_outcome(request: OutcomeRequest):
    """カウンセリング結果保存"""
    try:
        outcome_data = {
            'session_id': request.session_id,
            'outcome_type': request.outcome_type,
            'contract_amount': request.contract_amount,
            'follow_up_scheduled': request.follow_up_scheduled,
            'notes': request.notes
        }
        
        outcome_id = db_manager.save_counseling_outcome(outcome_data)
        
        return {
            'status': 'success',
            'outcome_id': outcome_id,
            'message': '結果を保存しました'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics(doctor_id: Optional[str] = None):
    """統計情報取得"""
    stats = db_manager.get_outcome_statistics(doctor_id)
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)