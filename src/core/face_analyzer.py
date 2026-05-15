"""
VoiceHealth — 面部分析模块

基于OpenCV的真实面部分析算法，检测以下6个维度：
1. 皱纹 (Wrinkle) - 基于边缘检测和拉普拉斯方差
2. 色斑 (Spot) - 基于HSV色彩空间的色斑检测
3. 紧致度 (Firmness) - 基于面部轮廓和边缘密度
4. 眼部 (Eye) - 基于眼部区域的黑眼圈/眼袋分析
5. 法令纹 (Nasolabial Fold) - 基于面部中下区域的沟纹检测
6. 肤色 (Skin Tone) - 基于肤色均匀度和亮度分析
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# Haar cascade路径
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_eye.xml"


@dataclass
class FaceRegion:
    """面部区域定义"""
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    @property
    def slice_2d(self) -> Tuple[slice, slice]:
        return (slice(self.y, self.y + self.h), slice(self.x, self.x + self.w))


@dataclass
class DimensionResult:
    """单维度分析结果"""
    name: str
    score: int  # 0-100
    detail: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FaceAnalysisResult:
    """面部分析完整结果"""
    face_detected: bool
    face_count: int
    overall_score: int
    predicted_age: int
    dimensions: List[DimensionResult]
    summary: str
    suggestions: List[str]

    def to_dict(self) -> dict:
        return {
            'overall_score': self.overall_score,
            'predicted_age': self.predicted_age,
            'dimensions': [
                {'name': d.name, 'score': d.score, 'detail': d.detail}
                for d in self.dimensions
            ],
            'summary': self.summary,
            'suggestions': self.suggestions
        }


class FaceAnalyzer:
    """基于OpenCV的面部分析器"""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        self.eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)
        if self.face_cascade.empty():
            raise RuntimeError(f"无法加载人脸级联分类器: {FACE_CASCADE_PATH}")
        if self.eye_cascade.empty():
            raise RuntimeError(f"无法加载眼部级联分类器: {EYE_CASCADE_PATH}")

    def analyze(self, image_path: str) -> FaceAnalysisResult:
        """
        对图片进行完整的面部分析

        Args:
            image_path: 图片文件路径

        Returns:
            FaceAnalysisResult 分析结果
        """
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return FaceAnalysisResult(
                face_detected=False, face_count=0,
                overall_score=0, predicted_age=0,
                dimensions=[], summary="无法读取图片",
                suggestions=["请上传有效的图片文件"]
            )

        # 转灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 直方图均衡化增强对比度
        gray_eq = cv2.equalizeHist(gray)

        # 人脸检测
        faces = self.face_cascade.detectMultiScale(
            gray_eq,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) == 0:
            return FaceAnalysisResult(
                face_detected=False, face_count=0,
                overall_score=0, predicted_age=0,
                dimensions=[], summary="未检测到人脸，请确保照片中包含清晰的正面人脸",
                suggestions=["请在光线充足的环境下拍摄", "请确保面部正对摄像头"]
            )

        # 取最大的人脸区域
        faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        fx, fy, fw, fh = faces_sorted[0]
        face_region = FaceRegion(int(fx), int(fy), int(fw), int(fh))

        # 提取面部ROI
        face_roi = img[fy:fy+fh, fx:fx+fw]
        face_gray = gray[fy:fy+fh, fx:fx+fw]
        face_gray_eq = gray_eq[fy:fy+fh, fx:fx+fw]

        # 检测眼部区域
        eyes = self.eye_cascade.detectMultiScale(
            face_gray_eq,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(20, 20)
        )

        # 分析各维度
        wrinkle = self._analyze_wrinkle(face_gray, face_gray_eq)
        spot = self._analyze_spots(face_roi, face_gray)
        firmness = self._analyze_firmness(face_gray, fh, fw)
        eye_result = self._analyze_eyes(face_roi, face_gray, eyes)
        nasolabial = self._analyze_nasolabial(face_gray, fh, fw)
        skin_tone = self._analyze_skin_tone(face_roi)

        dimensions = [wrinkle, spot, firmness, eye_result, nasolabial, skin_tone]

        # 计算综合分数 (加权平均)
        weights = [0.20, 0.15, 0.15, 0.20, 0.15, 0.15]
        overall = sum(d.score * w for d, w in zip(dimensions, weights))
        overall = max(30, min(98, int(overall)))

        # 根据皮肤状态估算"皮肤年龄"
        predicted_age = self._estimate_skin_age(overall, face_gray)

        # 生成总结和建议
        summary, suggestions = self._generate_summary(dimensions, overall)

        return FaceAnalysisResult(
            face_detected=True,
            face_count=len(faces),
            overall_score=overall,
            predicted_age=predicted_age,
            dimensions=dimensions,
            summary=summary,
            suggestions=suggestions
        )

    def _analyze_wrinkle(self, gray: np.ndarray, gray_eq: np.ndarray) -> DimensionResult:
        """
        皱纹检测 - 使用拉普拉斯算子和Canny边缘检测
        皱纹区域在边缘图中呈现较高密度的细线条
        """
        h, w = gray.shape[:2]

        # 重点检测区域：额头(上1/3)、眼角(两侧)、法令纹区(中下)
        forehead = gray[:h//3, w//4:3*w//4]
        left_eye_area = gray[h//4:h//2, :w//3]
        right_eye_area = gray[h//4:h//2, 2*w//3:]

        wrinkle_scores = []

        for region in [forehead, left_eye_area, right_eye_area]:
            if region.size == 0:
                continue
            # 高斯模糊去噪
            blurred = cv2.GaussianBlur(region, (3, 3), 0)
            # 拉普拉斯算子检测边缘（细纹响应更强）
            laplacian = cv2.Laplacian(blurred, cv2.CV_64F, ksize=3)
            lap_var = laplacian.var()
            # Canny边缘检测
            edges = cv2.Canny(blurred, 30, 80)
            edge_density = np.count_nonzero(edges) / edges.size if edges.size > 0 else 0

            # 综合评分：拉普拉斯方差越大 -> 纹理越复杂 -> 皱纹越多 -> 分数越低
            # 方差正常范围大约 100-2000
            lap_score = max(0, min(100, 100 - (lap_var - 100) / 20))
            # 边缘密度越高 -> 皱纹越多 -> 分数越低
            edge_score = max(0, min(100, 100 - edge_density * 500))

            wrinkle_scores.append((lap_score * 0.6 + edge_score * 0.4))

        if not wrinkle_scores:
            return DimensionResult("皱纹", 70, "数据不足")

        score = int(np.mean(wrinkle_scores))
        score = max(30, min(95, score))

        if score >= 80:
            detail = "皮肤光滑，皱纹较少"
            suggestions = ["继续保持良好的护肤习惯"]
        elif score >= 60:
            detail = "存在轻微细纹"
            suggestions = ["建议使用含视黄醇的护肤品", "注意保湿"]
        else:
            detail = "皱纹较为明显"
            suggestions = ["建议使用抗皱精华", "注意防晒减少光老化", "可考虑医美咨询"]

        return DimensionResult("皱纹", score, detail, suggestions)

    def _analyze_spots(self, face_bgr: np.ndarray, gray: np.ndarray) -> DimensionResult:
        """
        色斑检测 - 在HSV色彩空间检测颜色不均匀区域
        色斑表现为局部区域的饱和度/亮度异常
        """
        # 转换到HSV
        hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # 使用CLAHE增强亮度通道
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        v_eq = clahe.apply(v)

        # 计算亮度通道的标准差 -> 越大说明肤色越不均匀
        v_std = np.std(v_eq.astype(np.float64))
        # 计算饱和度均值 -> 高饱和可能表示色素沉着
        s_mean = np.mean(s.astype(np.float64))

        # 局部二值模式思想：用自适应阈值检测暗斑
        # 用大核的自适应阈值与原图做差，差异大的就是色斑
        thresh = cv2.adaptiveThreshold(
            v_eq, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, blockSize=31, C=10
        )
        # 开运算去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        spot_ratio = np.count_nonzero(thresh) / thresh.size if thresh.size > 0 else 0

        # 评分
        # 亮度标准差正常范围 15-40，越大越不均匀
        uniformity_score = max(0, min(100, 100 - (v_std - 15) * 2.5))
        # 色斑比例评分
        spot_score = max(0, min(100, 100 - spot_ratio * 300))
        # 饱和度评分
        sat_score = max(0, min(100, 100 - max(0, s_mean - 40) * 1.5))

        score = int(uniformity_score * 0.4 + spot_score * 0.4 + sat_score * 0.2)
        score = max(30, min(95, score))

        if score >= 80:
            detail = "肤色均匀，色斑不明显"
            suggestions = ["做好日常防晒即可"]
        elif score >= 60:
            detail = "存在轻微色斑或色素不均"
            suggestions = ["加强防晒(SPF30+)", "可使用美白精华"]
        else:
            detail = "色斑较明显，建议关注"
            suggestions = ["务必做好防晒", "建议使用维C/烟酰胺类产品", "如持续加重建议皮肤科就诊"]

        return DimensionResult("色斑", score, detail, suggestions)

    def _analyze_firmness(self, gray: np.ndarray, face_h: int, face_w: int) -> DimensionResult:
        """
        紧致度分析 - 基于面部轮廓清晰度和边缘密度
        紧致的面部轮廓边缘更清晰，松驰的面部边缘模糊
        """
        # 检测面部下半部分的轮廓（下颌线区域）
        lower_face = gray[face_h // 2:, :]

        if lower_face.size == 0:
            return DimensionResult("紧致度", 70, "数据不足")

        # Canny边缘检测
        blurred = cv2.GaussianBlur(lower_face, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 100)

        # 计算边缘密度
        edge_density = np.count_nonzero(edges) / edges.size if edges.size > 0 else 0

        # Sobel算子检测水平方向梯度（下颌线主要是水平方向的梯度）
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobel_x_abs = np.abs(sobel_x)
        gradient_strength = np.mean(sobel_x_abs)

        # 霍夫线检测 - 检测下颌线区域是否有清晰线条
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=30,
                                 minLineLength=face_w // 6, maxLineGap=10)
        line_count = len(lines) if lines is not None else 0

        # 评分
        # 边缘密度适中为佳（太低=模糊，太高=噪点多）
        edge_score = max(0, min(100, 100 - abs(edge_density - 0.08) * 800))
        # 梯度强度越大越好
        grad_score = max(0, min(100, gradient_strength * 1.5))
        # 线条检测数量（越多说明轮廓越清晰）
        line_score = max(0, min(100, line_count * 15))

        score = int(edge_score * 0.3 + grad_score * 0.4 + line_score * 0.3)
        score = max(30, min(95, score))

        if score >= 80:
            detail = "面部轮廓紧致"
            suggestions = ["保持良好的运动习惯"]
        elif score >= 60:
            detail = "紧致度一般"
            suggestions = ["建议增加面部运动", "注意补水保湿"]
        else:
            detail = "面部轮廓略显松驰"
            suggestions = ["建议做面部提拉按摩", "补充胶原蛋白", "可考虑射频紧肤等医美项目"]

        return DimensionResult("紧致度", score, detail, suggestions)

    def _analyze_eyes(self, face_bgr: np.ndarray, gray: np.ndarray,
                      eyes: np.ndarray) -> DimensionResult:
        """
        眼部分析 - 检测黑眼圈和眼袋
        通过分析眼下区域的亮度和颜色来评估
        """
        h, w = gray.shape[:2]

        # 默认眼部区域（面部上半部分的下半区域）
        eye_region_y1 = h // 4
        eye_region_y2 = h // 2
        under_eye_y1 = h // 2
        under_eye_y2 = int(h * 0.65)

        # 如果检测到眼睛，更精确地定位眼下区域
        if len(eyes) >= 1:
            eye_ys = [ey for (_, ey, _, eh) in eyes]
            eye_bottoms = [ey + eh for (_, ey, _, eh) in eyes]
            under_eye_y1 = max(int(min(eye_bottoms)), h // 3)
            under_eye_y2 = min(int(max(eye_bottoms) + h * 0.15), h)
            eye_region_y1 = max(int(min(eye_ys) - h * 0.05), 0)
            eye_region_y2 = min(int(max(eye_bottoms) + h * 0.05), h)

        # 提取眼下区域
        under_eye = gray[under_eye_y1:under_eye_y2, :]
        eye_area = gray[eye_region_y1:eye_region_y2, :]

        if under_eye.size == 0 or eye_area.size == 0:
            return DimensionResult("眼部", 70, "数据不足")

        # 黑眼圈检测：眼下区域的平均亮度 vs 面部平均亮度
        face_mean = np.mean(gray.astype(np.float64))
        under_eye_mean = np.mean(under_eye.astype(np.float64))

        # 眼下区域比面部其他区域暗的程度 -> 黑眼圈
        darkness_diff = face_mean - under_eye_mean
        # 眼下区域的纹理复杂度 -> 眼袋/细纹
        under_eye_lap = cv2.Laplacian(under_eye, cv2.CV_64F, ksize=3)
        under_eye_texture = under_eye_lap.var()

        # 检测眼下区域的HSV颜色（发青/发黑）
        hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
        under_eye_hsv = hsv[under_eye_y1:under_eye_y2, :]
        under_eye_s_mean = np.mean(under_eye_hsv[:, :, 1].astype(np.float64))

        # 评分
        # 亮度差异越小越好
        dark_score = max(0, min(100, 100 - max(0, darkness_diff - 5) * 3))
        # 纹理越简单越好（眼袋不明显）
        texture_score = max(0, min(100, 100 - max(0, under_eye_texture - 50) / 10))
        # 饱和度（低饱和度的暗区=黑眼圈）
        color_score = max(0, min(100, 80 - max(0, 20 - under_eye_s_mean) * 2))

        score = int(dark_score * 0.5 + texture_score * 0.3 + color_score * 0.2)
        score = max(30, min(95, score))

        if score >= 80:
            detail = "眼部状态良好，无明显黑眼圈"
            suggestions = ["保持充足睡眠"]
        elif score >= 60:
            detail = "存在轻微黑眼圈或眼袋"
            suggestions = ["保证每天7-8小时睡眠", "可使用含咖啡因的眼霜"]
        else:
            detail = "黑眼圈/眼袋较为明显"
            suggestions = ["建议充足睡眠并减少熬夜", "冷敷可缓解黑眼圈", "如持续不退建议就医排查"]

        return DimensionResult("眼部", score, detail, suggestions)

    def _analyze_nasolabial(self, gray: np.ndarray, face_h: int,
                            face_w: int) -> DimensionResult:
        """
        法令纹检测 - 分析鼻翼到嘴角区域的沟纹深度
        使用垂直方向的梯度检测和局部对比度分析
        """
        # 法令纹区域：面部中下1/3，鼻翼两侧
        y1 = int(face_h * 0.35)
        y2 = int(face_h * 0.75)

        # 左侧法令纹区域（图像右侧，因为是镜像）
        left_area = gray[y1:y2, face_w // 2:3 * face_w // 4]
        # 右侧法令纹区域
        right_area = gray[y1:y2, face_w // 4:face_w // 2]

        scores = []
        for area in [left_area, right_area]:
            if area.size == 0:
                continue

            # 高斯模糊
            blurred = cv2.GaussianBlur(area, (3, 3), 0)

            # Sobel垂直方向梯度（法令纹主要是垂直走向）
            sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
            sobel_y_abs = np.abs(sobel_y)
            grad_strength = np.mean(sobel_y_abs)

            # 局部对比度：用大窗口的均值和小窗口的标准差
            local_std = np.std(blurred.astype(np.float64))

            # Canny边缘中垂直线条的密度
            edges = cv2.Canny(blurred, 25, 70)
            edge_density = np.count_nonzero(edges) / edges.size if edges.size > 0 else 0

            # 梯度越大、对比度越高、边缘越密 -> 法令纹越深 -> 分数越低
            grad_score = max(0, min(100, 100 - grad_strength * 2))
            contrast_score = max(0, min(100, 100 - max(0, local_std - 15) * 2))
            edge_score = max(0, min(100, 100 - edge_density * 600))

            scores.append(grad_score * 0.4 + contrast_score * 0.3 + edge_score * 0.3)

        if not scores:
            return DimensionResult("法令纹", 70, "数据不足")

        score = int(np.mean(scores))
        score = max(30, min(95, score))

        if score >= 80:
            detail = "法令纹不明显"
            suggestions = ["注意面部表情管理"]
        elif score >= 60:
            detail = "法令纹初现"
            suggestions = ["加强面部保湿", "可使用含肽类的抗皱产品"]
        else:
            detail = "法令纹较深"
            suggestions = ["建议使用透明质酸填充类护肤品", "面部提拉按摩有助于改善", "可咨询医美方案"]

        return DimensionResult("法令纹", score, detail, suggestions)

    def _analyze_skin_tone(self, face_bgr: np.ndarray) -> DimensionResult:
        """
        肤色分析 - 基于LAB和HSV色彩空间分析肤色均匀度和健康度
        """
        # 转换到LAB色彩空间（更适合肤色分析）
        lab = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # 转换到HSV
        hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)

        # LAB空间分析
        l_mean = np.mean(l_channel.astype(np.float64))  # 亮度
        l_std = np.std(l_channel.astype(np.float64))  # 亮度均匀度
        a_mean = np.mean(a_channel.astype(np.float64))  # 红绿色度
        b_mean = np.mean(b_channel.astype(np.float64))  # 黄蓝色度

        # HSV空间分析
        s_mean = np.mean(s_channel.astype(np.float64))  # 饱和度
        v_mean = np.mean(v_channel.astype(np.float64))  # 明度
        v_std = np.std(v_channel.astype(np.float64))  # 明度均匀度

        # 评分
        # 亮度适中(120-180)为佳
        brightness_score = max(0, min(100, 100 - abs(l_mean - 150) * 0.8))
        # 均匀度：标准差越小越好
        uniformity_score = max(0, min(100, 100 - l_std * 2))
        # 饱和度适中(40-100)为健康肤色
        sat_score = max(0, min(100, 100 - abs(s_mean - 65) * 1.2))
        # 明度均匀度
        v_uniformity = max(0, min(100, 100 - v_std * 2))

        score = int(
            brightness_score * 0.25 +
            uniformity_score * 0.30 +
            sat_score * 0.20 +
            v_uniformity * 0.25
        )
        score = max(30, min(95, score))

        if score >= 80:
            detail = "肤色均匀健康，光泽度好"
            suggestions = ["坚持日常防晒和保湿"]
        elif score >= 60:
            detail = "肤色基本均匀，略有暗沉"
            suggestions = ["注意防晒", "可使用提亮肤色的精华", "保持规律作息"]
        else:
            detail = "肤色暗沉或不均匀"
            suggestions = ["加强防晒(SPF50+)", "使用维C类产品提亮肤色", "保持充足饮水和睡眠"]

        return DimensionResult("肤色", score, detail, suggestions)

    def _estimate_skin_age(self, overall_score: int, gray: np.ndarray) -> int:
        """根据皮肤状态估算皮肤年龄"""
        # 基础年龄 25，根据综合分数上下浮动
        # overall_score 越高 -> 皮肤越好 -> 年龄越年轻
        base_age = 25
        age_offset = (75 - overall_score) * 0.3  # 每差1分年龄偏移0.3岁

        # 加入纹理复杂度的影响
        lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)
        texture = lap.var()
        texture_offset = max(0, (texture - 200) / 200) * 2

        estimated = int(base_age + age_offset + texture_offset)
        return max(18, min(60, estimated))

    def _generate_summary(self, dimensions: List[DimensionResult],
                          overall: int) -> Tuple[str, List[str]]:
        """生成总结和建议"""
        all_suggestions = []
        low_dims = []
        high_dims = []

        for d in dimensions:
            all_suggestions.extend(d.suggestions)
            if d.score < 60:
                low_dims.append(d.name)
            elif d.score >= 80:
                high_dims.append(d.name)

        if overall >= 85:
            summary = "皮肤状态优秀，整体健康！"
        elif overall >= 70:
            summary = "皮肤状态良好，部分维度有提升空间。"
        elif overall >= 55:
            summary = "皮肤状态一般，建议加强护理。"
        else:
            summary = "皮肤状态需要关注，建议采取针对性护理措施。"

        if low_dims:
            summary += f" {', '.join(low_dims)}方面需要重点关注。"
        if high_dims:
            summary += f" {', '.join(high_dims)}方面表现良好。"

        # 去重并限制建议数量
        seen = set()
        unique_suggestions = []
        for s in all_suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)

        return summary, unique_suggestions[:5]
