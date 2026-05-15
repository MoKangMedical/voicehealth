"""
视频分析模块
基于OpenCV实现视频帧提取和健康状态分析
分析维度：皮肤状态、眼睛状态、头发状态
"""
import cv2
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import os


@dataclass
class SkinAnalysis:
    """皮肤分析结果"""
    skin_tone: str = "未知"  # 肤色类型
    skin_brightness: float = 0.0  # 皮肤亮度 (0-255)
    skin_uniformity: float = 0.0  # 肤色均匀度 (0-1)
    texture_score: float = 0.0  # 纹理粗糙度 (0-1, 越高越粗糙)
    dark_circles_score: float = 0.0  # 黑眼圈程度 (0-1, 越高越严重)
    redness_score: float = 0.0  # 泛红程度 (0-1)
    oiliness_score: float = 0.0  # 油光程度 (0-1)
    health_score: float = 0.0  # 综合皮肤健康评分 (0-100)
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class EyeAnalysis:
    """眼睛分析结果"""
    eye_openness: float = 0.0  # 眼睛开合度 (0-1)
    eye_symmetry: float = 0.0  # 双眼对称性 (0-1)
    blink_rate: float = 0.0  # 估计眨眼频率 (次/分钟)
    fatigue_score: float = 0.0  # 疲劳程度 (0-1, 越高越疲劳)
    redness_score: float = 0.0  # 眼睛充血程度 (0-1)
    sclera_brightness: float = 0.0  # 巩膜(眼白)亮度
    health_score: float = 0.0  # 综合眼睛健康评分 (0-100)
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class HairAnalysis:
    """头发分析结果"""
    hair_coverage: float = 0.0  # 头发覆盖率 (0-1)
    hair_color: str = "未知"  # 头发颜色类型
    hair_shine: float = 0.0  # 头发光泽度 (0-1)
    hair_uniformity: float = 0.0  # 头发均匀度 (0-1)
    dryness_score: float = 0.0  # 干燥程度 (0-1)
    health_score: float = 0.0  # 综合头发健康评分 (0-100)
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class VideoAnalysisResult:
    """视频分析综合结果"""
    skin: SkinAnalysis = None
    eye: EyeAnalysis = None
    hair: HairAnalysis = None
    frame_count: int = 0
    video_duration: float = 0.0
    overall_health_score: float = 0.0
    summary: str = ""

    def __post_init__(self):
        if self.skin is None:
            self.skin = SkinAnalysis()
        if self.eye is None:
            self.eye = EyeAnalysis()
        if self.hair is None:
            self.hair = HairAnalysis()

    def to_dict(self):
        return {
            "skin": self.skin.to_dict(),
            "eye": self.eye.to_dict(),
            "hair": self.hair.to_dict(),
            "frame_count": self.frame_count,
            "video_duration": self.video_duration,
            "overall_health_score": self.overall_health_score,
            "summary": self.summary,
        }


class VideoAnalyzer:
    """视频分析器 - 使用OpenCV进行人脸健康状态分析"""

    def __init__(self, face_cascade_path: Optional[str] = None):
        """
        初始化视频分析器
        
        Args:
            face_cascade_path: Haar级联分类器路径，如果为None则使用OpenCV自带的
        """
        # 加载人脸检测器
        if face_cascade_path and os.path.exists(face_cascade_path):
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
        else:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # 加载眼睛检测器
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        
        # 分析参数
        self.max_frames = 100  # 最多分析帧数
        self.sample_interval = 1  # 每隔多少帧采样一次

    def analyze_video(self, video_path: str) -> VideoAnalysisResult:
        """
        分析视频文件
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            VideoAnalysisResult: 分析结果
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"无法打开视频文件: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # 计算采样间隔
            if total_frames > self.max_frames:
                self.sample_interval = max(1, total_frames // self.max_frames)
            else:
                self.sample_interval = 1

            # 收集所有采样帧的分析数据
            skin_data_list = []
            eye_data_list = []
            hair_data_list = []
            analyzed_frames = 0

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % self.sample_interval == 0:
                    # 缩小帧以加速处理
                    small_frame = self._resize_frame(frame, max_width=640)
                    
                    # 检测人脸
                    faces = self._detect_faces(small_frame)
                    
                    if len(faces) > 0:
                        face = max(faces, key=lambda f: f[2] * f[3])  # 选最大的人脸
                        
                        # 分析各个维度
                        skin_data = self._analyze_skin(small_frame, face)
                        eye_data = self._analyze_eyes(small_frame, face)
                        hair_data = self._analyze_hair(small_frame, face)
                        
                        skin_data_list.append(skin_data)
                        eye_data_list.append(eye_data)
                        hair_data_list.append(hair_data)
                    
                    analyzed_frames += 1

                frame_idx += 1

            # 汇总分析结果
            result = VideoAnalysisResult()
            result.frame_count = analyzed_frames
            result.video_duration = round(duration, 2)

            if skin_data_list:
                result.skin = self._aggregate_skin(skin_data_list)
            if eye_data_list:
                result.eye = self._aggregate_eyes(eye_data_list, duration)
            if hair_data_list:
                result.hair = self._aggregate_hair(hair_data_list)

            # 计算综合健康评分
            scores = []
            if result.skin.health_score > 0:
                scores.append(result.skin.health_score)
            if result.eye.health_score > 0:
                scores.append(result.eye.health_score)
            if result.hair.health_score > 0:
                scores.append(result.hair.health_score)
            
            if scores:
                result.overall_health_score = round(np.mean(scores), 1)

            result.summary = self._generate_summary(result)
            return result

        finally:
            cap.release()

    def analyze_frame(self, frame: np.ndarray) -> VideoAnalysisResult:
        """
        分析单帧图像
        
        Args:
            frame: BGR格式的图像数组
            
        Returns:
            VideoAnalysisResult: 分析结果
        """
        small_frame = self._resize_frame(frame, max_width=640)
        faces = self._detect_faces(small_frame)

        result = VideoAnalysisResult()
        result.frame_count = 1

        if len(faces) > 0:
            face = max(faces, key=lambda f: f[2] * f[3])
            result.skin = self._analyze_skin_single(small_frame, face)
            result.eye = self._analyze_eyes_single(small_frame, face)
            result.hair = self._analyze_hair_single(small_frame, face)

            scores = []
            if result.skin.health_score > 0:
                scores.append(result.skin.health_score)
            if result.eye.health_score > 0:
                scores.append(result.eye.health_score)
            if result.hair.health_score > 0:
                scores.append(result.hair.health_score)
            if scores:
                result.overall_health_score = round(np.mean(scores), 1)

        result.summary = self._generate_summary(result)
        return result

    # ==================== 内部方法 ====================

    def _resize_frame(self, frame: np.ndarray, max_width: int = 640) -> np.ndarray:
        """缩放帧"""
        h, w = frame.shape[:2]
        if w <= max_width:
            return frame
        scale = max_width / w
        return cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    def _detect_faces(self, frame: np.ndarray) -> list:
        """检测人脸，返回(x, y, w, h)列表"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
        return list(faces) if len(faces) > 0 else []

    def _get_face_roi(self, frame: np.ndarray, face: tuple) -> Tuple[np.ndarray, tuple]:
        """获取人脸ROI区域"""
        x, y, w, h = face
        # 扩展区域以包含额头和下巴
        pad_x = int(w * 0.1)
        pad_y = int(h * 0.2)
        fh, fw = frame.shape[:2]
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(fw, x + w + pad_x)
        y2 = min(fh, y + h + pad_y)
        roi = frame[y1:y2, x1:x2]
        return roi, (x1, y1, x2 - x1, y2 - y1)

    def _get_skin_mask(self, roi: np.ndarray) -> np.ndarray:
        """提取皮肤区域掩码（基于HSV颜色空间）"""
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # 皮肤颜色范围（HSV）
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([25, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        # 形态学操作去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    # ==================== 皮肤分析 ====================

    def _analyze_skin(self, frame: np.ndarray, face: tuple) -> dict:
        roi, _ = self._get_face_roi(frame, face)
        return self._compute_skin_metrics(roi)

    def _analyze_skin_single(self, frame: np.ndarray, face: tuple) -> SkinAnalysis:
        roi, _ = self._get_face_roi(frame, face)
        metrics = self._compute_skin_metrics(roi)
        return self._aggregate_skin([metrics])

    def _compute_skin_metrics(self, roi: np.ndarray) -> dict:
        """计算皮肤指标"""
        skin_mask = self._get_skin_mask(roi)
        skin_pixels = roi[skin_mask > 0]
        
        if len(skin_pixels) < 100:
            return {}

        # 转换到不同颜色空间
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        skin_hsv = hsv[skin_mask > 0]
        skin_lab = lab[skin_mask > 0]
        skin_gray = gray[skin_mask > 0]

        # 1. 皮肤亮度
        brightness = float(np.mean(skin_gray))
        
        # 2. 肤色均匀度（亮度标准差越小越均匀）
        brightness_std = float(np.std(skin_gray))
        uniformity = max(0, 1.0 - brightness_std / 80.0)
        
        # 3. 纹理粗糙度（使用拉普拉斯算子）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_score = min(1.0, float(np.std(laplacian)) / 50.0)
        
        # 4. 泛红程度（红色通道偏高）
        redness = float(np.mean(skin_hsv[:, 0])) / 180.0  # H通道
        
        # 5. 油光程度（高亮度像素占比）
        highlight_mask = skin_gray > 200
        oiliness = float(np.sum(highlight_mask)) / max(1, len(skin_gray))
        
        # 6. 肤色类型判定
        mean_b = float(np.mean(skin_pixels[:, 0]))
        mean_g = float(np.mean(skin_pixels[:, 1]))
        mean_r = float(np.mean(skin_pixels[:, 2]))
        if brightness < 100:
            tone = "偏暗"
        elif brightness > 180:
            tone = "偏白"
        else:
            tone = "正常"

        # 综合评分
        health = 100.0
        health -= texture_score * 20  # 纹理越粗糙扣分
        health -= (1 - uniformity) * 15  # 不均匀扣分
        health -= oiliness * 15  # 油光扣分
        health -= max(0, brightness - 200) * 0.3  # 过亮扣分
        health -= max(0, 80 - brightness) * 0.3  # 过暗扣分
        health = max(0, min(100, health))

        return {
            "brightness": brightness,
            "uniformity": round(uniformity, 3),
            "texture_score": round(texture_score, 3),
            "redness": round(redness, 3),
            "oiliness": round(oiliness, 3),
            "tone": tone,
            "health_score": round(health, 1),
        }

    def _aggregate_skin(self, data_list: list) -> SkinAnalysis:
        """汇总多帧皮肤数据"""
        valid = [d for d in data_list if d]
        if not valid:
            return SkinAnalysis()

        result = SkinAnalysis()
        result.skin_brightness = round(float(np.mean([d["brightness"] for d in valid])), 1)
        result.skin_uniformity = round(float(np.mean([d["uniformity"] for d in valid])), 3)
        result.texture_score = round(float(np.mean([d["texture_score"] for d in valid])), 3)
        result.redness_score = round(float(np.mean([d["redness"] for d in valid])), 3)
        result.oiliness_score = round(float(np.mean([d["oiliness"] for d in valid])), 3)
        result.health_score = round(float(np.mean([d["health_score"] for d in valid])), 1)

        # 取众数作为肤色类型
        tones = [d["tone"] for d in valid]
        result.skin_tone = max(set(tones), key=tones.count)

        # 生成摘要
        issues = []
        if result.texture_score > 0.4:
            issues.append("皮肤纹理较粗糙")
        if result.skin_uniformity < 0.5:
            issues.append("肤色不够均匀")
        if result.oiliness_score > 0.3:
            issues.append("面部有油光")
        if result.skin_brightness < 80:
            issues.append("面部偏暗")
        if result.skin_brightness > 200:
            issues.append("面部过亮")
        
        if issues:
            result.summary = "皮肤状态: " + "; ".join(issues)
        else:
            result.summary = "皮肤状态良好"

        return result

    # ==================== 眼睛分析 ====================

    def _analyze_eyes(self, frame: np.ndarray, face: tuple) -> dict:
        roi, roi_rect = self._get_face_roi(frame, face)
        return self._compute_eye_metrics(roi, roi_rect, frame)

    def _analyze_eyes_single(self, frame: np.ndarray, face: tuple) -> EyeAnalysis:
        roi, roi_rect = self._get_face_roi(frame, face)
        metrics = self._compute_eye_metrics(roi, roi_rect, frame)
        if not metrics:
            return EyeAnalysis()
        return self._aggregate_eyes([metrics], 0)

    def _compute_eye_metrics(self, roi: np.ndarray, roi_rect: tuple, full_frame: np.ndarray) -> dict:
        """计算眼睛指标"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 检测眼睛（在人脸上半部分）
        h, w = gray.shape
        upper_half = gray[0:int(h * 0.6), :]
        upper_roi = roi[0:int(h * 0.6), :]
        
        eyes = self.eye_cascade.detectMultiScale(
            upper_half, scaleFactor=1.1, minNeighbors=5, minSize=(20, 15)
        )
        
        if len(eyes) < 1:
            return {}

        # 取最大的两个眼睛
        eyes_sorted = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
        
        # 眼睛开合度（通过眼睛区域亮度变化判断）
        eye_openness_list = []
        eye_redness_list = []
        
        for (ex, ey, ew, eh) in eyes_sorted:
            eye_region = upper_roi[ey:ey+eh, ex:ex+ew]
            if eye_region.size == 0:
                continue
            
            eye_gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
            
            # 开合度：使用边缘密度作为指标（眼睛睁开时边缘更丰富）
            edges = cv2.Canny(eye_gray, 50, 150)
            edge_density = float(np.sum(edges > 0)) / max(1, edges.size)
            openness = min(1.0, edge_density * 5)  # 归一化
            eye_openness_list.append(openness)
            
            # 眼睛充血：检测红色分量
            eye_hsv = cv2.cvtColor(eye_region, cv2.COLOR_BGR2HSV)
            # 红色在HSV中的范围
            red_mask = cv2.inRange(eye_hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
            redness = float(np.sum(red_mask > 0)) / max(1, red_mask.size)
            eye_redness_list.append(redness)

        if not eye_openness_list:
            return {}

        # 眼睛对称性
        symmetry = 1.0
        if len(eye_openness_list) == 2:
            diff = abs(eye_openness_list[0] - eye_openness_list[1])
            symmetry = max(0, 1.0 - diff * 5)

        mean_openness = float(np.mean(eye_openness_list))
        mean_redness = float(np.mean(eye_redness_list)) if eye_redness_list else 0

        # 疲劳度（眼睛开合度低 = 更疲劳）
        fatigue = max(0, 1.0 - mean_openness * 2)

        # 巩膜亮度
        sclera_brightness = 0
        for (ex, ey, ew, eh) in eyes_sorted:
            eye_region = upper_roi[ey:ey+eh, ex:ex+ew]
            if eye_region.size == 0:
                continue
            eye_gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
            # 巩膜通常是眼睛区域中最亮的部分
            sclera_brightness += float(np.percentile(eye_gray, 90))
        sclera_brightness /= max(1, len(eyes_sorted))

        # 健康评分
        health = 100.0
        health -= fatigue * 30  # 疲劳扣分
        health -= mean_redness * 200  # 充血扣分
        health -= (1 - symmetry) * 15  # 不对称扣分
        health = max(0, min(100, health))

        return {
            "openness": round(mean_openness, 3),
            "symmetry": round(symmetry, 3),
            "redness": round(mean_redness, 4),
            "fatigue": round(fatigue, 3),
            "sclera_brightness": round(sclera_brightness, 1),
            "health_score": round(health, 1),
        }

    def _aggregate_eyes(self, data_list: list, duration: float) -> EyeAnalysis:
        """汇总多帧眼睛数据"""
        valid = [d for d in data_list if d]
        if not valid:
            return EyeAnalysis()

        result = EyeAnalysis()
        result.eye_openness = round(float(np.mean([d["openness"] for d in valid])), 3)
        result.eye_symmetry = round(float(np.mean([d["symmetry"] for d in valid])), 3)
        result.redness_score = round(float(np.mean([d["redness"] for d in valid])), 4)
        result.fatigue_score = round(float(np.mean([d["fatigue"] for d in valid])), 3)
        result.sclera_brightness = round(float(np.mean([d["sclera_brightness"] for d in valid])), 1)
        result.health_score = round(float(np.mean([d["health_score"] for d in valid])), 1)

        # 估算眨眼频率
        if duration > 0 and len(valid) > 2:
            # 通过开合度变化检测眨眼
            openness_values = [d["openness"] for d in valid]
            threshold = np.mean(openness_values) * 0.6
            blink_count = 0
            in_blink = False
            for val in openness_values:
                if val < threshold and not in_blink:
                    blink_count += 1
                    in_blink = True
                elif val >= threshold:
                    in_blink = False
            result.blink_rate = round(blink_count / (duration / 60.0), 1) if duration > 0 else 0
        else:
            result.blink_rate = 0

        # 生成摘要
        issues = []
        if result.fatigue_score > 0.5:
            issues.append("眼睛疲劳明显")
        if result.redness_score > 0.05:
            issues.append("眼睛有充血现象")
        if result.eye_symmetry < 0.7:
            issues.append("双眼开合不对称")
        if result.blink_rate > 0 and (result.blink_rate < 10 or result.blink_rate > 30):
            issues.append(f"眨眼频率异常({result.blink_rate}次/分)")
        
        if issues:
            result.summary = "眼睛状态: " + "; ".join(issues)
        else:
            result.summary = "眼睛状态正常"

        return result

    # ==================== 头发分析 ====================

    def _analyze_hair(self, frame: np.ndarray, face: tuple) -> dict:
        roi, _ = self._get_face_roi(frame, face)
        return self._compute_hair_metrics(roi, frame)

    def _analyze_hair_single(self, frame: np.ndarray, face: tuple) -> HairAnalysis:
        roi, _ = self._get_face_roi(frame, face)
        metrics = self._compute_hair_metrics(roi, frame)
        if not metrics:
            return HairAnalysis()
        return self._aggregate_hair([metrics])

    def _compute_hair_metrics(self, roi: np.ndarray, full_frame: np.ndarray) -> dict:
        """计算头发指标"""
        h, w = roi.shape[:2]
        
        # 头发区域通常在人脸ROI的上方
        # 取人脸顶部上方的区域作为头发候选区域
        hair_region = roi[0:int(h * 0.35), :]
        if hair_region.size == 0:
            return {}

        # 转换颜色空间
        hsv = cv2.cvtColor(hair_region, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(hair_region, cv2.COLOR_BGR2GRAY)
        
        # 头发颜色检测（深色头发的HSV范围）
        # 暗色头发：低亮度、低饱和度
        dark_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
        # 棕色头发
        brown_mask = cv2.inRange(hsv, np.array([10, 30, 30]), np.array([25, 200, 200]))
        
        # 综合头发掩码
        hair_mask = cv2.bitwise_or(dark_mask, brown_mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
        
        hair_pixels = hair_region[hair_mask > 0]
        total_pixels = hair_region.shape[0] * hair_region.shape[1]
        
        if len(hair_pixels) < total_pixels * 0.05:
            return {}

        # 1. 头发覆盖率
        coverage = len(hair_pixels) / max(1, total_pixels)
        
        # 2. 头发颜色类型
        mean_brightness = float(np.mean(hair_pixels[:, 2])) if len(hair_pixels) > 0 else 0
        if mean_brightness < 40:
            color = "深黑色"
        elif mean_brightness < 80:
            color = "深棕色"
        elif mean_brightness < 130:
            color = "棕色"
        else:
            color = "浅色"
        
        # 3. 头发光泽度（高亮度像素占比）
        hair_gray = gray[hair_mask > 0]
        if len(hair_gray) > 0:
            highlights = np.sum(hair_gray > np.percentile(hair_gray, 90))
            shine = min(1.0, float(highlights) / max(1, len(hair_gray)) * 3)
        else:
            shine = 0
        
        # 4. 头发均匀度
        if len(hair_gray) > 0:
            uniformity = max(0, 1.0 - float(np.std(hair_gray)) / 60.0)
        else:
            uniformity = 0
        
        # 5. 干燥度（纹理分析）
        if len(hair_gray) > 0:
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            hair_lap = laplacian[hair_mask > 0]
            dryness = min(1.0, float(np.std(hair_lap)) / 40.0)
        else:
            dryness = 0

        # 健康评分
        health = 100.0
        health -= dryness * 25  # 干燥扣分
        health -= (1 - uniformity) * 20  # 不均匀扣分
        health -= (1 - shine) * 15  # 无光泽扣分
        health -= max(0, coverage - 0.8) * 50  # 覆盖率异常扣分
        health = max(0, min(100, health))

        return {
            "coverage": round(coverage, 3),
            "color": color,
            "shine": round(shine, 3),
            "uniformity": round(uniformity, 3),
            "dryness": round(dryness, 3),
            "health_score": round(health, 1),
        }

    def _aggregate_hair(self, data_list: list) -> HairAnalysis:
        """汇总多帧头发数据"""
        valid = [d for d in data_list if d]
        if not valid:
            return HairAnalysis()

        result = HairAnalysis()
        result.hair_coverage = round(float(np.mean([d["coverage"] for d in valid])), 3)
        result.hair_shine = round(float(np.mean([d["shine"] for d in valid])), 3)
        result.hair_uniformity = round(float(np.mean([d["uniformity"] for d in valid])), 3)
        result.dryness_score = round(float(np.mean([d["dryness"] for d in valid])), 3)
        result.health_score = round(float(np.mean([d["health_score"] for d in valid])), 1)

        # 取众数作为颜色
        colors = [d["color"] for d in valid]
        result.hair_color = max(set(colors), key=colors.count)

        # 生成摘要
        issues = []
        if result.dryness_score > 0.4:
            issues.append("头发较干燥")
        if result.hair_shine < 0.3:
            issues.append("头发缺乏光泽")
        if result.hair_uniformity < 0.5:
            issues.append("头发均匀度较差")
        
        if issues:
            result.summary = "头发状态: " + "; ".join(issues)
        else:
            result.summary = "头发状态良好"

        return result

    # ==================== 辅助方法 ====================

    def _generate_summary(self, result: VideoAnalysisResult) -> str:
        """生成综合分析摘要"""
        parts = []
        
        if result.overall_health_score >= 80:
            parts.append("整体健康状态良好")
        elif result.overall_health_score >= 60:
            parts.append("整体健康状态一般")
        else:
            parts.append("整体健康状态需关注")

        if result.skin.summary:
            parts.append(result.skin.summary)
        if result.eye.summary:
            parts.append(result.eye.summary)
        if result.hair.summary:
            parts.append(result.hair.summary)

        return "。".join(parts) + "。" if parts else "未检测到足够的人脸区域进行分析。"
