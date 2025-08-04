#!/usr/bin/env python3
"""
音声感情分析モジュール - プロトタイプ
将来的にAmiVoice ESASのような機能を実装するためのサンプル
"""

import json
import random
from typing import Dict, List
from datetime import datetime

class VoiceEmotionAnalyzer:
    """音声感情分析クラス（サンプル実装）"""
    
    def __init__(self):
        self.emotion_categories = [
            'joy',      # 喜び
            'anger',    # 怒り
            'stress',   # ストレス
            'anxiety',  # 不安
            'satisfaction', # 満足
            'confusion',    # 困惑
            'trust',        # 信頼
            'hesitation'    # 躊躇
        ]
    
    def analyze_voice_emotion(self, audio_file_path: str, transcript: List[Dict]) -> Dict:
        """
        音声ファイルから感情を分析（サンプル実装）
        実際の実装では音響特徴量を解析
        """
        print(f"🎵 音声感情分析開始: {audio_file_path}")
        
        # サンプルデータ生成（実際はAI分析結果）
        emotion_timeline = []
        
        for i, entry in enumerate(transcript):
            # 発言者別の感情傾向をシミュレート
            if entry['speaker'] == '患者':
                emotions = self._analyze_patient_emotion(entry['text'])
            else:
                emotions = self._analyze_doctor_emotion(entry['text'])
            
            emotion_timeline.append({
                'timestamp': entry.get('timestamp', f"00:00:{i*10:02d}"),
                'speaker': entry['speaker'],
                'text': entry['text'][:50] + "..." if len(entry['text']) > 50 else entry['text'],
                'emotions': emotions
            })
        
        # 全体的な感情サマリー
        overall_analysis = self._generate_overall_analysis(emotion_timeline)
        
        result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'audio_file': audio_file_path,
            'emotion_timeline': emotion_timeline,
            'overall_analysis': overall_analysis,
            'counseling_success_prediction': self._predict_counseling_success(overall_analysis)
        }
        
        print("✅ 音声感情分析完了")
        return result
    
    def _analyze_patient_emotion(self, text: str) -> Dict:
        """患者の発言から感情を分析"""
        emotions = {}
        
        # キーワードベースの感情推定（サンプル）
        if any(word in text for word in ['痛い', 'しみる', 'ひどい']):
            emotions['stress'] = random.uniform(0.6, 0.9)
            emotions['anxiety'] = random.uniform(0.5, 0.8)
        
        if any(word in text for word in ['分かりました', 'お願いします']):
            emotions['trust'] = random.uniform(0.7, 0.9)
            emotions['satisfaction'] = random.uniform(0.6, 0.8)
        
        if any(word in text for word in ['どのくらい', 'どうなる']):
            emotions['anxiety'] = random.uniform(0.5, 0.7)
            emotions['confusion'] = random.uniform(0.4, 0.6)
        
        # 基本感情値を設定
        for emotion in self.emotion_categories:
            if emotion not in emotions:
                emotions[emotion] = random.uniform(0.1, 0.3)
        
        return emotions
    
    def _analyze_doctor_emotion(self, text: str) -> Dict:
        """医師の発言から感情を分析"""
        emotions = {}
        
        # 医師は一般的に安定した感情
        if any(word in text for word in ['なるほど', '分かりました', 'そうですね']):
            emotions['trust'] = random.uniform(0.8, 0.9)
            emotions['satisfaction'] = random.uniform(0.7, 0.8)
        
        if any(word in text for word in ['治療', '大丈夫', '問題ありません']):
            emotions['joy'] = random.uniform(0.6, 0.8)
            emotions['trust'] = random.uniform(0.8, 0.9)
        
        # 基本感情値を設定（医師は安定）
        for emotion in self.emotion_categories:
            if emotion not in emotions:
                emotions[emotion] = random.uniform(0.1, 0.2)
        
        return emotions
    
    def _generate_overall_analysis(self, emotion_timeline: List[Dict]) -> Dict:
        """全体的な感情分析サマリーを生成"""
        patient_emotions = []
        doctor_emotions = []
        
        for entry in emotion_timeline:
            if entry['speaker'] == '患者':
                patient_emotions.append(entry['emotions'])
            else:
                doctor_emotions.append(entry['emotions'])
        
        # 平均感情値を計算
        patient_avg = self._calculate_average_emotions(patient_emotions)
        doctor_avg = self._calculate_average_emotions(doctor_emotions)
        
        return {
            'patient_emotional_state': patient_avg,
            'doctor_emotional_state': doctor_avg,
            'emotional_rapport': self._calculate_rapport(patient_avg, doctor_avg),
            'key_insights': self._generate_insights(patient_avg, doctor_avg)
        }
    
    def _calculate_average_emotions(self, emotion_list: List[Dict]) -> Dict:
        """感情の平均値を計算"""
        if not emotion_list:
            return {}
        
        avg_emotions = {}
        for emotion in self.emotion_categories:
            values = [emotions.get(emotion, 0) for emotions in emotion_list]
            avg_emotions[emotion] = sum(values) / len(values)
        
        return avg_emotions
    
    def _calculate_rapport(self, patient_emotions: Dict, doctor_emotions: Dict) -> float:
        """患者と医師の感情的な調和度を計算"""
        if not patient_emotions or not doctor_emotions:
            return 0.5
        
        # 信頼度と満足度の相関を重視
        patient_trust = patient_emotions.get('trust', 0)
        doctor_trust = doctor_emotions.get('trust', 0)
        patient_satisfaction = patient_emotions.get('satisfaction', 0)
        
        rapport_score = (patient_trust + doctor_trust + patient_satisfaction) / 3
        return min(rapport_score, 1.0)
    
    def _generate_insights(self, patient_emotions: Dict, doctor_emotions: Dict) -> List[str]:
        """感情分析に基づく洞察を生成"""
        insights = []
        
        if patient_emotions.get('anxiety', 0) > 0.6:
            insights.append("患者の不安レベルが高い - より丁寧な説明が効果的")
        
        if patient_emotions.get('trust', 0) > 0.7:
            insights.append("患者の信頼度が高い - 治療同意の可能性が高い")
        
        if patient_emotions.get('confusion', 0) > 0.5:
            insights.append("患者が混乱している可能性 - 説明の簡素化を推奨")
        
        if doctor_emotions.get('satisfaction', 0) > 0.8:
            insights.append("医師の説明が効果的 - 良好なコミュニケーション")
        
        return insights
    
    def _predict_counseling_success(self, overall_analysis: Dict) -> Dict:
        """カウンセリング成功率を予測"""
        rapport = overall_analysis.get('emotional_rapport', 0.5)
        patient_trust = overall_analysis.get('patient_emotional_state', {}).get('trust', 0.5)
        patient_anxiety = overall_analysis.get('patient_emotional_state', {}).get('anxiety', 0.5)
        
        # 成功率計算（サンプルロジック）
        success_score = (rapport * 0.4 + patient_trust * 0.4 + (1 - patient_anxiety) * 0.2)
        
        prediction = {
            'success_probability': min(success_score, 1.0),
            'confidence_level': 'high' if success_score > 0.7 else 'medium' if success_score > 0.5 else 'low',
            'recommendation': self._generate_recommendation(success_score)
        }
        
        return prediction
    
    def _generate_recommendation(self, success_score: float) -> str:
        """成功率に基づく推奨アクションを生成"""
        if success_score > 0.8:
            return "治療同意の可能性が高い。積極的に治療計画を提案してください。"
        elif success_score > 0.6:
            return "患者は概ね理解している。追加の質問がないか確認してください。"
        elif success_score > 0.4:
            return "患者の不安が残っている。より詳細な説明や安心材料の提供を推奨。"
        else:
            return "患者の理解度や信頼度が低い。別の説明方法を検討してください。"

def demo_voice_emotion_analysis():
    """音声感情分析のデモンストレーション"""
    print("🎵 音声感情分析デモ")
    print("=" * 50)
    
    # サンプル文字起こしデータ
    sample_transcript = [
        {'speaker': '医師', 'text': 'おはようございます。今日はどのような症状でいらっしゃいましたか？'},
        {'speaker': '患者', 'text': '右上の奥歯が2週間ほど前から冷たいものを飲むとしみるんです。'},
        {'speaker': '医師', 'text': 'なるほど。冷たいものでしみるということですね。'},
        {'speaker': '患者', 'text': 'ズキズキするような痛みではなくて、キーンとしみる感じです。'},
        {'speaker': '医師', 'text': '右上の第一大臼歯に深いう蝕を認めますね。'},
        {'speaker': '患者', 'text': 'やっぱり虫歯でしたか。どのくらい悪いんでしょうか？'},
        {'speaker': '医師', 'text': 'かなり深い虫歯ですが、神経はまだ生きているようです。'},
        {'speaker': '患者', 'text': '分かりました。いつ頃治療していただけますか？'},
        {'speaker': '医師', 'text': '来週の火曜日、2月2日の午前中はいかがでしょうか？'},
        {'speaker': '患者', 'text': 'はい、お願いします。'}
    ]
    
    # 感情分析実行
    analyzer = VoiceEmotionAnalyzer()
    result = analyzer.analyze_voice_emotion('sample_audio.mp3', sample_transcript)
    
    # 結果表示
    print("\n📊 感情分析結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 成功予測結果
    prediction = result['counseling_success_prediction']
    print(f"\n🎯 カウンセリング成功予測:")
    print(f"成功確率: {prediction['success_probability']:.1%}")
    print(f"信頼度: {prediction['confidence_level']}")
    print(f"推奨アクション: {prediction['recommendation']}")

if __name__ == "__main__":
    demo_voice_emotion_analysis()