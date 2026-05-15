"""
VoiceHealth evidence base and user guidance.

This module stores platform-facing scientific rationale, references, collection
protocols, result interpretation guidance, and compliance boundaries. Content is
for health management reference only and does not create diagnostic claims.
"""

from datetime import date
from typing import Dict, List


THEORY_FOUNDATIONS: List[Dict] = [
    {
        "icon": "🫁",
        "title": "声音来自呼吸-发声-共鸣-构音链路",
        "desc": "一次朗读同时调动肺部气流、声带振动、咽喉共鸣、口腔舌唇构音和中枢控制。气息、音高、音质、停顿、语速和频谱变化，可作为健康管理的可解释线索。",
        "basis": "Voice production pathway; acoustic voice assessment; speech signal analysis reviews",
    },
    {
        "icon": "📈",
        "title": "声学特征适合做趋势参考",
        "desc": "单次语音容易受环境、设备、情绪、感冒和睡眠影响。平台重点看同一用户在相似环境下的连续趋势，而不是把一次结果当作诊断结论。",
        "basis": "Digital measure validation and vocal biomarker protocol literature",
    },
    {
        "icon": "🔬",
        "title": "特征必须可解释",
        "desc": "当前模型使用F0、Jitter、Shimmer、HNR、能量、停顿、语速、频谱、MFCC、信噪估计等指标，并把每个风险提示映射到对应声学标志物。",
        "basis": "Acoustic analysis and voice disorder assessment practice",
    },
    {
        "icon": "🧭",
        "title": "结果按大健康维度组织",
        "desc": "能力范围覆盖呼吸与气道、嗓音与喉部、神经运动、心理与压力、睡眠与疲劳、认知与沟通、心肺活力和总体活力。",
        "basis": "Systematic reviews across respiratory, neurological, psychiatric, and cardiopulmonary speech studies",
    },
    {
        "icon": "✅",
        "title": "验证分三层推进",
        "desc": "平台按V3思路区分技术验证、分析验证和临床验证。当前上线定位是健康参考；若未来声称筛查、诊断或治疗辅助，需要进入医疗器械和临床验证路径。",
        "basis": "Verification, analytical validation, clinical validation framework",
    },
]


EVIDENCE_REFERENCES: List[Dict] = [
    {
        "category": "总框架",
        "title": "Master protocols in vocal biomarker development to reduce variability and advance clinical precision: a narrative review",
        "source": "Frontiers in Digital Health",
        "year": "2025",
        "doi": "10.3389/fdgth.2025.1619183",
        "url": "https://doi.org/10.3389/fdgth.2025.1619183",
        "relevance": "支持用标准化任务、采集协议和验证路径降低语音生物标志物研究差异。",
        "limitation": "综述性质，不能直接证明本平台算法的临床有效性。",
    },
    {
        "category": "验证框架",
        "title": "V3 Framework: Verification, Analytical Validation, Clinical Validation",
        "source": "Digital Medicine Society",
        "year": "2020+",
        "doi": "",
        "url": "https://dimesociety.org/access-resources/v3-framework/",
        "relevance": "用于定义从传感器质量、算法稳定性到临床意义验证的分层路线。",
        "limitation": "属于方法框架，具体性能仍需本平台数据验证。",
    },
    {
        "category": "语音评估",
        "title": "Voice Disorders Practice Portal",
        "source": "American Speech-Language-Hearing Association",
        "year": "持续更新",
        "doi": "",
        "url": "https://www.asha.org/practice-portal/clinical-topics/voice-disorders/",
        "relevance": "支持把声音质量、音高、响度、气息和功能影响纳入嗓音评估。",
        "limitation": "专业评估指南，不等同于移动端自动化筛查批准。",
    },
    {
        "category": "呼吸与气道",
        "title": "Respiratory Diseases Diagnosis Using Audio Analysis and Artificial Intelligence: A Systematic Review",
        "source": "Sensors",
        "year": "2024",
        "doi": "10.3390/s24041173",
        "url": "https://doi.org/10.3390/s24041173",
        "relevance": "总结咳嗽、呼吸音、语音等音频信号在呼吸疾病AI分析中的研究现状。",
        "limitation": "研究异质性较高，平台目前只输出风险参考而非诊断。",
    },
    {
        "category": "神经运动",
        "title": "Acoustic analysis of voice in Parkinson's disease: a systematic review of voice disability and meta-analysis of studies",
        "source": "Revista de Neurologia",
        "year": "2020",
        "doi": "10.33588/rn.7011.2019414",
        "url": "https://doi.org/10.33588/rn.7011.2019414",
        "relevance": "支持帕金森相关声音异常可通过声学特征进行研究和量化。",
        "limitation": "疾病诊断需神经专科评估，语音只能作为辅助线索。",
    },
    {
        "category": "神经运动",
        "title": "Clinical Decision Support Using Speech Signal Analysis: Systematic Scoping Review of Neurological Disorders",
        "source": "Journal of Medical Internet Research",
        "year": "2025",
        "doi": "10.2196/63004",
        "url": "https://doi.org/10.2196/63004",
        "relevance": "覆盖多类神经系统疾病中语音信号分析的临床决策支持研究。",
        "limitation": "范围综述提示机会与差距，不能替代本地临床验证。",
    },
    {
        "category": "心理与压力",
        "title": "Automated assessment of psychiatric disorders using speech: A systematic review",
        "source": "Laryngoscope Investigative Otolaryngology",
        "year": "2020",
        "doi": "10.1002/lio2.354",
        "url": "https://doi.org/10.1002/lio2.354",
        "relevance": "支持语速、停顿、韵律、音高和能量等语音指标与心理状态研究相关。",
        "limitation": "心理健康评估必须结合量表、访谈和专业人员判断。",
    },
    {
        "category": "心肺活力",
        "title": "Voice Assessment and Vocal Biomarkers in Heart Failure: A Systematic Review",
        "source": "Circulation: Heart Failure",
        "year": "2025",
        "doi": "10.1161/CIRCHEARTFAILURE.124.012303",
        "url": "https://doi.org/10.1161/CIRCHEARTFAILURE.124.012303",
        "relevance": "总结心衰场景中声音评估与声学生物标志物研究。",
        "limitation": "胸闷、气促、胸痛等症状应直接就医，不能依赖小程序。",
    },
    {
        "category": "嗓音与喉部",
        "title": "Glottic insufficiency caused by vocal fold atrophy with or without sulcus: systematic review of outcome measurements",
        "source": "European Archives of Oto-Rhino-Laryngology",
        "year": "2024",
        "doi": "10.1007/s00405-024-08751-5",
        "url": "https://doi.org/10.1007/s00405-024-08751-5",
        "relevance": "提示嗓音障碍研究常结合患者报告、听感、声学和喉镜等多种结局指标。",
        "limitation": "持续嘶哑、吞咽困难或咽喉疼痛应线下耳鼻喉评估。",
    },
    {
        "category": "AI报告规范",
        "title": "Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension",
        "source": "Nature Medicine",
        "year": "2020",
        "doi": "10.1038/s41591-020-1034-x",
        "url": "https://doi.org/10.1038/s41591-020-1034-x",
        "relevance": "指导AI医疗干预临床试验报告透明化，适合未来临床研究阶段使用。",
        "limitation": "当前平台尚未按临床试验结论宣传准确率。",
    },
    {
        "category": "AI诊断研究规范",
        "title": "Developing a reporting guideline for artificial intelligence-centred diagnostic test accuracy studies: the STARD-AI protocol",
        "source": "BMJ Open",
        "year": "2021",
        "doi": "10.1136/bmjopen-2020-047709",
        "url": "https://doi.org/10.1136/bmjopen-2020-047709",
        "relevance": "为AI诊断准确性研究提供透明报告方向，适合未来做诊断/筛查声明前参考。",
        "limitation": "本平台当前不宣称诊断准确率。",
    },
    {
        "category": "中国合规",
        "title": "人工智能医疗器械注册审查指导原则",
        "source": "国家药监局医疗器械技术审评中心",
        "year": "2022",
        "doi": "",
        "url": "https://www.cmde.org.cn/",
        "relevance": "若产品未来用于疾病筛查、辅助诊断或治疗决策，应按医疗器械软件/AI医疗器械路径评估。",
        "limitation": "当前小程序需保持健康管理参考定位，避免医疗器械式宣传。",
    },
    {
        "category": "隐私合规",
        "title": "中华人民共和国个人信息保护法",
        "source": "全国人大",
        "year": "2021",
        "doi": "",
        "url": "https://www.npc.gov.cn/",
        "relevance": "语音、面部、健康信息属于高度敏感数据场景，应取得明确同意、最小化采集并提供删除/撤回路径。",
        "limitation": "具体上线还需结合小程序隐私弹窗、隐私政策和数据安全制度执行。",
    },
]


COLLECTION_GUIDE: List[Dict] = [
    {
        "title": "采集前",
        "items": [
            "选择安静室内，关闭电视、音乐、风扇等持续噪声。",
            "手机麦克风距口部约15-25厘米，不遮挡麦克风。",
            "剧烈运动、饮酒、刚哭笑、长时间用嗓、感冒发热后不建议立即采集。",
            "如正在出现胸痛、明显气促、突然言语含糊或肢体无力，应先就医。",
        ],
    },
    {
        "title": "采集中",
        "items": [
            "用自然语速朗读小程序给出的固定文本。",
            "录制接近30秒，少于20秒时趋势稳定性会下降。",
            "保持正常音量，不刻意压低、升高、模仿或表演声音。",
            "中途明显咳嗽、被打断或背景噪声过大时，建议重新录制。",
        ],
    },
    {
        "title": "复测规则",
        "items": [
            "建立个人基线：连续7天在相近时间、相近环境录制。",
            "日常管理：每周2-3次即可，重点观察连续趋势。",
            "同日多次结果不一致时，以环境更安静、朗读更完整的一次作为参考。",
            "连续3次同一维度明显下降，再结合睡眠、压力、运动和症状判断。",
        ],
    },
]


CHECKIN_GUIDE: List[Dict] = [
    {
        "title": "每日声纹卡",
        "desc": "固定早晨起床后或晚间睡前录制一次，记录睡眠时长、主观疲劳和当日压力。",
    },
    {
        "title": "嗓音保护卡",
        "desc": "嘶哑、干涩或气声升高时，减少长时间讲话，补充饮水，连续异常超过两周建议耳鼻喉评估。",
    },
    {
        "title": "呼吸观察卡",
        "desc": "气短、停顿增加或发声占比下降时，记录运动耐量、咳嗽、喘息、胸闷和近期感染情况。",
    },
    {
        "title": "压力睡眠卡",
        "desc": "语速、停顿和韵律同时异常时，记录睡眠、咖啡因、工作压力和情绪变化，优先做恢复管理。",
    },
    {
        "title": "饮食水分卡",
        "desc": "记录饮水、咖啡因、酒精、辛辣油腻和睡前进食。咽喉干涩、反流刺激或嗓音疲劳时，优先补水并减少刺激性饮食。",
    },
    {
        "title": "复测确认卡",
        "desc": "单次高关注不等于疾病。先排除噪声、时长不足、麦克风距离、感冒和用嗓过度，再做复测。",
    },
    {
        "title": "就医提醒卡",
        "desc": "胸痛、呼吸困难、突然说话不清、吞咽困难、咳血、持续高热等情况不要等待小程序结果。",
    },
]


RESULT_GUIDE: List[Dict] = [
    {
        "title": "总体分",
        "items": [
            "85-100：本次声音状态整体平稳，建议继续积累趋势。",
            "70-84：少数维度可观察，优先复测并结合生活状态判断。",
            "60-69：建议关注近期睡眠、压力、呼吸、嗓音或感染因素。",
            "低于60：若连续出现或伴随不适，应咨询专业医生。",
        ],
    },
    {
        "title": "关注等级",
        "items": [
            "低关注：目前仅作为个人趋势记录。",
            "中等关注：建议在相同条件下复测，并查看是否有对应症状。",
            "高关注：建议结合线下评估；如出现急性症状，优先就医。",
        ],
    },
    {
        "title": "平台不做的事",
        "items": [
            "不根据声音给出疾病确诊结论。",
            "不替代医生问诊、体格检查、影像、实验室检查或量表评估。",
            "不向用户宣传未验证准确率、治愈率或疾病筛查结论。",
        ],
    },
]


COMPLIANCE_GUIDE: List[Dict] = [
    {
        "title": "产品定位",
        "desc": "当前定位为健康管理参考和趋势记录，不作为医学诊断、筛查或治疗建议。",
    },
    {
        "title": "数据保护",
        "desc": "语音、面部、视频和健康推断属于敏感场景，应提供清晰授权、隐私政策、删除路径和最小化采集。",
    },
    {
        "title": "证据分级",
        "desc": "公开文献只能说明领域可行性。本平台自身性能需要独立测试集、偏倚评估、真实世界验证和专家审阅。",
    },
    {
        "title": "上线审核",
        "desc": "小程序页面、分享文案、广告和付费页都应避免疾病诊断承诺，并保留免责声明和就医提醒。",
    },
    {
        "title": "未来升级",
        "desc": "如果未来进入筛查/辅助诊断，需要按医疗器械软件、AI医疗器械、临床试验和质量管理体系推进。",
    },
]


def get_evidence_base() -> Dict:
    return {
        "ok": True,
        "updatedAt": date.today().isoformat(),
        "theories": THEORY_FOUNDATIONS,
        "references": EVIDENCE_REFERENCES,
        "collectionGuide": COLLECTION_GUIDE,
        "checkinGuide": CHECKIN_GUIDE,
        "resultGuide": RESULT_GUIDE,
        "complianceGuide": COMPLIANCE_GUIDE,
        "referenceTotal": len(EVIDENCE_REFERENCES),
    }
