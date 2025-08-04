// モダンJavaScript - 歯科カウンセリングAIツール

// グローバル変数
let currentStep = 1;
let selectedTool = null;
let uploadedFiles = [];
let appointmentData = [];
let currentSessionData = null;
let editMode = false;

// DOM要素の取得
const DOM = {
    // ファイル入力
    plaudFiles: () => document.getElementById('plaud-files'),
    nottaFiles: () => document.getElementById('notta-files'),
    
    // ファイルリスト
    plaudFileList: () => document.getElementById('plaud-file-list'),
    nottaFileList: () => document.getElementById('notta-file-list'),
    
    // ボタン
    processBtn: () => document.getElementById('process-files'),
    saveBtn: () => document.getElementById('save-soap'),
    
    // ステップ関連
    stepContents: () => document.querySelectorAll('.step-content'),
    stepIndicators: () => document.querySelectorAll('.step'),
    
    // 処理状況表示
    processSteps: () => document.querySelectorAll('.process-step'),
    statusIndicators: () => document.querySelectorAll('.status-indicator'),
    progressFill: () => document.getElementById('progress-fill'),
    progressText: () => document.getElementById('progress-text'),
    
    // 結果表示
    patientName: () => document.getElementById('patient-name'),
    doctorName: () => document.getElementById('doctor-name'),
    sessionDate: () => document.getElementById('session-date'),
    sourceTool: () => document.getElementById('source-tool'),
    
    // SOAP表示
    soapElements: () => ({
        s: { display: document.getElementById('soap-s-display'), input: document.getElementById('soap-s') },
        o: { display: document.getElementById('soap-o-display'), input: document.getElementById('soap-o') },
        a: { display: document.getElementById('soap-a-display'), input: document.getElementById('soap-a') },
        p: { display: document.getElementById('soap-p-display'), input: document.getElementById('soap-p') }
    }),
    
    // 分析結果
    communicationScore: () => document.getElementById('communication-score'),
    understandingScore: () => document.getElementById('understanding-score'),
    consentScore: () => document.getElementById('consent-score'),
    improvementList: () => document.getElementById('improvement-list'),
    positiveList: () => document.getElementById('positive-list'),
    
    // その他
    rawDataDisplay: () => document.getElementById('raw-data-display'),
    formatInfo: () => document.getElementById('format-info'),
    historySidebar: () => document.getElementById('history-sidebar'),
    historyList: () => document.getElementById('history-list'),
    loadingOverlay: () => document.getElementById('loading-overlay'),
    loadingMessage: () => document.getElementById('loading-message'),
    saveSummary: () => document.getElementById('save-summary')
};

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    bindEvents();
    loadHistory();
});

// アプリケーション初期化
function initializeApp() {
    // 初期ステップの設定
    showStep(1);
    
    // ボタンの初期状態
    if (DOM.processBtn()) DOM.processBtn().disabled = true;
    if (DOM.saveBtn()) DOM.saveBtn().disabled = true;
    
    console.log('🚀 歯科カウンセリングAIツール初期化完了');
}

// イベントバインディング
function bindEvents() {
    // ファイル選択イベント
    if (DOM.plaudFiles()) {
        DOM.plaudFiles().addEventListener('change', () => handleFileSelect('plaud'));
    }
    if (DOM.nottaFiles()) {
        DOM.nottaFiles().addEventListener('change', () => handleFileSelect('notta'));
    }
    
    // ボタンイベント
    if (DOM.processBtn()) {
        DOM.processBtn().addEventListener('click', startProcessing);
    }
    if (DOM.saveBtn()) {
        DOM.saveBtn().addEventListener('click', saveToDatabase);
    }
    
    // UI制御ボタン
    const formatInfoBtn = document.getElementById('format-info-btn');
    if (formatInfoBtn) {
        formatInfoBtn.addEventListener('click', toggleFormatInfo);
    }
    
    const editModeBtn = document.getElementById('edit-mode-btn');
    if (editModeBtn) {
        editModeBtn.addEventListener('click', toggleEditMode);
    }
    
    const rawDataToggle = document.getElementById('raw-data-toggle');
    if (rawDataToggle) {
        rawDataToggle.addEventListener('click', toggleRawData);
    }
    
    const resetAppBtn = document.getElementById('reset-app-btn');
    if (resetAppBtn) {
        resetAppBtn.addEventListener('click', resetApp);
    }
    
    const newProcessBtn = document.getElementById('new-process-btn');
    if (newProcessBtn) {
        newProcessBtn.addEventListener('click', resetApp);
    }
    
    const showHistoryBtn = document.getElementById('show-history-btn');
    if (showHistoryBtn) {
        showHistoryBtn.addEventListener('click', showHistory);
    }
    
    const closeHistoryBtn = document.getElementById('close-history-btn');
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', hideHistory);
    }
    
    // 予約データ読み込み（オプション機能）
    const appointmentCsv = document.getElementById('appointment-csv');
    const loadAppointmentsBtn = document.getElementById('load-appointments');
    if (appointmentCsv && loadAppointmentsBtn) {
        loadAppointmentsBtn.addEventListener('click', () => appointmentCsv.click());
        appointmentCsv.addEventListener('change', loadAppointments);
    }
}

// ファイル選択処理
function handleFileSelect(tool) {
    const files = tool === 'plaud' ? DOM.plaudFiles().files : DOM.nottaFiles().files;
    uploadedFiles = Array.from(files);
    selectedTool = tool;
    
    // ファイルリスト表示
    displayFileList(tool);
    
    // 処理ボタンの状態更新
    DOM.processBtn().disabled = uploadedFiles.length === 0;
    
    // 他のツールの選択をクリア
    if (tool === 'plaud') {
        DOM.nottaFiles().value = '';
        DOM.nottaFileList().innerHTML = '';
    } else {
        DOM.plaudFiles().value = '';
        DOM.plaudFileList().innerHTML = '';
    }
    
    console.log(`📁 ${tool}ファイル選択:`, uploadedFiles.map(f => f.name));
}

// ファイルリスト表示
function displayFileList(tool) {
    const listElement = tool === 'plaud' ? DOM.plaudFileList() : DOM.nottaFileList();
    listElement.innerHTML = '';
    
    uploadedFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <span>${file.name}</span>
            <small>(${formatFileSize(file.size)})</small>
        `;
        listElement.appendChild(div);
    });
}

// ファイルサイズフォーマット
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 処理開始
async function startProcessing() {
    if (uploadedFiles.length === 0) return;
    
    console.log('🤖 AI処理開始');
    
    // ステップ2（処理中）に移動
    showStep(2);
    
    try {
        // ファイル内容読み込み
        const fileContent = await readFileContent(uploadedFiles[0]);
        
        // 処理の可視化
        await visualizeProcessing(fileContent);
        
        // 実際のAI処理
        const result = await processWithAI(fileContent, uploadedFiles[0]);
        
        // 結果保存
        currentSessionData = result;
        
        // ステップ3（結果表示）に移動
        showStep(3);
        
        // 結果表示
        displayResults(result);
        
    } catch (error) {
        console.error('❌ 処理エラー:', error);
        alert(`処理中にエラーが発生しました: ${error.message}`);
        showStep(1);
    }
}

// 処理の可視化
async function visualizeProcessing(fileContent) {
    const steps = [
        { id: 1, name: 'ファイル解析', duration: 1000 },
        { id: 2, name: '患者・医師特定', duration: 1500 },
        { id: 3, name: 'SOAP変換', duration: 2000 },
        { id: 4, name: '品質分析', duration: 1000 }
    ];
    
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        
        // ステップをアクティブ化
        updateProcessStep(step.id, 'active', `${step.name}中...`);
        updateProgress((i / steps.length) * 100);
        
        // 処理時間をシミュレート
        await new Promise(resolve => setTimeout(resolve, step.duration));
        
        // ステップを完了
        updateProcessStep(step.id, 'completed', `${step.name}完了`);
        updateProgress(((i + 1) / steps.length) * 100);
    }
}

// 処理ステップ更新
function updateProcessStep(stepId, status, message) {
    const processStep = document.getElementById(`process-step-${stepId}`);
    const statusIndicator = document.getElementById(`status-${stepId}`);
    const statusText = document.getElementById(`step-${stepId}-status`);
    
    if (processStep) {
        processStep.className = `process-step ${status}`;
    }
    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${status}`;
    }
    if (statusText) {
        statusText.textContent = message;
    }
}

// プログレス更新
function updateProgress(percentage) {
    if (DOM.progressFill()) {
        DOM.progressFill().style.width = `${percentage}%`;
    }
    if (DOM.progressText()) {
        DOM.progressText().textContent = `${Math.round(percentage)}%`;
    }
}

// ファイル内容読み込み（改善版：エラー処理とファイル検証を強化）
async function readFileContent(file) {
    console.log('📖 ファイル読み込み開始:', { 
        name: file.name, 
        size: file.size, 
        type: file.type 
    });
    
    return new Promise((resolve, reject) => {
        // ファイルサイズチェック（10MB制限）
        if (file.size > 10 * 1024 * 1024) {
            reject(new Error('ファイルサイズが大きすぎます（10MB以下にしてください）'));
            return;
        }
        
        // 空ファイルチェック
        if (file.size === 0) {
            reject(new Error('空のファイルです'));
            return;
        }
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const content = e.target.result;
            
            // 内容検証
            if (!content || content.trim().length === 0) {
                reject(new Error('ファイル内容が空です'));
                return;
            }
            
            // 最小文字数チェック（意味のある内容があるか）
            if (content.trim().length < 10) {
                reject(new Error('ファイル内容が短すぎます（10文字以上必要）'));
                return;
            }
            
            console.log('✅ ファイル読み込み成功:', { 
                contentLength: content.length,
                firstChars: content.substring(0, 50) + '...'
            });
            
            resolve(content);
        };
        
        reader.onerror = function(error) {
            console.error('❌ ファイル読み込みエラー:', error);
            reject(new Error('ファイルの読み込みに失敗しました'));
        };
        
        reader.onabort = function() {
            console.error('❌ ファイル読み込み中断');
            reject(new Error('ファイル読み込みが中断されました'));
        };
        
        // エンコーディングを明示的に指定してテキストとして読み込み
        try {
            reader.readAsText(file, 'UTF-8');
        } catch (error) {
            console.error('❌ ファイルリーダー初期化エラー:', error);
            reject(new Error('ファイルリーダーの初期化に失敗しました'));
        }
    });
}

// AI処理（実際のファイル内容を解析）
async function processWithAI(fileContent, file) {
    console.log('🧠 AI解析開始:', file.name);
    
    // ファイル形式の判定
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const fileAnalysis = analyzeFileContent(fileContent, fileExtension, file.name);
    
    // 患者・医師特定（実際の内容から推定）
    const identification = identifyPatientDoctor(fileContent);
    
    // SOAP変換（実際の会話内容から生成）
    const soapResult = convertToSOAP(fileContent, fileAnalysis);
    
    // 品質分析
    const qualityAnalysis = analyzeQuality(fileContent, fileAnalysis);
    
    return {
        identification,
        soap: soapResult,
        quality: qualityAnalysis,
        fileAnalysis,
        sourceFile: {
            name: file.name,
            size: file.size,
            type: fileExtension,
            content: fileContent
        }
    };
}

// ファイル内容分析
function analyzeFileContent(content, extension, fileName) {
    const analysis = {
        format: extension.toUpperCase(),
        totalLines: content.split('\n').length,
        totalCharacters: content.length,
        speakers: [],
        conversations: [],
        timeStamps: [],
        structure: 'unknown'
    };
    
    if (extension === 'txt') {
        if (fileName.toLowerCase().includes('plaud') || content.includes('Speaker A') || content.includes('Speaker B')) {
            // PLAUD NOTE TXT形式
            analysis.structure = 'plaud_txt';
            analysis.speakers = extractPlaudSpeakers(content);
            analysis.conversations = parsePlaudConversation(content);
        } else if (content.includes('【発言者') || content.includes('[発言者')) {
            // Notta TXT形式
            analysis.structure = 'notta_txt';
            analysis.speakers = extractNottaTxtSpeakers(content);
            analysis.conversations = parseNottaTxtConversation(content);
        }
    } else if (extension === 'csv') {
        // Notta CSV形式
        analysis.structure = 'notta_csv';
        const parsed = parseNottaCSV(content);
        analysis.speakers = parsed.speakers;
        analysis.conversations = parsed.conversations;
        analysis.timeStamps = parsed.timeStamps;
    } else if (extension === 'srt') {
        // SRT形式
        analysis.structure = 'srt';
        const parsed = parseSRT(content);
        analysis.conversations = parsed.conversations;
        analysis.timeStamps = parsed.timeStamps;
    } else if (extension === 'md' || extension === 'markdown') {
        // PLAUD NOTE Markdown要約
        analysis.structure = 'plaud_markdown';
        analysis.conversations = parseMarkdownSummary(content);
    }
    
    return analysis;
}

// PLAUD NOTE話者抽出
function extractPlaudSpeakers(content) {
    const speakers = [];
    const speakerAMatches = (content.match(/Speaker A:/g) || []).length;
    const speakerBMatches = (content.match(/Speaker B:/g) || []).length;
    
    if (speakerAMatches > 0) speakers.push({ id: 'A', count: speakerAMatches, role: '医師' });
    if (speakerBMatches > 0) speakers.push({ id: 'B', count: speakerBMatches, role: '患者' });
    
    return speakers;
}

// PLAUD NOTE会話解析
function parsePlaudConversation(content) {
    const conversations = [];
    const lines = content.split('\n\n');
    
    lines.forEach((line, index) => {
        if (line.trim() && line.includes(':')) {
            const [speaker, ...textParts] = line.split(':');
            const text = textParts.join(':').trim();
            if (text) {
                conversations.push({
                    id: index,
                    speaker: speaker.trim(),
                    text: text,
                    role: speaker.includes('A') ? '医師' : '患者'
                });
            }
        }
    });
    
    return conversations;
}

// Notta TXT話者抽出（例として実装）
function extractNottaTxtSpeakers(content) {
    const speakers = [];
    const speakerMatches = content.match(/【発言者\d+】/g) || content.match(/\[発言者\d+\]/g) || [];
    
    const uniqueSpeakers = [...new Set(speakerMatches)];
    uniqueSpeakers.forEach((speaker, index) => {
        speakers.push({
            id: speaker,
            role: index === 0 ? '医師' : '患者'
        });
    });
    
    return speakers;
}

// Notta TXT会話解析（例として実装）
function parseNottaTxtConversation(content) {
    const conversations = [];
    const lines = content.split('\n');
    
    lines.forEach((line, index) => {
        const speakerMatch = line.match(/【発言者(\d+)】(.*)/) || line.match(/\[発言者(\d+)\](.*)/);
        if (speakerMatch) {
            conversations.push({
                id: index,
                speaker: `発言者${speakerMatch[1]}`,
                text: speakerMatch[2].trim(),
                role: speakerMatch[1] === '1' ? '医師' : '患者'
            });
        }
    });
    
    return conversations;
}

// Notta CSV解析
function parseNottaCSV(content) {
    const lines = content.trim().split('\n');
    const headers = lines[0].split(',');
    const conversations = [];
    const speakers = new Set();
    const timeStamps = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        if (values.length >= 5) {
            const speaker = values[0];
            const startTime = values[1];
            const endTime = values[2];
            const text = values[4];
            
            speakers.add(speaker);
            timeStamps.push({ start: startTime, end: endTime });
            conversations.push({
                id: i - 1,
                speaker: speaker,
                text: text,
                startTime: startTime,
                endTime: endTime,
                role: speaker === 'Speaker 1' ? '医師' : '患者'
            });
        }
    }
    
    return {
        speakers: Array.from(speakers).map(s => ({ id: s, role: s === 'Speaker 1' ? '医師' : '患者' })),
        conversations,
        timeStamps
    };
}

// SRT解析（例として実装）
function parseSRT(content) {
    const conversations = [];
    const timeStamps = [];
    const blocks = content.split('\n\n');
    
    blocks.forEach((block, index) => {
        const lines = block.trim().split('\n');
        if (lines.length >= 3) {
            const timeCode = lines[1];
            const text = lines.slice(2).join(' ');
            
            const timeParts = timeCode.split(' --> ');
            if (timeParts.length === 2) {
                timeStamps.push({ start: timeParts[0], end: timeParts[1] });
                conversations.push({
                    id: index,
                    speaker: `話者${(index % 2) + 1}`,
                    text: text,
                    role: (index % 2) === 0 ? '医師' : '患者',
                    startTime: timeParts[0],
                    endTime: timeParts[1]
                });
            }
        }
    });
    
    return { conversations, timeStamps };
}

// Markdown要約解析（例として実装）
function parseMarkdownSummary(content) {
    const conversations = [];
    const lines = content.split('\n');
    
    lines.forEach((line, index) => {
        if (line.startsWith('- ') || line.startsWith('* ')) {
            conversations.push({
                id: index,
                speaker: '要約',
                text: line.substring(2).trim(),
                role: 'summary'
            });
        }
    });
    
    return conversations;
}

// 患者・医師特定（実際の内容から）
function identifyPatientDoctor(content) {
    let patientName = '患者';
    let doctorName = '医師';
    let confidence = 0.5;
    
    // 名前パターンの検索
    const namePatterns = [
        /([一-龯]+)さん/g,
        /([一-龯]+)先生/g,
        /患者.*?([一-龯]+)/g,
        /医師.*?([一-龯]+)/g
    ];
    
    namePatterns.forEach(pattern => {
        const matches = content.match(pattern);
        if (matches) {
            matches.forEach(match => {
                if (match.includes('さん')) {
                    patientName = match.replace('さん', '');
                    confidence = Math.max(confidence, 0.8);
                } else if (match.includes('先生')) {
                    doctorName = match.replace('先生', '');
                    confidence = Math.max(confidence, 0.8);
                }
            });
        }
    });
    
    return {
        patient_name: patientName,
        doctor_name: doctorName,
        confidence_patient: confidence,
        confidence_doctor: confidence,
        reasoning: '会話内容から名前パターンを検出'
    };
}

// SOAP変換（改善版：より正確な分類と自然な文章生成）
function convertToSOAP(content, fileAnalysis) {
    const soap = { S: '', O: '', A: '', P: '' };
    
    // 拡張された歯科特有のキーワード分析
    const keywords = {
        subjective: {
            pain: ['痛い', '痛み', 'ズキズキ', 'ジンジン', 'チクチク', '激痛', '鈍痛'],
            sensitivity: ['しみる', 'キーン', '冷たい', '熱い', '甘い'],
            discomfort: ['違和感', '気になる', '不快', 'むずむず', 'ヒリヒリ'],
            swelling: ['腫れ', '腫れた', '膨らん', '腫脹'],
            other: ['噛めない', '口が開かない', '血が出る', '口臭', '味がしない']
        },
        objective: {
            dental: ['う蝕', 'C1', 'C2', 'C3', 'C4', 'カリエス', '虫歯', '穴'],
            periodontal: ['歯肉', '歯茎', '歯石', 'プラーク', '歯周病', '出血', 'BOP'],
            examination: ['打診痛', '冷水痛', '温熱痛', '咬合痛', '動揺', '変色', '破折'],
            radiographic: ['レントゲン', 'X線', '根尖', '骨吸収', '透過像']
        },
        assessment: {
            diagnosis: ['診断', '疑い', '所見', '判断'],
            condition: ['虫歯', '歯周病', '根尖病変', '咬合異常', '炎症', '感染', '壊死']
        },
        plan: {
            treatment: ['治療', '処置', '施術'],
            restorative: ['充填', 'CR', 'インレー', 'クラウン', 'ブリッジ'],
            surgical: ['抜歯', '外科', '切開', '縫合'],
            endodontic: ['根管治療', 'RCT', '根充', '感染根管治療'],
            periodontal: ['スケーリング', 'SRP', '歯周治療', 'PMTC'],
            other: ['予約', '経過観察', '再評価', 'メンテナンス']
        }
    };
    
    const conversations = fileAnalysis.conversations || [];
    console.log('🔍 SOAP変換開始:', { conversationCount: conversations.length });
    
    // より詳細な発言分類
    const categorizedContent = {
        subjective: new Set(),
        objective: new Set(),
        assessment: new Set(),
        plan: new Set()
    };
    
    // 患者の発言から主観的情報を抽出（症状の記述を重視）
    const patientStatements = conversations.filter(c => c.role === '患者');
    patientStatements.forEach(statement => {
        const text = statement.text;
        let hasSubjectiveKeyword = false;
        
        // 痛みの種類を詳細に分類
        Object.values(keywords.subjective).flat().forEach(keyword => {
            if (text.includes(keyword)) {
                categorizedContent.subjective.add(text);
                hasSubjectiveKeyword = true;
            }
        });
        
        // 患者の発言は基本的に主観的情報として扱う（10文字以上の意味のある発言）
        if (!hasSubjectiveKeyword && text.length > 10 && !text.includes('はい') && !text.includes('そうです')) {
            categorizedContent.subjective.add(text);
        }
    });
    
    // 医師の発言から客観的所見、評価、計画を抽出
    const doctorStatements = conversations.filter(c => c.role === '医師');
    doctorStatements.forEach(statement => {
        const text = statement.text;
        
        // 客観的所見（検査結果、観察事項）
        Object.values(keywords.objective).flat().forEach(keyword => {
            if (text.includes(keyword)) {
                categorizedContent.objective.add(text);
            }
        });
        
        // 評価・診断
        Object.values(keywords.assessment).flat().forEach(keyword => {
            if (text.includes(keyword)) {
                categorizedContent.assessment.add(text);
            }
        });
        
        // 治療計画
        Object.values(keywords.plan).flat().forEach(keyword => {
            if (text.includes(keyword)) {
                categorizedContent.plan.add(text);
            }
        });
    });
    
    // 自然な文章としてSOAP記録を生成
    soap.S = generateSubjective(Array.from(categorizedContent.subjective));
    soap.O = generateObjective(Array.from(categorizedContent.objective));
    soap.A = generateAssessment(Array.from(categorizedContent.assessment));
    soap.P = generatePlan(Array.from(categorizedContent.plan));
    
    const confidence = calculateConfidence(categorizedContent, conversations.length);
    
    console.log('✅ SOAP変換完了:', { 
        S_length: soap.S.length, 
        O_length: soap.O.length, 
        A_length: soap.A.length, 
        P_length: soap.P.length,
        confidence 
    });
    
    return {
        ...soap,
        confidence,
        key_points: [
            `総会話数: ${conversations.length}`,
            `患者発言: ${patientStatements.length}`,
            `医師発言: ${doctorStatements.length}`,
            `抽出した主観的情報: ${categorizedContent.subjective.size}件`,
            `抽出した客観的所見: ${categorizedContent.objective.size}件`
        ]
    };
}

// 主観的情報の文章生成
function generateSubjective(statements) {
    if (statements.length === 0) {
        return '患者からの特記すべき主観的症状の訴えなし。';
    }
    
    // 重複を除去し、意味のある内容を選択
    const uniqueStatements = [...new Set(statements)].filter(s => s.length > 5);
    const selected = uniqueStatements.slice(0, 3);
    
    return `患者の主訴: ${selected.join('。 ')}。`;
}

// 客観的所見の文章生成
function generateObjective(statements) {
    if (statements.length === 0) {
        return '口腔内診査において特記すべき異常所見なし。';
    }
    
    const uniqueStatements = [...new Set(statements)].filter(s => s.length > 5);
    const selected = uniqueStatements.slice(0, 4);
    
    return `口腔内所見: ${selected.join('。 ')}。`;
}

// 評価・診断の文章生成
function generateAssessment(statements) {
    if (statements.length === 0) {
        return '詳細な診査・診断が必要。';
    }
    
    const uniqueStatements = [...new Set(statements)].filter(s => s.length > 5);
    const selected = uniqueStatements.slice(0, 2);
    
    return `診断: ${selected.join('。 ')}。`;
}

// 治療計画の文章生成
function generatePlan(statements) {
    if (statements.length === 0) {
        return '治療方針については次回診察時に決定。経過観察継続。';
    }
    
    const uniqueStatements = [...new Set(statements)].filter(s => s.length > 5);
    const selected = uniqueStatements.slice(0, 3);
    
    return `治療計画: ${selected.join('。 ')}。`;
}

// 信頼度計算
function calculateConfidence(categorizedContent, totalConversations) {
    let confidence = 0.3; // 基本値
    
    // 会話数による加算
    if (totalConversations >= 10) confidence += 0.3;
    else if (totalConversations >= 5) confidence += 0.2;
    else confidence += 0.1;
    
    // 各SOAP要素の充実度による加算
    if (categorizedContent.subjective.size >= 2) confidence += 0.1;
    if (categorizedContent.objective.size >= 2) confidence += 0.1;
    if (categorizedContent.assessment.size >= 1) confidence += 0.1;
    if (categorizedContent.plan.size >= 1) confidence += 0.1;
    
    return Math.min(0.95, confidence); // 最大95%
}

// 品質分析
function analyzeQuality(content, fileAnalysis) {
    const conversations = fileAnalysis.conversations || [];
    const totalConversations = conversations.length;
    const patientCount = conversations.filter(c => c.role === '患者').length;
    const doctorCount = conversations.filter(c => c.role === '医師').length;
    
    // コミュニケーション品質の計算
    const communicationQuality = Math.min(0.95, (totalConversations / 10) * 0.8 + 0.2);
    
    // 患者理解度の計算（質問と回答のバランス）
    const balanceRatio = Math.min(patientCount, doctorCount) / Math.max(patientCount, doctorCount, 1);
    const patientUnderstanding = Math.min(0.95, balanceRatio * 0.7 + 0.3);
    
    // 治療同意可能性の計算
    const consentLikelihood = content.includes('分かりました') || content.includes('お願いします') ? 0.9 : 0.7;
    
    // 改善提案の生成
    const improvements = [];
    if (totalConversations < 5) improvements.push('より詳細な問診を行う');
    if (balanceRatio < 0.5) improvements.push('患者からの質問を促す');
    if (!content.includes('説明')) improvements.push('治療内容の詳細説明を追加');
    if (!content.includes('費用') && !content.includes('料金')) improvements.push('治療費用の説明を追加');
    
    // 良い点の抽出
    const positives = [];
    if (content.includes('丁寧')) positives.push('丁寧な対応');
    if (content.includes('説明')) positives.push('適切な説明');
    if (totalConversations >= 8) positives.push('十分な対話時間');
    if (content.includes('ありがとう')) positives.push('良好な関係性');
    
    return {
        communication_quality: communicationQuality,
        patient_understanding: patientUnderstanding,
        doctor_explanation: Math.min(0.95, doctorCount / totalConversations + 0.1),
        treatment_consent_likelihood: consentLikelihood,
        improvement_suggestions: improvements.length > 0 ? improvements : ['現在の対応は適切です'],
        positive_aspects: positives.length > 0 ? positives : ['基本的な診療が実施されています']
    };
}

// 結果表示
function displayResults(result) {
    // 基本情報
    DOM.patientName().textContent = result.identification.patient_name;
    DOM.doctorName().textContent = result.identification.doctor_name;
    DOM.sessionDate().textContent = new Date().toLocaleString('ja-JP');
    DOM.sourceTool().textContent = selectedTool === 'plaud' ? 'PLAUD NOTE' : 'Notta';
    
    // SOAP表示
    const soapElements = DOM.soapElements();
    soapElements.s.display.textContent = result.soap.S;
    soapElements.o.display.textContent = result.soap.O;
    soapElements.a.display.textContent = result.soap.A;
    soapElements.p.display.textContent = result.soap.P;
    
    soapElements.s.input.value = result.soap.S;
    soapElements.o.input.value = result.soap.O;
    soapElements.a.input.value = result.soap.A;
    soapElements.p.input.value = result.soap.P;
    
    // 分析結果表示
    DOM.communicationScore().textContent = `${Math.round(result.quality.communication_quality * 100)}%`;
    DOM.understandingScore().textContent = `${Math.round(result.quality.patient_understanding * 100)}%`;
    DOM.consentScore().textContent = `${Math.round(result.quality.treatment_consent_likelihood * 100)}%`;
    
    // 改善提案
    DOM.improvementList().innerHTML = '';
    result.quality.improvement_suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        li.textContent = suggestion;
        DOM.improvementList().appendChild(li);
    });
    
    // 良い点
    DOM.positiveList().innerHTML = '';
    result.quality.positive_aspects.forEach(aspect => {
        const li = document.createElement('li');
        li.textContent = aspect;
        DOM.positiveList().appendChild(li);
    });
    
    // 元データ表示
    displayRawData(result.sourceFile, result.fileAnalysis);
    
    // 保存ボタンを有効化
    DOM.saveBtn().disabled = false;
    
    console.log('✅ 結果表示完了');
}

// 元データ表示
function displayRawData(sourceFile, analysis) {
    const rawDataDisplay = DOM.rawDataDisplay();
    
    const analysisInfo = `
        <div class="raw-data-analysis">
            <h4>📊 ファイル分析結果</h4>
            <div class="analysis-grid">
                <div class="analysis-item">
                    <label>形式:</label>
                    <span>${analysis.format}</span>
                </div>
                <div class="analysis-item">
                    <label>構造:</label>
                    <span>${getStructureDescription(analysis.structure)}</span>
                </div>
                <div class="analysis-item">
                    <label>総行数:</label>
                    <span>${analysis.totalLines}行</span>
                </div>
                <div class="analysis-item">
                    <label>文字数:</label>
                    <span>${analysis.totalCharacters.toLocaleString()}文字</span>
                </div>
                <div class="analysis-item">
                    <label>会話数:</label>
                    <span>${analysis.conversations.length}回</span>
                </div>
                <div class="analysis-item">
                    <label>話者数:</label>
                    <span>${analysis.speakers.length}名</span>
                </div>
            </div>
        </div>
        <div class="raw-data-preview">
            <h4>📝 内容プレビュー</h4>
            <pre><code>${sourceFile.content.substring(0, 1000)}${sourceFile.content.length > 1000 ? '\n\n...(省略)' : ''}</code></pre>
        </div>
    `;
    
    rawDataDisplay.innerHTML = analysisInfo;
    
    // 追加のCSS適用
    rawDataDisplay.style.display = 'none'; // 初期は非表示
}

// 構造説明の取得
function getStructureDescription(structure) {
    const descriptions = {
        'plaud_txt': 'PLAUD NOTE TXT形式（Speaker A/B）',
        'notta_txt': 'Notta TXT形式（発言者ラベル）',
        'notta_csv': 'Notta CSV形式（タイムスタンプ付き）',
        'srt': 'SRT字幕形式',
        'plaud_markdown': 'PLAUD NOTE AI要約',
        'unknown': '不明な形式'
    };
    return descriptions[structure] || '不明な形式';
}

// データベース保存
function saveToDatabase() {
    if (!currentSessionData) return;
    
    const saveData = {
        session_info: {
            patient_name: currentSessionData.identification.patient_name,
            doctor_name: currentSessionData.identification.doctor_name,
            session_date: new Date().toISOString(),
            source_tool: selectedTool,
            file_name: currentSessionData.sourceFile.name,
            file_size: currentSessionData.sourceFile.size
        },
        soap_record: {
            subjective: currentSessionData.soap.S,
            objective: currentSessionData.soap.O,
            assessment: currentSessionData.soap.A,
            plan: currentSessionData.soap.P
        },
        quality_analysis: {
            communication_quality: currentSessionData.quality.communication_quality,
            patient_understanding: currentSessionData.quality.patient_understanding,
            consent_likelihood: currentSessionData.quality.treatment_consent_likelihood,
            improvement_suggestions: currentSessionData.quality.improvement_suggestions,
            positive_aspects: currentSessionData.quality.positive_aspects
        },
        file_analysis: currentSessionData.fileAnalysis
    };
    
    // 実際のAPIへの保存（ここではローカルストレージにシミュレート）
    const sessionId = generateSessionId();
    localStorage.setItem(`dental_session_${sessionId}`, JSON.stringify(saveData));
    
    // 保存完了の表示
    displaySaveSuccess(saveData);
    
    // ステップ4に移動
    showStep(4);
    
    // 履歴に追加
    addToHistory(saveData.session_info);
    
    console.log('💾 データベース保存完了:', sessionId);
}

// 保存成功表示
function displaySaveSuccess(saveData) {
    const summary = `
        <div class="save-details">
            <h4>保存された情報</h4>
            <ul>
                <li><strong>患者:</strong> ${saveData.session_info.patient_name}</li>
                <li><strong>医師:</strong> ${saveData.session_info.doctor_name}</li>
                <li><strong>SOAP記録:</strong> 4項目すべて保存</li>
                <li><strong>品質分析:</strong> ${saveData.quality_analysis.improvement_suggestions.length}件の改善提案</li>
                <li><strong>元ファイル:</strong> ${saveData.session_info.file_name}</li>
            </ul>
        </div>
    `;
    
    DOM.saveSummary().innerHTML = summary;
}

// セッションID生成
function generateSessionId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

// ステップ表示切り替え
function showStep(step) {
    currentStep = step;
    
    // すべてのステップコンテンツを非表示
    DOM.stepContents().forEach(content => {
        content.style.display = 'none';
    });
    
    // 指定されたステップを表示
    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.style.display = 'block';
    }
    
    // ステップインジケーターの更新
    DOM.stepIndicators().forEach((indicator, index) => {
        const stepNumber = index + 1;
        indicator.classList.remove('active', 'completed');
        
        if (stepNumber === step) {
            indicator.classList.add('active');
        } else if (stepNumber < step) {
            indicator.classList.add('completed');
        }
    });
    
    console.log(`📍 ステップ${step}に移動`);
}

// アプリリセット
function resetApp() {
    currentStep = 1;
    selectedTool = null;
    uploadedFiles = [];
    currentSessionData = null;
    editMode = false;
    
    // フォームリセット
    if (DOM.plaudFiles()) DOM.plaudFiles().value = '';
    if (DOM.nottaFiles()) DOM.nottaFiles().value = '';
    DOM.plaudFileList().innerHTML = '';
    DOM.nottaFileList().innerHTML = '';
    
    // ボタン状態リセット
    DOM.processBtn().disabled = true;
    DOM.saveBtn().disabled = true;
    
    // プログレスリセット
    updateProgress(0);
    
    // ステップ1に戻る
    showStep(1);
    
    console.log('🔄 アプリケーションリセット完了');
}

// 編集モード切り替え
function toggleEditMode() {
    editMode = !editMode;
    const soapElements = DOM.soapElements();
    
    Object.values(soapElements).forEach(element => {
        if (editMode) {
            element.display.style.display = 'none';
            element.input.style.display = 'block';
        } else {
            element.display.style.display = 'block';
            element.input.style.display = 'none';
            // 編集内容を表示に反映
            element.display.textContent = element.input.value;
        }
    });
    
    // 編集ボタンのテキスト更新
    const editBtn = document.querySelector('.edit-btn');
    if (editBtn) {
        editBtn.innerHTML = editMode ? 
            '<i class="fas fa-save"></i> 保存' : 
            '<i class="fas fa-edit"></i> 編集';
    }
}

// フォーマット情報表示切り替え
function toggleFormatInfo() {
    const formatInfo = DOM.formatInfo();
    if (formatInfo.style.display === 'none' || !formatInfo.style.display) {
        formatInfo.style.display = 'block';
    } else {
        formatInfo.style.display = 'none';
    }
}

// 元データ表示切り替え
function toggleRawData() {
    const rawDataDisplay = DOM.rawDataDisplay();
    if (rawDataDisplay.style.display === 'none' || !rawDataDisplay.style.display) {
        rawDataDisplay.style.display = 'block';
    } else {
        rawDataDisplay.style.display = 'none';
    }
}

// 履歴表示
function showHistory() {
    const sidebar = DOM.historySidebar();
    sidebar.classList.add('active');
    loadHistoryData();
}

// 履歴非表示
function hideHistory() {
    const sidebar = DOM.historySidebar();
    sidebar.classList.remove('active');
}

// 履歴データ読み込み
function loadHistoryData() {
    const historyList = DOM.historyList();
    historyList.innerHTML = '';
    
    // ローカルストレージから履歴を取得
    const sessions = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('dental_session_')) {
            try {
                const session = JSON.parse(localStorage.getItem(key));
                sessions.push(session);
            } catch (e) {
                console.warn('履歴データの読み込みエラー:', key);
            }
        }
    }
    
    // 日付でソート
    sessions.sort((a, b) => new Date(b.session_info.session_date) - new Date(a.session_info.session_date));
    
    // 履歴アイテム表示
    sessions.forEach(session => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-header">
                <strong>${session.session_info.patient_name}</strong>
                <small>${new Date(session.session_info.session_date).toLocaleString('ja-JP')}</small>
            </div>
            <div class="history-details">
                <p>医師: ${session.session_info.doctor_name}</p>
                <p>ソース: ${session.session_info.source_tool === 'plaud' ? 'PLAUD NOTE' : 'Notta'}</p>
                <p>品質スコア: ${Math.round(session.quality_analysis.communication_quality * 100)}%</p>
            </div>
        `;
        historyList.appendChild(historyItem);
    });
    
    if (sessions.length === 0) {
        historyList.innerHTML = '<p class="no-history">処理履歴がありません</p>';
    }
}

// 履歴に追加
function addToHistory(sessionInfo) {
    // この関数は保存時に自動的に呼ばれるため、
    // 実際の実装では必要に応じてUI更新などを行う
    console.log('📋 履歴に追加:', sessionInfo.patient_name);
}

// 予約データ読み込み（オプション機能）
function loadAppointments() {
    const appointmentCsv = document.getElementById('appointment-csv');
    if (!appointmentCsv.files[0]) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const csv = e.target.result;
            appointmentData = parseCSV(csv);
            
            const statusElement = document.getElementById('appointment-status');
            if (statusElement) {
                statusElement.textContent = `${appointmentData.length}件の予約データを読み込みました`;
                statusElement.className = 'status-text success';
            }
            
            console.log('📅 予約データ読み込み完了:', appointmentData.length);
        } catch (error) {
            console.error('予約データ読み込みエラー:', error);
            const statusElement = document.getElementById('appointment-status');
            if (statusElement) {
                statusElement.textContent = 'CSVファイルの読み込みに失敗しました';
                statusElement.className = 'status-text error';
            }
        }
    };
    reader.readAsText(appointmentCsv.files[0]);
}

// CSV解析
function parseCSV(csv) {
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',');
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        const row = {};
        headers.forEach((header, index) => {
            row[header.trim()] = values[index]?.trim() || '';
        });
        data.push(row);
    }
    
    return data;
}

// 履歴読み込み（初期化時）
function loadHistory() {
    // 必要に応じて初期履歴読み込み処理を実装
    console.log('📚 履歴初期化完了');
}

// エクスポート（グローバル関数として公開）
window.toggleEditMode = toggleEditMode;
window.toggleFormatInfo = toggleFormatInfo;
window.toggleRawData = toggleRawData;
window.showHistory = showHistory;
window.hideHistory = hideHistory;
window.resetApp = resetApp;

// デバッグ用
if (typeof window !== 'undefined') {
    window.debugDental = {
        getCurrentStep: () => currentStep,
        getUploadedFiles: () => uploadedFiles,
        getCurrentSessionData: () => currentSessionData,
        getSelectedTool: () => selectedTool
    };
}

console.log('🎯 歯科カウンセリングAIツール - スクリプト読み込み完了');