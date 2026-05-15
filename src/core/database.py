"""
VoiceHealth — 数据库模型和管理

完整的数据存储方案：
- 用户系统
- 检测记录
- 订单系统
- VIP会员
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class Database:
    """SQLite数据库管理"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "voicehealth.db")
        
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def init_db(self):
        """初始化数据库表"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                openid TEXT UNIQUE,
                phone TEXT,
                nickname TEXT DEFAULT '',
                avatar_url TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                age INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                vip_expire_at TEXT,
                free_count INTEGER DEFAULT 0,
                last_free_date TEXT,
                total_reports INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        
        # 语音检测记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                audio_url TEXT,
                overall_score REAL,
                summary TEXT,
                features TEXT,  -- JSON
                risks TEXT,     -- JSON
                domains TEXT,   -- JSON
                voice_quality TEXT, -- JSON
                feature_vector TEXT, -- JSON
                ai_insight TEXT,
                reading_text_id TEXT,
                liveness_score REAL,
                reading_match_score REAL,
                duration REAL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        voice_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(voice_reports)").fetchall()
        }
        for column_name, column_type in (
            ('domains', 'TEXT'),
            ('voice_quality', 'TEXT'),
            ('feature_vector', 'TEXT'),
        ):
            if column_name not in voice_columns:
                cursor.execute(f'ALTER TABLE voice_reports ADD COLUMN {column_name} {column_type}')
        
        # 面部检测记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                image_url TEXT,
                overall_score REAL,
                predicted_age INTEGER,
                dimensions TEXT,  -- JSON
                summary TEXT,
                suggestions TEXT, -- JSON
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 视频检测记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                video_url TEXT,
                overall_score REAL,
                biological_age INTEGER,
                skin_result TEXT,  -- JSON
                eye_result TEXT,   -- JSON
                hair_result TEXT,  -- JSON
                detect_items TEXT, -- JSON
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 综合评估记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS combined_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                voice_report_id TEXT,
                face_report_id TEXT,
                video_report_id TEXT,
                overall_score REAL,
                biological_age INTEGER,
                dimensions TEXT,  -- JSON
                summary TEXT,
                suggestions TEXT, -- JSON
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        combined_columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(combined_reports)").fetchall()
        }
        if 'video_report_id' not in combined_columns:
            cursor.execute('ALTER TABLE combined_reports ADD COLUMN video_report_id TEXT')
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                order_no TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,  -- single, vip_monthly, vip_yearly
                amount INTEGER NOT NULL,  -- 单位：分
                status TEXT DEFAULT 'pending',  -- pending, paid, refunded, cancelled
                payment_method TEXT,
                payment_id TEXT,
                paid_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # VIP记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                order_id TEXT,
                type TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        ''')
        
        # 验证日志
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                audio_url TEXT,
                is_live INTEGER,
                liveness_score REAL,
                reading_text_id TEXT,
                reading_match_score REAL,
                is_valid INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # 每日生活方式打卡：饮食、运动、睡眠、压力和症状记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lifestyle_checkins (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                meals TEXT,
                diet_tags TEXT,
                water_ml INTEGER DEFAULT 0,
                caffeine_cups REAL DEFAULT 0,
                alcohol INTEGER DEFAULT 0,
                spicy_oily INTEGER DEFAULT 0,
                late_meal INTEGER DEFAULT 0,
                exercise_type TEXT DEFAULT '',
                exercise_minutes INTEGER DEFAULT 0,
                exercise_intensity TEXT DEFAULT '',
                steps INTEGER DEFAULT 0,
                sleep_hours REAL DEFAULT 0,
                stress_level INTEGER DEFAULT 0,
                mood TEXT DEFAULT '',
                symptoms TEXT,
                notes TEXT DEFAULT '',
                source TEXT DEFAULT 'mini_program',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, checkin_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # 改善闭环周期：从报告异常/关注项生成计划，持续执行、复测、回顾
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_cycles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                source_report_id TEXT,
                status TEXT DEFAULT 'active',
                plan_json TEXT NOT NULL,
                baseline_score REAL DEFAULT 0,
                latest_score REAL DEFAULT 0,
                target_score REAL DEFAULT 0,
                start_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                completed_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_progress (
                id TEXT PRIMARY KEY,
                cycle_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                completed_action_ids TEXT,
                skipped_action_ids TEXT,
                mood_score INTEGER DEFAULT 0,
                energy_score INTEGER DEFAULT 0,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(cycle_id, checkin_date),
                FOREIGN KEY (cycle_id) REFERENCES improvement_cycles(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ═══════ 用户操作 ═══════
    
    def create_user(self, openid: str, nickname: str = '', avatar_url: str = '') -> Dict:
        """创建用户"""
        user_id = str(uuid.uuid4())
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO users (id, openid, nickname, avatar_url)
            VALUES (?, ?, ?, ?)
        ''', (user_id, openid, nickname, avatar_url))
        conn.commit()
        user = self.get_user(user_id)
        conn.close()
        return user
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_openid(self, openid: str) -> Optional[Dict]:
        """通过openid获取用户"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM users WHERE openid = ?', (openid,)).fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_or_create_user(self, openid: str, nickname: str = '', avatar_url: str = '') -> Dict:
        """获取或创建用户"""
        user = self.get_user_by_openid(openid)
        if not user:
            user = self.create_user(openid, nickname, avatar_url)
        return user
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """更新用户信息"""
        allowed = ['nickname', 'avatar_url', 'gender', 'age', 'phone']
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        
        conn = self.get_conn()
        conn.execute(f'''
            UPDATE users SET {set_clause}, updated_at = datetime('now')
            WHERE id = ?
        ''', values)
        conn.commit()
        conn.close()
        return True
    
    def check_vip_status(self, user_id: str) -> bool:
        """检查VIP状态"""
        user = self.get_user(user_id)
        if not user or not user['is_vip']:
            return False
        
        if user['vip_expire_at']:
            expire = datetime.fromisoformat(user['vip_expire_at'])
            if datetime.now() > expire:
                # VIP已过期
                conn = self.get_conn()
                conn.execute('UPDATE users SET is_vip = 0 WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                return False
        
        return True
    
    def use_free_count(self, user_id: str) -> bool:
        """使用免费次数，返回是否成功"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查是否需要重置
        if user['last_free_date'] != today:
            conn = self.get_conn()
            conn.execute('''
                UPDATE users SET free_count = 0, last_free_date = ? WHERE id = ?
            ''', (today, user_id))
            conn.commit()
            conn.close()
            user['free_count'] = 0
        
        # 检查免费次数
        if user['free_count'] >= 1:  # 每天1次免费
            return False
        
        # 增加使用次数
        conn = self.get_conn()
        conn.execute('''
            UPDATE users SET free_count = free_count + 1, last_free_date = ? WHERE id = ?
        ''', (today, user_id))
        conn.commit()
        conn.close()
        return True
    
    # ═══════ 语音报告 ═══════
    
    def save_voice_report(self, user_id: str, report: Dict) -> str:
        """保存语音检测报告"""
        report_id = str(uuid.uuid4())
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO voice_reports 
            (id, user_id, overall_score, summary, features, risks, domains,
             voice_quality, feature_vector, ai_insight, 
             reading_text_id, liveness_score, reading_match_score, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, user_id,
            report.get('overall_score', 0),
            report.get('summary', ''),
            json.dumps(report.get('features', [])),
            json.dumps(report.get('risks', [])),
            json.dumps(report.get('domains', [])),
            json.dumps(report.get('voice_quality', {})),
            json.dumps(report.get('feature_vector', {})),
            report.get('ai_insight', ''),
            report.get('reading_text_id'),
            report.get('liveness_score'),
            report.get('reading_match_score'),
            report.get('duration', 30)
        ))
        
        # 更新用户报告数
        conn.execute('''
            UPDATE users SET total_reports = total_reports + 1 WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return report_id
    
    def get_voice_report(self, report_id: str) -> Optional[Dict]:
        """获取语音报告"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM voice_reports WHERE id = ?', (report_id,)).fetchone()
        conn.close()
        if row:
            result = dict(row)
            result['features'] = json.loads(result['features']) if result['features'] else []
            result['risks'] = json.loads(result['risks']) if result['risks'] else []
            result['domains'] = json.loads(result['domains']) if result.get('domains') else []
            result['voice_quality'] = json.loads(result['voice_quality']) if result.get('voice_quality') else {}
            result['feature_vector'] = json.loads(result['feature_vector']) if result.get('feature_vector') else {}
            return result
        return None
    
    def get_user_voice_reports(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """获取用户的语音报告列表"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT * FROM voice_reports 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset)).fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            result['features'] = json.loads(result['features']) if result['features'] else []
            result['risks'] = json.loads(result['risks']) if result['risks'] else []
            result['domains'] = json.loads(result['domains']) if result.get('domains') else []
            result['voice_quality'] = json.loads(result['voice_quality']) if result.get('voice_quality') else {}
            result['feature_vector'] = json.loads(result['feature_vector']) if result.get('feature_vector') else {}
            results.append(result)
        return results
    
    # ═══════ 面部报告 ═══════
    
    def save_face_report(self, user_id: str, report: Dict) -> str:
        """保存面部检测报告"""
        report_id = str(uuid.uuid4())
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO face_reports 
            (id, user_id, overall_score, predicted_age, dimensions, summary, suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, user_id,
            report.get('overall_score', 0),
            report.get('predicted_age', 0),
            json.dumps(report.get('dimensions', [])),
            report.get('summary', ''),
            json.dumps(report.get('suggestions', []))
        ))
        
        conn.execute('UPDATE users SET total_reports = total_reports + 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return report_id
    
    def get_face_report(self, report_id: str) -> Optional[Dict]:
        """获取面部报告"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM face_reports WHERE id = ?', (report_id,)).fetchone()
        conn.close()
        if row:
            result = dict(row)
            result['dimensions'] = json.loads(result['dimensions']) if result['dimensions'] else []
            result['suggestions'] = json.loads(result['suggestions']) if result['suggestions'] else []
            return result
        return None
    
    # ═══════ 视频报告 ═══════
    
    def save_video_report(self, user_id: str, report: Dict) -> str:
        """保存视频检测报告"""
        report_id = str(uuid.uuid4())
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO video_reports 
            (id, user_id, overall_score, biological_age, skin_result, eye_result, hair_result, detect_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, user_id,
            report.get('overall_score', 0),
            report.get('biological_age', 0),
            json.dumps(report.get('skin')),
            json.dumps(report.get('eye')),
            json.dumps(report.get('hair')),
            json.dumps(report.get('detect_items', ['skin', 'eye', 'hair']))
        ))
        
        conn.execute('UPDATE users SET total_reports = total_reports + 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return report_id
    
    def get_video_report(self, report_id: str) -> Optional[Dict]:
        """获取视频报告"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM video_reports WHERE id = ?', (report_id,)).fetchone()
        conn.close()
        if row:
            result = dict(row)
            result['skin_result'] = json.loads(result['skin_result']) if result['skin_result'] else None
            result['eye_result'] = json.loads(result['eye_result']) if result['eye_result'] else None
            result['hair_result'] = json.loads(result['hair_result']) if result['hair_result'] else None
            result['detect_items'] = json.loads(result['detect_items']) if result['detect_items'] else []
            return result
        return None

    # ═══════ 综合报告 ═══════

    def save_combined_report(self, user_id: str, report: Dict) -> str:
        """保存综合健康评估报告"""
        report_id = str(uuid.uuid4())
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO combined_reports
            (id, user_id, voice_report_id, face_report_id, video_report_id, overall_score,
             biological_age, dimensions, summary, suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            user_id,
            report.get('voice_report_id'),
            report.get('face_report_id'),
            report.get('video_report_id'),
            report.get('overall_score', 0),
            report.get('biological_age', 0),
            json.dumps(report.get('dimensions', [])),
            report.get('summary', ''),
            json.dumps(report.get('suggestions', []))
        ))

        conn.execute('UPDATE users SET total_reports = total_reports + 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return report_id

    def get_combined_report(self, report_id: str) -> Optional[Dict]:
        """获取综合报告"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM combined_reports WHERE id = ?', (report_id,)).fetchone()
        conn.close()
        if row:
            result = dict(row)
            result['dimensions'] = json.loads(result['dimensions']) if result['dimensions'] else []
            result['suggestions'] = json.loads(result['suggestions']) if result['suggestions'] else []
            return result
        return None

    # ═══════ 生活方式打卡 ═══════

    def save_lifestyle_checkin(self, user_id: str, checkin: Dict) -> Dict:
        """保存或更新每日生活方式打卡。"""
        checkin_date = checkin.get('checkinDate') or checkin.get('checkin_date') or datetime.now().strftime('%Y-%m-%d')
        meals = {
            'breakfast': checkin.get('breakfast', ''),
            'lunch': checkin.get('lunch', ''),
            'dinner': checkin.get('dinner', ''),
            'snack': checkin.get('snack', ''),
        }
        diet_tags = checkin.get('dietTags') or checkin.get('diet_tags') or []
        symptoms = checkin.get('symptoms') or []

        values = {
            'meals': json.dumps(meals, ensure_ascii=False),
            'diet_tags': json.dumps(diet_tags, ensure_ascii=False),
            'water_ml': int(checkin.get('waterMl') or checkin.get('water_ml') or 0),
            'caffeine_cups': float(checkin.get('caffeineCups') or checkin.get('caffeine_cups') or 0),
            'alcohol': 1 if checkin.get('alcohol') else 0,
            'spicy_oily': 1 if (checkin.get('spicyOily') or checkin.get('spicy_oily')) else 0,
            'late_meal': 1 if (checkin.get('lateMeal') or checkin.get('late_meal')) else 0,
            'exercise_type': checkin.get('exerciseType') or checkin.get('exercise_type') or '',
            'exercise_minutes': int(checkin.get('exerciseMinutes') or checkin.get('exercise_minutes') or 0),
            'exercise_intensity': checkin.get('exerciseIntensity') or checkin.get('exercise_intensity') or '',
            'steps': int(checkin.get('steps') or 0),
            'sleep_hours': float(checkin.get('sleepHours') or checkin.get('sleep_hours') or 0),
            'stress_level': int(checkin.get('stressLevel') or checkin.get('stress_level') or 0),
            'mood': checkin.get('mood') or '',
            'symptoms': json.dumps(symptoms, ensure_ascii=False),
            'notes': checkin.get('notes') or '',
            'source': checkin.get('source') or 'mini_program',
        }

        conn = self.get_conn()
        existing = conn.execute('''
            SELECT id FROM lifestyle_checkins
            WHERE user_id = ? AND checkin_date = ?
        ''', (user_id, checkin_date)).fetchone()

        if existing:
            checkin_id = existing['id']
            conn.execute('''
                UPDATE lifestyle_checkins
                SET meals = ?, diet_tags = ?, water_ml = ?, caffeine_cups = ?,
                    alcohol = ?, spicy_oily = ?, late_meal = ?, exercise_type = ?,
                    exercise_minutes = ?, exercise_intensity = ?, steps = ?,
                    sleep_hours = ?, stress_level = ?, mood = ?, symptoms = ?,
                    notes = ?, source = ?, updated_at = datetime('now')
                WHERE id = ?
            ''', (
                values['meals'], values['diet_tags'], values['water_ml'], values['caffeine_cups'],
                values['alcohol'], values['spicy_oily'], values['late_meal'], values['exercise_type'],
                values['exercise_minutes'], values['exercise_intensity'], values['steps'],
                values['sleep_hours'], values['stress_level'], values['mood'], values['symptoms'],
                values['notes'], values['source'], checkin_id
            ))
        else:
            checkin_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO lifestyle_checkins
                (id, user_id, checkin_date, meals, diet_tags, water_ml, caffeine_cups,
                 alcohol, spicy_oily, late_meal, exercise_type, exercise_minutes,
                 exercise_intensity, steps, sleep_hours, stress_level, mood, symptoms,
                 notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                checkin_id, user_id, checkin_date, values['meals'], values['diet_tags'],
                values['water_ml'], values['caffeine_cups'], values['alcohol'],
                values['spicy_oily'], values['late_meal'], values['exercise_type'],
                values['exercise_minutes'], values['exercise_intensity'], values['steps'],
                values['sleep_hours'], values['stress_level'], values['mood'],
                values['symptoms'], values['notes'], values['source']
            ))

        conn.commit()
        conn.close()
        return self.get_lifestyle_checkin(user_id, checkin_date) or {}

    def get_lifestyle_checkin(self, user_id: str, checkin_date: str) -> Optional[Dict]:
        """按日期获取生活方式打卡。"""
        conn = self.get_conn()
        row = conn.execute('''
            SELECT * FROM lifestyle_checkins
            WHERE user_id = ? AND checkin_date = ?
        ''', (user_id, checkin_date)).fetchone()
        conn.close()
        return self._parse_lifestyle_checkin(row) if row else None

    def get_lifestyle_checkins(self, user_id: str, days: int = 30, limit: int = 100) -> List[Dict]:
        """获取最近一段时间的生活方式打卡。"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT * FROM lifestyle_checkins
            WHERE user_id = ? AND checkin_date >= date('now', ?)
            ORDER BY checkin_date DESC
            LIMIT ?
        ''', (user_id, f'-{days} days', limit)).fetchall()
        conn.close()
        return [self._parse_lifestyle_checkin(row) for row in rows]

    def get_lifestyle_summary(self, user_id: str, days: int = 30) -> Dict:
        """汇总饮食、运动、睡眠和压力记录。"""
        records = self.get_lifestyle_checkins(user_id, days=days, limit=days + 5)
        if not records:
            return {
                'days': days,
                'checkinDays': 0,
                'streak': 0,
                'avgWaterMl': 0,
                'exerciseDays': 0,
                'avgExerciseMinutes': 0,
                'avgSteps': 0,
                'avgSleepHours': 0,
                'avgStressLevel': 0,
                'latest': None,
            }

        def avg(values):
            values = [float(v) for v in values if v is not None and float(v) > 0]
            return round(sum(values) / len(values), 1) if values else 0

        exercise_days = sum(1 for item in records if int(item.get('exerciseMinutes') or 0) > 0)
        return {
            'days': days,
            'checkinDays': len(records),
            'streak': self._lifestyle_streak(records),
            'avgWaterMl': avg([item.get('waterMl') for item in records]),
            'exerciseDays': exercise_days,
            'avgExerciseMinutes': avg([item.get('exerciseMinutes') for item in records]),
            'avgSteps': avg([item.get('steps') for item in records]),
            'avgSleepHours': avg([item.get('sleepHours') for item in records]),
            'avgStressLevel': avg([item.get('stressLevel') for item in records]),
            'latest': records[0],
        }

    @staticmethod
    def _parse_lifestyle_checkin(row) -> Dict:
        result = dict(row)
        meals = json.loads(result['meals']) if result.get('meals') else {}
        diet_tags = json.loads(result['diet_tags']) if result.get('diet_tags') else []
        symptoms = json.loads(result['symptoms']) if result.get('symptoms') else []
        return {
            'id': result['id'],
            'userId': result['user_id'],
            'checkinDate': result['checkin_date'],
            'breakfast': meals.get('breakfast', ''),
            'lunch': meals.get('lunch', ''),
            'dinner': meals.get('dinner', ''),
            'snack': meals.get('snack', ''),
            'dietTags': diet_tags,
            'waterMl': result.get('water_ml') or 0,
            'caffeineCups': result.get('caffeine_cups') or 0,
            'alcohol': bool(result.get('alcohol')),
            'spicyOily': bool(result.get('spicy_oily')),
            'lateMeal': bool(result.get('late_meal')),
            'exerciseType': result.get('exercise_type') or '',
            'exerciseMinutes': result.get('exercise_minutes') or 0,
            'exerciseIntensity': result.get('exercise_intensity') or '',
            'steps': result.get('steps') or 0,
            'sleepHours': result.get('sleep_hours') or 0,
            'stressLevel': result.get('stress_level') or 0,
            'mood': result.get('mood') or '',
            'symptoms': symptoms,
            'notes': result.get('notes') or '',
            'source': result.get('source') or '',
            'createdAt': result.get('created_at'),
            'updatedAt': result.get('updated_at'),
        }

    @staticmethod
    def _lifestyle_streak(records: List[Dict]) -> int:
        dates = {item.get('checkinDate') for item in records}
        streak = 0
        current = datetime.now().date()
        while current.strftime('%Y-%m-%d') in dates:
            streak += 1
            current = current - timedelta(days=1)
        return streak

    # ═══════ 改善闭环 ═══════

    def create_improvement_cycle(
        self,
        user_id: str,
        plan: Dict,
        source_report_id: Optional[str] = None,
        duration_days: int = 14
    ) -> Dict:
        """创建新的改善闭环周期，并把旧active周期标记为replaced。"""
        cycle_id = str(uuid.uuid4())
        start_date = datetime.now().strftime('%Y-%m-%d')
        target_date = (datetime.now() + timedelta(days=max(1, duration_days))).strftime('%Y-%m-%d')
        baseline_score = float(plan.get('scoreStatus', {}).get('score') or 0)
        target_score = min(100.0, baseline_score + (8 if baseline_score < 70 else 5 if baseline_score < 85 else 2))

        conn = self.get_conn()
        conn.execute('''
            UPDATE improvement_cycles
            SET status = 'replaced', updated_at = datetime('now')
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        conn.execute('''
            INSERT INTO improvement_cycles
            (id, user_id, source_report_id, status, plan_json, baseline_score,
             latest_score, target_score, start_date, target_date)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
        ''', (
            cycle_id,
            user_id,
            source_report_id,
            json.dumps(plan, ensure_ascii=False),
            baseline_score,
            baseline_score,
            target_score,
            start_date,
            target_date,
        ))
        conn.commit()
        conn.close()
        return self.get_improvement_cycle(user_id, cycle_id) or {}

    def get_active_improvement_cycle(self, user_id: str) -> Optional[Dict]:
        """获取用户当前active改善周期。"""
        conn = self.get_conn()
        row = conn.execute('''
            SELECT * FROM improvement_cycles
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()
        conn.close()
        return self._parse_improvement_cycle(row) if row else None

    def get_improvement_cycle(self, user_id: str, cycle_id: str) -> Optional[Dict]:
        """按ID获取改善周期。"""
        conn = self.get_conn()
        row = conn.execute('''
            SELECT * FROM improvement_cycles
            WHERE id = ? AND user_id = ?
        ''', (cycle_id, user_id)).fetchone()
        conn.close()
        return self._parse_improvement_cycle(row) if row else None

    def list_improvement_cycles(self, user_id: str, limit: int = 20) -> List[Dict]:
        """列出改善周期。"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT * FROM improvement_cycles
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
        conn.close()
        return [self._parse_improvement_cycle(row) for row in rows]

    def update_improvement_cycle_status(
        self,
        user_id: str,
        cycle_id: str,
        status: str,
        latest_score: Optional[float] = None
    ) -> Optional[Dict]:
        """更新改善周期状态。"""
        completed_at = datetime.now().isoformat() if status in ('completed', 'cancelled') else None
        conn = self.get_conn()
        if latest_score is None:
            conn.execute('''
                UPDATE improvement_cycles
                SET status = ?, completed_at = COALESCE(?, completed_at), updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
            ''', (status, completed_at, cycle_id, user_id))
        else:
            conn.execute('''
                UPDATE improvement_cycles
                SET status = ?, latest_score = ?, completed_at = COALESCE(?, completed_at),
                    updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
            ''', (status, latest_score, completed_at, cycle_id, user_id))
        conn.commit()
        conn.close()
        return self.get_improvement_cycle(user_id, cycle_id)

    def save_improvement_progress(self, user_id: str, cycle_id: str, progress: Dict) -> Dict:
        """保存或更新某天的改善执行记录。"""
        checkin_date = progress.get('checkinDate') or progress.get('checkin_date') or datetime.now().strftime('%Y-%m-%d')
        completed = progress.get('completedActionIds') or progress.get('completed_action_ids') or []
        skipped = progress.get('skippedActionIds') or progress.get('skipped_action_ids') or []
        mood_score = int(progress.get('moodScore') or progress.get('mood_score') or 0)
        energy_score = int(progress.get('energyScore') or progress.get('energy_score') or 0)
        note = progress.get('note') or ''

        conn = self.get_conn()
        existing = conn.execute('''
            SELECT id FROM improvement_progress
            WHERE cycle_id = ? AND user_id = ? AND checkin_date = ?
        ''', (cycle_id, user_id, checkin_date)).fetchone()

        if existing:
            progress_id = existing['id']
            conn.execute('''
                UPDATE improvement_progress
                SET completed_action_ids = ?, skipped_action_ids = ?, mood_score = ?,
                    energy_score = ?, note = ?, updated_at = datetime('now')
                WHERE id = ?
            ''', (
                json.dumps(completed, ensure_ascii=False),
                json.dumps(skipped, ensure_ascii=False),
                mood_score,
                energy_score,
                note,
                progress_id,
            ))
        else:
            progress_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO improvement_progress
                (id, cycle_id, user_id, checkin_date, completed_action_ids,
                 skipped_action_ids, mood_score, energy_score, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                progress_id,
                cycle_id,
                user_id,
                checkin_date,
                json.dumps(completed, ensure_ascii=False),
                json.dumps(skipped, ensure_ascii=False),
                mood_score,
                energy_score,
                note,
            ))
        conn.commit()
        conn.close()
        return self.get_improvement_progress_for_date(user_id, cycle_id, checkin_date) or {}

    def get_improvement_progress(
        self,
        user_id: str,
        cycle_id: str,
        limit: int = 60
    ) -> List[Dict]:
        """获取改善周期执行记录。"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT * FROM improvement_progress
            WHERE user_id = ? AND cycle_id = ?
            ORDER BY checkin_date DESC
            LIMIT ?
        ''', (user_id, cycle_id, limit)).fetchall()
        conn.close()
        return [self._parse_improvement_progress(row) for row in rows]

    def get_improvement_progress_for_date(
        self,
        user_id: str,
        cycle_id: str,
        checkin_date: str
    ) -> Optional[Dict]:
        """获取某天改善执行记录。"""
        conn = self.get_conn()
        row = conn.execute('''
            SELECT * FROM improvement_progress
            WHERE user_id = ? AND cycle_id = ? AND checkin_date = ?
        ''', (user_id, cycle_id, checkin_date)).fetchone()
        conn.close()
        return self._parse_improvement_progress(row) if row else None

    @staticmethod
    def _parse_improvement_cycle(row) -> Dict:
        result = dict(row)
        return {
            'id': result['id'],
            'userId': result['user_id'],
            'sourceReportId': result.get('source_report_id'),
            'status': result.get('status') or 'active',
            'plan': json.loads(result['plan_json']) if result.get('plan_json') else {},
            'baselineScore': result.get('baseline_score') or 0,
            'latestScore': result.get('latest_score') or 0,
            'targetScore': result.get('target_score') or 0,
            'startDate': result.get('start_date'),
            'targetDate': result.get('target_date'),
            'completedAt': result.get('completed_at'),
            'createdAt': result.get('created_at'),
            'updatedAt': result.get('updated_at'),
        }

    @staticmethod
    def _parse_improvement_progress(row) -> Dict:
        result = dict(row)
        return {
            'id': result['id'],
            'cycleId': result['cycle_id'],
            'userId': result['user_id'],
            'checkinDate': result['checkin_date'],
            'completedActionIds': json.loads(result['completed_action_ids']) if result.get('completed_action_ids') else [],
            'skippedActionIds': json.loads(result['skipped_action_ids']) if result.get('skipped_action_ids') else [],
            'moodScore': result.get('mood_score') or 0,
            'energyScore': result.get('energy_score') or 0,
            'note': result.get('note') or '',
            'createdAt': result.get('created_at'),
            'updatedAt': result.get('updated_at'),
        }
    
    # ═══════ 订单操作 ═══════
    
    def create_order(self, user_id: str, order_type: str, amount: int) -> Dict:
        """创建订单"""
        order_id = str(uuid.uuid4())
        order_no = f"VH{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        
        conn = self.get_conn()
        conn.execute('''
            INSERT INTO orders (id, order_no, user_id, type, amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, order_no, user_id, order_type, amount))
        conn.commit()
        
        order = self.get_order(order_id)
        conn.close()
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """获取订单"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_order_by_no(self, order_no: str) -> Optional[Dict]:
        """通过订单号获取订单"""
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM orders WHERE order_no = ?', (order_no,)).fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_order_status(self, order_id: str, status: str, payment_id: str = None) -> bool:
        """更新订单状态"""
        conn = self.get_conn()
        if status == 'paid':
            conn.execute('''
                UPDATE orders SET status = ?, payment_id = ?, paid_at = datetime('now')
                WHERE id = ?
            ''', (status, payment_id, order_id))
        else:
            conn.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        conn.commit()
        conn.close()
        return True
    
    def activate_vip(self, user_id: str, order_id: str, days: int = 30) -> bool:
        """激活VIP"""
        start_at = datetime.now()
        end_at = start_at + timedelta(days=days)
        
        conn = self.get_conn()
        
        # 创建VIP记录
        conn.execute('''
            INSERT INTO vip_records (id, user_id, order_id, type, start_at, end_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), user_id, order_id, 'monthly', 
              start_at.isoformat(), end_at.isoformat()))
        
        # 更新用户VIP状态
        conn.execute('''
            UPDATE users SET is_vip = 1, vip_expire_at = ? WHERE id = ?
        ''', (end_at.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True
    
    # ═══════ 统计查询 ═══════
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计"""
        conn = self.get_conn()
        
        voice_count = conn.execute(
            'SELECT COUNT(*) FROM voice_reports WHERE user_id = ?', (user_id,)
        ).fetchone()[0]
        
        face_count = conn.execute(
            'SELECT COUNT(*) FROM face_reports WHERE user_id = ?', (user_id,)
        ).fetchone()[0]
        
        video_count = conn.execute(
            'SELECT COUNT(*) FROM video_reports WHERE user_id = ?', (user_id,)
        ).fetchone()[0]

        combined_count = conn.execute(
            'SELECT COUNT(*) FROM combined_reports WHERE user_id = ?', (user_id,)
        ).fetchone()[0]

        checkin_count = conn.execute(
            'SELECT COUNT(*) FROM lifestyle_checkins WHERE user_id = ?', (user_id,)
        ).fetchone()[0]

        latest_checkin = conn.execute('''
            SELECT checkin_date FROM lifestyle_checkins
            WHERE user_id = ? ORDER BY checkin_date DESC LIMIT 1
        ''', (user_id,)).fetchone()
        
        # 获取最新报告
        latest_voice = conn.execute('''
            SELECT overall_score, created_at FROM voice_reports 
            WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (user_id,)).fetchone()

        score_rows = conn.execute('''
            SELECT overall_score FROM voice_reports WHERE user_id = ?
            UNION ALL
            SELECT overall_score FROM face_reports WHERE user_id = ?
            UNION ALL
            SELECT overall_score FROM video_reports WHERE user_id = ?
            UNION ALL
            SELECT overall_score FROM combined_reports WHERE user_id = ?
        ''', (user_id, user_id, user_id, user_id)).fetchall()

        scores = [float(row['overall_score'] or 0) for row in score_rows]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        best_score = round(max(scores), 1) if scores else 0

        user = conn.execute(
            'SELECT free_count, last_free_date, is_vip, vip_expire_at FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        
        conn.close()

        today = datetime.now().strftime('%Y-%m-%d')
        free_count = 0
        if user and user['last_free_date'] == today:
            free_count = int(user['free_count'] or 0)
        
        return {
            'voice_count': voice_count,
            'face_count': face_count,
            'video_count': video_count,
            'combined_count': combined_count,
            'checkin_count': checkin_count,
            'total_reports': voice_count + face_count + video_count + combined_count,
            'avg_score': avg_score,
            'best_score': best_score,
            'free_count': free_count,
            'free_remaining': max(0, 1 - free_count),
            'is_vip': bool(user['is_vip']) if user else False,
            'vip_expire_at': user['vip_expire_at'] if user else None,
            'latest_voice_score': latest_voice['overall_score'] if latest_voice else None,
            'latest_voice_date': latest_voice['created_at'] if latest_voice else None,
            'latest_checkin_date': latest_checkin['checkin_date'] if latest_checkin else None
        }

    def get_report(self, user_id: str, report_id: str) -> Optional[Dict]:
        """按ID获取任意类型报告。"""
        for report_type, getter in (
            ('voice', self.get_voice_report),
            ('face', self.get_face_report),
            ('video', self.get_video_report),
            ('combined', self.get_combined_report),
        ):
            report = getter(report_id)
            if report and report.get('user_id') == user_id:
                report['type'] = report_type
                return report
        return None

    def get_user_reports(
        self,
        user_id: str,
        report_type: str = 'all',
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """获取用户全部检测报告列表。"""
        reports: List[Dict] = []

        if report_type in ('all', 'voice'):
            for row in self.get_user_voice_reports(user_id, limit=1000, offset=0):
                row['type'] = 'voice'
                row['score'] = row.get('overall_score', 0)
                reports.append(row)

        if report_type in ('all', 'face'):
            conn = self.get_conn()
            rows = conn.execute('''
                SELECT * FROM face_reports
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,)).fetchall()
            conn.close()
            for row in rows:
                result = dict(row)
                result['type'] = 'face'
                result['score'] = result.get('overall_score', 0)
                result['dimensions'] = json.loads(result['dimensions']) if result['dimensions'] else []
                result['suggestions'] = json.loads(result['suggestions']) if result['suggestions'] else []
                reports.append(result)

        if report_type in ('all', 'video'):
            conn = self.get_conn()
            rows = conn.execute('''
                SELECT * FROM video_reports
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,)).fetchall()
            conn.close()
            for row in rows:
                result = dict(row)
                result['type'] = 'video'
                result['score'] = result.get('overall_score', 0)
                result['skin'] = json.loads(result['skin_result']) if result['skin_result'] else None
                result['eye'] = json.loads(result['eye_result']) if result['eye_result'] else None
                result['hair'] = json.loads(result['hair_result']) if result['hair_result'] else None
                result['detect_items'] = json.loads(result['detect_items']) if result['detect_items'] else []
                result['summary'] = self._video_summary(result)
                reports.append(result)

        if report_type in ('all', 'combined'):
            conn = self.get_conn()
            rows = conn.execute('''
                SELECT * FROM combined_reports
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,)).fetchall()
            conn.close()
            for row in rows:
                result = dict(row)
                result['type'] = 'combined'
                result['score'] = result.get('overall_score', 0)
                result['dimensions'] = json.loads(result['dimensions']) if result['dimensions'] else []
                result['suggestions'] = json.loads(result['suggestions']) if result['suggestions'] else []
                reports.append(result)

        reports.sort(key=lambda r: r.get('created_at') or '', reverse=True)
        return reports[offset:offset + limit]

    def delete_report(self, user_id: str, report_id: str) -> bool:
        """删除用户自己的任意类型报告。"""
        conn = self.get_conn()
        deleted = False
        for table in ('voice_reports', 'face_reports', 'video_reports', 'combined_reports'):
            cursor = conn.execute(
                f'DELETE FROM {table} WHERE id = ? AND user_id = ?',
                (report_id, user_id)
            )
            deleted = deleted or cursor.rowcount > 0

        if deleted:
            conn.execute('''
                UPDATE users
                SET total_reports = MAX(total_reports - 1, 0)
                WHERE id = ?
            ''', (user_id,))

        conn.commit()
        conn.close()
        return deleted

    @staticmethod
    def _video_summary(report: Dict) -> str:
        parts = []
        for key in ('skin', 'eye', 'hair'):
            item = report.get(key)
            if item and item.get('summary'):
                parts.append(item['summary'])
        return '；'.join(parts) or '视频健康分析已完成'
    
    def get_trend_data(self, user_id: str, days: int = 30) -> List[Dict]:
        """获取趋势数据"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT overall_score, created_at, 'voice' AS type FROM voice_reports
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            UNION ALL
            SELECT overall_score, created_at, 'face' AS type FROM face_reports
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            UNION ALL
            SELECT overall_score, created_at, 'video' AS type FROM video_reports
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            UNION ALL
            SELECT overall_score, created_at, 'combined' AS type FROM combined_reports
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at ASC
        ''', (
            user_id, f'-{days} days',
            user_id, f'-{days} days',
            user_id, f'-{days} days',
            user_id, f'-{days} days'
        )).fetchall()
        conn.close()

        return [{'score': row['overall_score'], 'date': row['created_at'], 'type': row['type']} for row in rows]


# 全局数据库实例
db = Database()


__all__ = ['Database', 'db']
