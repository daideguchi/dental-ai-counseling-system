"""
データベースモデル定義
SQLAlchemyを使用したテーブル定義
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class CounselingSession(Base):
    """カウンセリングセッションテーブル"""
    __tablename__ = 'counseling_sessions'
    
    id = Column(String(50), primary_key=True)
    patient_id = Column(String(20))
    doctor_id = Column(String(20))
    appointment_id = Column(String(50))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    audio_file_path = Column(String(255))
    transcript = Column(Text)
    soap_note = Column(JSON)
    confidence_score = Column(Float)
    status = Column(String(20), default='processing')  # processing, completed, error
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # リレーション
    voice_analytics = relationship("VoiceAnalytics", back_populates="session")
    outcome = relationship("CounselingOutcome", back_populates="session", uselist=False)


class VoiceAnalytics(Base):
    """音声分析データテーブル"""
    __tablename__ = 'voice_analytics'
    
    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('counseling_sessions.id'))
    timestamp_offset = Column(Float)  # 秒単位のオフセット
    tone_level = Column(Float)
    speech_rate = Column(Float)
    emotion_scores = Column(JSON)
    non_verbal_events = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    session = relationship("CounselingSession", back_populates="voice_analytics")


class CounselingOutcome(Base):
    """カウンセリング結果テーブル"""
    __tablename__ = 'counseling_outcomes'
    
    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('counseling_sessions.id'))
    outcome_type = Column(String(20))  # contracted, declined, pending
    contract_amount = Column(Float)
    follow_up_scheduled = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    session = relationship("CounselingSession", back_populates="outcome")


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, database_url: str = "sqlite:///dental_counseling.db"):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """テーブルを作成"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """データベースセッションを取得"""
        return self.SessionLocal()
    
    def save_counseling_session(self, session_data: dict) -> str:
        """カウンセリングセッションを保存"""
        db = self.get_session()
        try:
            session = CounselingSession(
                id=session_data['recording_id'],
                patient_id=session_data.get('patient_id'),
                doctor_id=session_data.get('doctor_id'),
                appointment_id=session_data.get('appointment_id'),
                start_time=datetime.fromisoformat(session_data.get('start_time', datetime.now().isoformat())),
                end_time=datetime.fromisoformat(session_data.get('end_time', datetime.now().isoformat())),
                audio_file_path=session_data.get('audio_file_path'),
                transcript=session_data.get('transcript'),
                soap_note=session_data.get('soap_note'),
                confidence_score=session_data.get('confidence_score', 0.0),
                status=session_data.get('status', 'processing')
            )
            
            db.add(session)
            db.commit()
            return session.id
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_counseling_session(self, session_id: str) -> dict:
        """カウンセリングセッションを取得"""
        db = self.get_session()
        try:
            session = db.query(CounselingSession).filter(CounselingSession.id == session_id).first()
            if session:
                return {
                    'id': session.id,
                    'patient_id': session.patient_id,
                    'doctor_id': session.doctor_id,
                    'appointment_id': session.appointment_id,
                    'start_time': session.start_time.isoformat() if session.start_time else None,
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'audio_file_path': session.audio_file_path,
                    'transcript': session.transcript,
                    'soap_note': session.soap_note,
                    'confidence_score': session.confidence_score,
                    'status': session.status,
                    'created_at': session.created_at.isoformat() if session.created_at else None
                }
            return None
        finally:
            db.close()
    
    def update_soap_note(self, session_id: str, soap_note: dict, confidence_score: float = None):
        """SOAPノートを更新"""
        db = self.get_session()
        try:
            session = db.query(CounselingSession).filter(CounselingSession.id == session_id).first()
            if session:
                session.soap_note = soap_note
                if confidence_score is not None:
                    session.confidence_score = confidence_score
                session.status = 'completed'
                session.updated_at = datetime.now()
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def save_voice_analytics(self, analytics_data: dict) -> str:
        """音声分析データを保存"""
        db = self.get_session()
        try:
            analytics = VoiceAnalytics(
                id=f"va_{analytics_data['session_id']}_{int(analytics_data.get('timestamp_offset', 0))}",
                session_id=analytics_data['session_id'],
                timestamp_offset=analytics_data.get('timestamp_offset', 0.0),
                tone_level=analytics_data.get('tone_level', 0.0),
                speech_rate=analytics_data.get('speech_rate', 0.0),
                emotion_scores=analytics_data.get('emotion_scores', {}),
                non_verbal_events=analytics_data.get('non_verbal_events', {})
            )
            
            db.add(analytics)
            db.commit()
            return analytics.id
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def save_counseling_outcome(self, outcome_data: dict) -> str:
        """カウンセリング結果を保存"""
        db = self.get_session()
        try:
            outcome = CounselingOutcome(
                id=f"outcome_{outcome_data['session_id']}",
                session_id=outcome_data['session_id'],
                outcome_type=outcome_data.get('outcome_type', 'pending'),
                contract_amount=outcome_data.get('contract_amount', 0.0),
                follow_up_scheduled=outcome_data.get('follow_up_scheduled', False),
                notes=outcome_data.get('notes', '')
            )
            
            db.add(outcome)
            db.commit()
            return outcome.id
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_sessions_by_doctor(self, doctor_id: str, limit: int = 10) -> list:
        """医師別のセッション一覧を取得"""
        db = self.get_session()
        try:
            sessions = db.query(CounselingSession)\
                       .filter(CounselingSession.doctor_id == doctor_id)\
                       .order_by(CounselingSession.created_at.desc())\
                       .limit(limit).all()
            
            return [{
                'id': session.id,
                'patient_id': session.patient_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'status': session.status,
                'confidence_score': session.confidence_score
            } for session in sessions]
            
        finally:
            db.close()
    
    def get_outcome_statistics(self, doctor_id: str = None) -> dict:
        """成約率などの統計を取得"""
        db = self.get_session()
        try:
            query = db.query(CounselingOutcome)
            if doctor_id:
                query = query.join(CounselingSession).filter(CounselingSession.doctor_id == doctor_id)
            
            outcomes = query.all()
            
            total = len(outcomes)
            if total == 0:
                return {'total': 0, 'contracted': 0, 'declined': 0, 'pending': 0, 'contract_rate': 0.0}
            
            contracted = len([o for o in outcomes if o.outcome_type == 'contracted'])
            declined = len([o for o in outcomes if o.outcome_type == 'declined'])
            pending = len([o for o in outcomes if o.outcome_type == 'pending'])
            
            return {
                'total': total,
                'contracted': contracted,
                'declined': declined,
                'pending': pending,
                'contract_rate': contracted / (contracted + declined) if (contracted + declined) > 0 else 0.0
            }
            
        finally:
            db.close()


def test_database():
    """データベース機能のテスト"""
    
    # データベース初期化
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # サンプルセッションデータ
    session_data = {
        'recording_id': 'rec_20250126_1030',
        'patient_id': 'P12345',
        'doctor_id': 'D001',
        'appointment_id': 'APT-001',
        'start_time': '2025-01-26T10:30:00',
        'end_time': '2025-01-26T11:00:00',
        'audio_file_path': 'audio/rec_20250126_1030.mp3',
        'transcript': '患者: 右上の奥歯が痛くて...',
        'soap_note': {
            'S': '右上奥歯の痛み、2週間前から',
            'O': '右上第一大臼歯に深いう蝕',
            'A': '深在性う蝕',
            'P': 'CR充填予定'
        },
        'confidence_score': 0.85,
        'status': 'completed'
    }
    
    # セッション保存
    session_id = db_manager.save_counseling_session(session_data)
    print(f"保存されたセッションID: {session_id}")
    
    # セッション取得
    retrieved_session = db_manager.get_counseling_session(session_id)
    print("取得されたセッション:")
    print(json.dumps(retrieved_session, ensure_ascii=False, indent=2))
    
    # 音声分析データ保存
    analytics_data = {
        'session_id': session_id,
        'timestamp_offset': 30.5,
        'tone_level': 0.7,
        'speech_rate': 1.2,
        'emotion_scores': {'anxiety': 0.3, 'satisfaction': 0.8},
        'non_verbal_events': {'sighs': 1, 'pauses': 3}
    }
    
    analytics_id = db_manager.save_voice_analytics(analytics_data)
    print(f"保存された音声分析ID: {analytics_id}")
    
    # 結果データ保存
    outcome_data = {
        'session_id': session_id,
        'outcome_type': 'contracted',
        'contract_amount': 50000.0,
        'follow_up_scheduled': True,
        'notes': '治療に同意、次回予約済み'
    }
    
    outcome_id = db_manager.save_counseling_outcome(outcome_data)
    print(f"保存された結果ID: {outcome_id}")
    
    # 統計取得
    stats = db_manager.get_outcome_statistics('D001')
    print("統計データ:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_database()