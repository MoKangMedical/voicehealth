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
                ai_insight TEXT,
                reading_text_id TEXT,
                liveness_score REAL,
                reading_match_score REAL,
                duration REAL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
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
                overall_score REAL,
                biological_age INTEGER,
                dimensions TEXT,  -- JSON
                summary TEXT,
                suggestions TEXT, -- JSON
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
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
            (id, user_id, overall_score, summary, features, risks, ai_insight, 
             reading_text_id, liveness_score, reading_match_score, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, user_id,
            report.get('overall_score', 0),
            report.get('summary', ''),
            json.dumps(report.get('features', [])),
            json.dumps(report.get('risks', [])),
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
        
        # 获取最新报告
        latest_voice = conn.execute('''
            SELECT overall_score, created_at FROM voice_reports 
            WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (user_id,)).fetchone()
        
        conn.close()
        
        return {
            'voice_count': voice_count,
            'face_count': face_count,
            'video_count': video_count,
            'total_reports': voice_count + face_count + video_count,
            'latest_voice_score': latest_voice['overall_score'] if latest_voice else None,
            'latest_voice_date': latest_voice['created_at'] if latest_voice else None
        }
    
    def get_trend_data(self, user_id: str, days: int = 30) -> List[Dict]:
        """获取趋势数据"""
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT overall_score, created_at FROM voice_reports 
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            ORDER BY created_at ASC
        ''', (user_id, f'-{days} days')).fetchall()
        conn.close()
        
        return [{'score': row['overall_score'], 'date': row['created_at']} for row in rows]


# 全局数据库实例
db = Database()


__all__ = ['Database', 'db']
