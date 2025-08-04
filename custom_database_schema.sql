-- AIカスタム分析によるデータベース設計例
-- 元データにない情報をAIが生成してデータベースに保存

-- 基本セッション情報
CREATE TABLE counseling_sessions (
    session_id TEXT PRIMARY KEY,
    patient_name TEXT,
    doctor_name TEXT,
    session_date DATETIME,
    original_file_path TEXT
);

-- 元の会話データ
CREATE TABLE conversation_records (
    record_id TEXT PRIMARY KEY,
    session_id TEXT,
    speaker TEXT,
    original_text TEXT,
    timestamp_start TEXT,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成する感情分析データ（元データにはない）
CREATE TABLE ai_emotion_analysis (
    analysis_id TEXT PRIMARY KEY,
    session_id TEXT,
    patient_anxiety_level REAL,        -- AIが推定
    patient_trust_level REAL,          -- AIが推定
    doctor_empathy_score REAL,         -- AIが推定
    emotional_state TEXT,              -- AIが判断
    communication_comfort REAL,        -- AIが評価
    stress_indicators JSON,            -- AIが特定
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成する治療評価データ（元データにはない）
CREATE TABLE ai_treatment_assessment (
    assessment_id TEXT PRIMARY KEY,
    session_id TEXT,
    urgency_level REAL,                -- AIが判断
    pain_severity_estimated INTEGER,   -- AIが推定（1-10）
    treatment_complexity TEXT,         -- AIが評価
    patient_compliance_prediction REAL, -- AIが予測
    treatment_success_probability REAL, -- AIが予測
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成するリスク分析（元データにはない）
CREATE TABLE ai_risk_analysis (
    risk_id TEXT PRIMARY KEY,
    session_id TEXT,
    risk_factor TEXT,                  -- AIが特定
    risk_probability REAL,             -- AIが評価
    severity_level TEXT,               -- AIが判断
    mitigation_suggestion TEXT,        -- AIが提案
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成する満足度・成功予測（元データにはない）
CREATE TABLE ai_satisfaction_prediction (
    prediction_id TEXT PRIMARY KEY,
    session_id TEXT,
    satisfaction_score REAL,           -- AIが予測
    success_probability REAL,          -- AIが予測
    confidence_level REAL,             -- AIの予測信頼度
    key_factors JSON,                  -- AIが特定した要因
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成するフォローアップ提案（元データにはない）
CREATE TABLE ai_followup_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id TEXT,
    recommendation_type TEXT,          -- AIが分類
    recommendation_text TEXT,          -- AIが生成
    priority_level INTEGER,            -- AIが判断（1-5）
    estimated_timeframe TEXT,          -- AIが提案
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- AIが生成する臨床洞察（元データにはない）
CREATE TABLE ai_clinical_insights (
    insight_id TEXT PRIMARY KEY,
    session_id TEXT,
    patient_education_needs JSON,      -- AIが特定
    communication_style_preference TEXT, -- AIが分析
    decision_making_pattern TEXT,      -- AIが判断
    learning_preferences JSON,         -- AIが推定
    cultural_considerations JSON,      -- AIが考慮
    generated_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES counseling_sessions(session_id)
);

-- 検索・分析用のビュー
CREATE VIEW comprehensive_session_analysis AS
SELECT 
    cs.session_id,
    cs.patient_name,
    cs.doctor_name,
    cs.session_date,
    aea.patient_anxiety_level,
    aea.patient_trust_level,
    aea.emotional_state,
    ata.urgency_level,
    ata.pain_severity_estimated,
    ata.treatment_success_probability,
    asp.satisfaction_score,
    COUNT(afr.recommendation_id) as total_recommendations
FROM counseling_sessions cs
LEFT JOIN ai_emotion_analysis aea ON cs.session_id = aea.session_id
LEFT JOIN ai_treatment_assessment ata ON cs.session_id = ata.session_id
LEFT JOIN ai_satisfaction_prediction asp ON cs.session_id = asp.session_id
LEFT JOIN ai_followup_recommendations afr ON cs.session_id = afr.session_id
GROUP BY cs.session_id;