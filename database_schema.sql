-- 歯科カウンセリングAIツール データベーススキーマ
-- SQLite形式で設計（本格運用時はPostgreSQL等に移行可能）

-- 1. 予約情報テーブル
CREATE TABLE appointments (
    appointment_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    scheduled_datetime DATETIME NOT NULL,
    treatment_type TEXT,
    status TEXT DEFAULT 'scheduled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. カウンセリングセッションテーブル
CREATE TABLE counseling_sessions (
    session_id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    recording_start_time DATETIME NOT NULL,
    recording_end_time DATETIME,
    audio_file_path TEXT,
    device_id TEXT,
    session_status TEXT DEFAULT 'in_progress',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- 3. 会話記録テーブル（全発言を記録）
CREATE TABLE conversation_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    speaker TEXT NOT NULL, -- 'patient' or 'doctor'
    speaker_name TEXT,
    timestamp_start TEXT,
    timestamp_end TEXT,
    original_text TEXT NOT NULL,
    confidence_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- 4. SOAP記録テーブル
CREATE TABLE soap_records (
    soap_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    subjective_text TEXT,
    objective_text TEXT,
    assessment_text TEXT,
    plan_text TEXT,
    generation_method TEXT DEFAULT 'ai_generated', -- 'ai_generated' or 'manual'
    reviewed_by_doctor BOOLEAN DEFAULT FALSE,
    doctor_modifications TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- 5. 音声感情分析テーブル（将来機能）
CREATE TABLE emotion_analysis (
    analysis_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    record_id INTEGER,
    speaker TEXT NOT NULL,
    joy_score REAL DEFAULT 0,
    anger_score REAL DEFAULT 0,
    stress_score REAL DEFAULT 0,
    anxiety_score REAL DEFAULT 0,
    satisfaction_score REAL DEFAULT 0,
    confusion_score REAL DEFAULT 0,
    trust_score REAL DEFAULT 0,
    hesitation_score REAL DEFAULT 0,
    overall_sentiment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id),
    FOREIGN KEY (record_id) REFERENCES conversation_records(record_id)
);

-- 6. システムログテーブル
CREATE TABLE system_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    log_level TEXT NOT NULL, -- 'INFO', 'WARNING', 'ERROR'
    component TEXT NOT NULL, -- 'audio_processing', 'ai_conversion', 'database'
    message TEXT NOT NULL,
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- インデックス作成（検索性能向上）
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_datetime ON appointments(scheduled_datetime);

CREATE INDEX idx_sessions_patient ON counseling_sessions(patient_id);
CREATE INDEX idx_sessions_doctor ON counseling_sessions(doctor_id);
CREATE INDEX idx_sessions_datetime ON counseling_sessions(recording_start_time);

CREATE INDEX idx_conversation_session ON conversation_records(session_id);
CREATE INDEX idx_conversation_speaker ON conversation_records(speaker);

CREATE INDEX idx_soap_session ON soap_records(session_id);
CREATE INDEX idx_soap_reviewed ON soap_records(reviewed_by_doctor);

-- サンプルデータ挿入
INSERT INTO appointments VALUES 
('APT-001', 'P12345', '田中太郎', 'D001', '伊藤理事長', '2025-01-26 10:30:00', 'カウンセリング', 'scheduled', datetime('now'), datetime('now')),
('APT-002', 'P12346', '佐藤花子', 'D002', '原田医師', '2025-01-26 11:00:00', '定期検診', 'scheduled', datetime('now'), datetime('now')),
('APT-003', 'P12347', '山田次郎', 'D001', '伊藤理事長', '2025-01-26 14:00:00', 'インプラント相談', 'scheduled', datetime('now'), datetime('now')),
('APT-004', 'P12348', '鈴木美咲', 'D003', '田中医師', '2025-01-26 15:30:00', '矯正相談', 'scheduled', datetime('now'), datetime('now'));