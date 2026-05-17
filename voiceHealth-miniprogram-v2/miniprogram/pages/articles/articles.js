// pages/articles/articles.js
// VoiceHealth 健康学院：阶段化课程 + 练习 + 神经TTS音频试听 + 工具入口

const EMPTY_AUDIO_STATE = {
  lessonId: '',
  playing: false,
  loading: false,
  current: 0,
  duration: 0,
  percent: 0,
  currentText: '00:00',
  durationText: '00:00',
  error: ''
}

function formatAudioTime(seconds) {
  const safe = Number.isFinite(Number(seconds)) ? Math.max(0, Math.floor(Number(seconds))) : 0
  const minutes = Math.floor(safe / 60)
  const rest = safe % 60
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
}

Page({
  data: {
    activePhase: 0,
    completedLessonIds: [],
    phases: [
      {
        id: 'foundation',
        name: 'Phase 1',
        title: '声音健康基础',
        range: '第1-4课',
        focus: '理解声音能看什么、不能看什么',
        lessons: [
          {
            id: 'vh-01',
            no: 1,
            title: '声音里的健康线索',
            subtitle: '从音高、能量、停顿、音质理解健康参考',
            tag: '基础',
            duration: '12分钟',
            objective: '理解语音生物标志物只能用于健康管理参考，不能替代诊断。',
            practice: '完成一次30秒标准朗读，并记录当日睡眠和压力。',
            content: 'VoiceHealth会分析音高、停顿、语速、能量、音质和频谱等可解释特征。请把结果当作健康管理参考，重点观察连续趋势。'
          },
          {
            id: 'vh-02',
            no: 2,
            title: '采集质量决定可信度',
            subtitle: '环境、距离、时长和朗读一致性',
            tag: '采集',
            duration: '10分钟',
            objective: '掌握可复测的录音流程。',
            practice: '在同一房间、同一距离下录制两次，比较活体和朗读匹配分。',
            content: '建议在安静室内录制，手机麦克风距口部约15-25厘米，使用自然语速朗读固定文本，录制接近30秒。'
          },
          {
            id: 'vh-03',
            no: 3,
            title: '建立个人声音基线',
            subtitle: '7天连续记录比单次分数更重要',
            tag: '核心',
            duration: '14分钟',
            objective: '学会用个人基线解释波动。',
            practice: '连续7天在相近时间完成复测，并填写打卡。',
            content: '单次分数容易受环境、设备、睡眠、压力、饮食和运动影响。连续趋势比单次结果更可靠。'
          },
          {
            id: 'vh-04',
            no: 4,
            title: '风险提示的正确读法',
            subtitle: '分数、维度、风险等级和就医边界',
            tag: '边界',
            duration: '13分钟',
            objective: '区分健康参考、复测观察和线下就医场景。',
            practice: '打开最近报告，找出一个高关注信号和一个复测动作。',
            content: '若出现胸痛、明显气促、突然言语异常、持续嘶哑超过两周等情况，不应继续依赖评分，应优先线下评估。'
          }
        ]
      },
      {
        id: 'lifestyle',
        name: 'Phase 2',
        title: '生活方式共振',
        range: '第5-8课',
        focus: '把睡眠、压力、饮食、运动和声音趋势连起来',
        lessons: [
          {
            id: 'vh-05',
            no: 5,
            title: '睡眠与声音恢复',
            subtitle: '睡眠不足如何影响能量、停顿和韵律',
            tag: '睡眠',
            duration: '15分钟',
            objective: '理解睡眠记录如何解释声音状态。',
            practice: '连续3天记录睡眠小时，并观察声音分数变化。',
            content: '睡眠不足可能让声音能量下降、停顿增多或韵律变平。成年人通常需要每晚至少7小时睡眠。'
          },
          {
            id: 'vh-06',
            no: 6,
            title: '压力负荷与语音节律',
            subtitle: '压力、焦虑、疲劳和语速波动',
            tag: '压力',
            duration: '12分钟',
            objective: '学会把主观压力和语音趋势放在一起看。',
            practice: '在压力较高的一天完成打卡，并记录恢复动作。',
            content: '疲劳、焦虑和压力可能影响语速、停顿、能量和韵律。记录压力等级有助于解释短期波动。'
          },
          {
            id: 'vh-07',
            no: 7,
            title: '饮水、饮食与嗓音',
            subtitle: '咽干、反流、辛辣油腻和睡前进食',
            tag: '嗓音',
            duration: '13分钟',
            objective: '识别影响嗓音稳定性的饮食触发因素。',
            practice: '使用“嗓音疲劳”模板完成一次打卡。',
            content: '咽喉干涩、气声升高或嘶哑时，优先补水、减少烟酒和刺激性饮食，避免睡前进食。'
          },
          {
            id: 'vh-08',
            no: 8,
            title: '运动日如何复测',
            subtitle: '运动后气息波动与恢复窗口',
            tag: '运动',
            duration: '10分钟',
            objective: '避免把运动后短期气息波动误读为健康下降。',
            practice: '运动后至少间隔30分钟再录音，并记录运动强度。',
            content: '运动后短期气息、心率和疲劳可能改变语音特征。建议固定复测条件，长期观察趋势。'
          }
        ]
      },
      {
        id: 'action',
        name: 'Phase 3',
        title: '改善闭环实战',
        range: '第9-12课',
        focus: '从报告到行动计划，再到复测复盘',
        lessons: [
          {
            id: 'vh-09',
            no: 9,
            title: '从报告生成行动计划',
            subtitle: '分数低时先做什么，分数稳定时如何保持',
            tag: '实战',
            duration: '14分钟',
            objective: '把风险信号转化为一周行动。',
            practice: '在报告页点击“开始改善”，生成本轮闭环。',
            content: '行动计划会结合评分、风险信号、生活方式记录和复测建议，输出目标、动作、复测节奏和就医边界。'
          },
          {
            id: 'vh-10',
            no: 10,
            title: '循证方案怎么选',
            subtitle: '运动、睡眠、饮食、饮水、压力和嗓音保护',
            tag: '方案',
            duration: '16分钟',
            objective: '理解方案库如何按信号匹配。',
            practice: '打开循证方案库，收藏或记录一个本周要执行的方案。',
            content: '方案库基于公开指南组织，覆盖有氧活动、力量训练、睡眠、健康饮食、饮水、压力恢复、减少饮酒、戒烟转介和嗓音保护。'
          },
          {
            id: 'vh-11',
            no: 11,
            title: '复测与复盘',
            subtitle: '如何判断改善是否真的发生',
            tag: '复盘',
            duration: '12分钟',
            objective: '使用趋势而不是单点分数做判断。',
            practice: '保存一次今日执行，再完成一次复测。',
            content: '评分低于70分时，建议在相同环境下连续复测3到7天。恢复稳定后，每周2到3次即可。'
          },
          {
            id: 'vh-12',
            no: 12,
            title: '数据授权与API对接',
            subtitle: '健康数据如何成为未来模块接口',
            tag: '进阶',
            duration: '15分钟',
            objective: '理解健康数据包、scope和外部模块对接边界。',
            practice: '查看个人中心里的数据模块，理解哪些数据可导出。',
            content: 'VoiceHealth 提供结构化健康数据摘要、时间线、生活方式记录、行动计划、循证方案和改善闭环数据，便于未来授权对接。'
          }
        ]
      }
    ],
    tools: [
      { title: '健康打卡', desc: '用模板快速记录今天状态', icon: '记录', url: '/pages/checkin/checkin' },
      { title: '循证方案', desc: '查看可执行改善方案', icon: '方案', url: '/pages/plans/plans' },
      { title: '改善闭环', desc: '保存执行并复测回顾', icon: '闭环', url: '/pages/improvement/improvement' },
      { title: '趋势分析', desc: '观察长期声音变化', icon: '趋势', url: '/pages/trends/trends' }
    ],
    activePhaseData: null,
    activeLessons: [],
    audioState: { ...EMPTY_AUDIO_STATE }
  },

  onLoad() {
    this.initAudioContext()
    const completedLessonIds = wx.getStorageSync('completedLessons') || []
    this.setData({ completedLessonIds }, () => this.applyPhase())
  },

  onShow() {
    const completedLessonIds = wx.getStorageSync('completedLessons') || []
    this.setData({ completedLessonIds }, () => this.applyPhase())
  },

  switchPhase(e) {
    this.setData({ activePhase: Number(e.currentTarget.dataset.index) }, () => this.applyPhase())
  },

  applyPhase() {
    const phase = this.data.phases[this.data.activePhase]
    const completed = new Set(this.data.completedLessonIds)
    const activeLessons = phase.lessons.map(item => ({
      ...item,
      completed: completed.has(item.id),
      audio: `/audio/courses/${item.id}.mp3`,
      audioProfile: 'YunyangNeural · 48kbps'
    }))
    this.setData({ activePhaseData: phase, activeLessons })

    if (this.data.audioState.lessonId && !activeLessons.some(item => item.id === this.data.audioState.lessonId)) {
      this.stopLessonAudio()
    }
  },

  initAudioContext() {
    if (this.audioContext || !wx.createInnerAudioContext) return

    const audio = wx.createInnerAudioContext()
    audio.obeyMuteSwitch = false
    this.audioContext = audio

    audio.onCanplay(() => {
      setTimeout(() => this.updateAudioProgress(), 250)
    })
    audio.onPlay(() => {
      this.setData({
        'audioState.playing': true,
        'audioState.loading': false,
        'audioState.error': ''
      })
    })
    audio.onPause(() => {
      this.setData({ 'audioState.playing': false, 'audioState.loading': false })
      this.updateAudioProgress()
    })
    audio.onStop(() => {
      this.setData({ 'audioState.playing': false, 'audioState.loading': false })
    })
    audio.onEnded(() => {
      this.updateAudioProgress()
      this.setData({
        'audioState.playing': false,
        'audioState.loading': false,
        'audioState.percent': 100
      })
    })
    audio.onWaiting(() => {
      this.setData({ 'audioState.loading': true })
    })
    audio.onTimeUpdate(() => {
      this.updateAudioProgress()
    })
    audio.onError(err => {
      this.setData({
        'audioState.playing': false,
        'audioState.loading': false,
        'audioState.error': '音频暂时无法播放，请稍后重试'
      })
      wx.showToast({ title: '音频加载失败', icon: 'none' })
      console.warn('course audio error', err)
    })
  },

  updateAudioProgress() {
    if (!this.audioContext || !this.data.audioState.lessonId) return
    const current = Number(this.audioContext.currentTime) || 0
    const duration = Number(this.audioContext.duration) || this.data.audioState.duration || 0
    const percent = duration ? Math.min(100, Math.round((current / duration) * 100)) : 0

    this.setData({
      'audioState.current': current,
      'audioState.duration': duration,
      'audioState.percent': percent,
      'audioState.currentText': formatAudioTime(current),
      'audioState.durationText': formatAudioTime(duration)
    })
  },

  toggleLessonAudio(e) {
    const id = e.currentTarget.dataset.id
    const lesson = this.data.activeLessons.find(item => item.id === id)
    if (!lesson) return
    if (!this.audioContext) this.initAudioContext()
    if (!this.audioContext) {
      wx.showToast({ title: '当前环境不支持音频播放', icon: 'none' })
      return
    }

    const state = this.data.audioState
    if (state.lessonId === id) {
      if (state.playing) {
        this.audioContext.pause()
      } else {
        this.setData({ 'audioState.loading': true, 'audioState.error': '' })
        this.audioContext.play()
      }
      return
    }

    this.audioContext.stop()
    this.setData({
      audioState: {
        ...EMPTY_AUDIO_STATE,
        lessonId: id,
        loading: true,
        durationText: '--:--'
      }
    })
    this.audioContext.src = lesson.audio
    this.audioContext.title = lesson.title
    this.audioContext.play()
  },

  onAudioSeek(e) {
    const state = this.data.audioState
    if (!this.audioContext || !state.lessonId || !state.duration) return
    const percent = Number(e.detail.value) || 0
    const target = Math.max(0, Math.min(state.duration, (state.duration * percent) / 100))
    this.audioContext.seek(target)
    this.setData({
      'audioState.current': target,
      'audioState.percent': percent,
      'audioState.currentText': formatAudioTime(target)
    })
  },

  stopLessonAudio() {
    if (this.audioContext) this.audioContext.stop()
    this.setData({ audioState: { ...EMPTY_AUDIO_STATE } })
  },

  noop() {
    return false
  },

  openLesson(e) {
    const id = e.currentTarget.dataset.id
    const lesson = this.data.activeLessons.find(item => item.id === id)
    if (!lesson) return

    wx.showModal({
      title: `第${lesson.no}课：${lesson.title}`,
      content: `${lesson.objective}\n\n课程要点：${lesson.content}\n\n行动练习：${lesson.practice}`,
      confirmText: lesson.completed ? '已完成' : '标记完成',
      cancelText: '关闭',
      success: res => {
        if (!res.confirm || lesson.completed) return
        const completedLessonIds = [...this.data.completedLessonIds, lesson.id]
        wx.setStorageSync('completedLessons', completedLessonIds)
        this.setData({ completedLessonIds }, () => this.applyPhase())
        wx.showToast({ title: '已完成', icon: 'success' })
      }
    })
  },

  goTool(e) {
    const url = e.currentTarget.dataset.url
    if (url) wx.navigateTo({ url })
  },

  onShareAppMessage() {
    return { title: 'VoiceHealth 健康学院', path: '/pages/articles/articles' }
  },

  onUnload() {
    if (this.audioContext) {
      this.audioContext.destroy()
      this.audioContext = null
    }
  }
})
