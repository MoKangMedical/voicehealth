// pages/checkin/checkin.js
// 每日生活方式打卡：饮食、运动、睡眠、压力与症状记录

const app = getApp()

function formatDateForApi(date) {
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

function dateKeyFromApi(dateStr) {
  const parts = dateStr.split('-').map(Number)
  return new Date(parts[0], parts[1] - 1, parts[2]).toDateString()
}

function createEmptyForm(dateStr) {
  return {
    checkinDate: dateStr,
    breakfast: '',
    lunch: '',
    dinner: '',
    snack: '',
    dietTags: [],
    waterMl: 1500,
    caffeineCups: 0,
    alcohol: false,
    spicyOily: false,
    lateMeal: false,
    exerciseType: '休息',
    exerciseMinutes: 0,
    exerciseIntensity: '未记录',
    steps: 0,
    sleepHours: 7,
    stressLevel: 2,
    mood: '平稳',
    symptoms: [],
    notes: ''
  }
}

Page({
  data: {
    loading: true,
    saving: false,
    isCheckedIn: false,
    selectedDate: '',
    streak: 0,
    totalDays: 0,
    checkinDays: [],
    summary: null,
    form: createEmptyForm(formatDateForApi(new Date())),
    weekDays: ['一', '二', '三', '四', '五', '六', '日'],
    currentWeek: [],
    exerciseTypes: ['休息', '步行', '跑步', '骑行', '力量训练', '瑜伽/拉伸', '球类', '游泳', '其他'],
    exerciseTypeIndex: 0,
    intensityOptions: ['未记录', '低强度', '中等强度', '高强度'],
    intensityIndex: 0,
    moodOptions: ['平稳', '轻松', '疲惫', '焦虑', '低落', '兴奋'],
    moodIndex: 0,
    quickPresets: [
      {
        key: 'balanced',
        title: '正常日',
        desc: '清淡饮食、步行、睡眠达标',
        values: {
          dietTags: ['清淡', '蔬果充足'],
          waterMl: 1800,
          exerciseType: '步行',
          exerciseMinutes: 30,
          exerciseIntensity: '中等强度',
          sleepHours: 7.5,
          stressLevel: 2,
          mood: '平稳',
          symptoms: [],
          alcohol: false,
          spicyOily: false,
          lateMeal: false
        }
      },
      {
        key: 'voice',
        title: '嗓音疲劳',
        desc: '补水、少刺激、记录咽喉症状',
        values: {
          dietTags: ['清淡'],
          waterMl: 2000,
          exerciseType: '休息',
          exerciseMinutes: 0,
          exerciseIntensity: '未记录',
          sleepHours: 7,
          stressLevel: 3,
          mood: '疲惫',
          symptoms: ['咽干', '嗓音嘶哑'],
          alcohol: false,
          spicyOily: false,
          lateMeal: false
        }
      },
      {
        key: 'stress',
        title: '熬夜压力',
        desc: '睡眠不足、压力偏高、需要恢复',
        values: {
          dietTags: ['夜宵'],
          waterMl: 1200,
          exerciseType: '休息',
          exerciseMinutes: 0,
          exerciseIntensity: '未记录',
          sleepHours: 5.5,
          stressLevel: 4,
          mood: '疲惫',
          symptoms: ['疲劳', '困倦', '压力大'],
          lateMeal: true
        }
      },
      {
        key: 'sport',
        title: '运动日',
        desc: '有氧或力量训练后快速记录',
        values: {
          dietTags: ['高蛋白', '蔬果充足'],
          waterMl: 2200,
          exerciseType: '跑步',
          exerciseMinutes: 40,
          exerciseIntensity: '中等强度',
          steps: 8000,
          sleepHours: 7,
          stressLevel: 2,
          mood: '轻松',
          symptoms: []
        }
      }
    ],
    rewards: [
      { days: 3, reward: '复测习惯', unlocked: false },
      { days: 7, reward: '个人基线', unlocked: false },
      { days: 14, reward: '趋势观察', unlocked: false },
      { days: 30, reward: '月度回顾', unlocked: false }
    ],
    dietTagOptions: [
      { label: '清淡', selected: false },
      { label: '高蛋白', selected: false },
      { label: '蔬果充足', selected: false },
      { label: '高油盐', selected: false },
      { label: '辛辣', selected: false },
      { label: '甜食', selected: false },
      { label: '夜宵', selected: false },
      { label: '饮酒', selected: false }
    ],
    symptomOptions: [
      { label: '咽干', selected: false },
      { label: '咳嗽', selected: false },
      { label: '气短', selected: false },
      { label: '疲劳', selected: false },
      { label: '困倦', selected: false },
      { label: '压力大', selected: false },
      { label: '嗓音嘶哑', selected: false }
    ]
  },

  onLoad() {
    const selectedDate = formatDateForApi(new Date())
    this.setData({
      selectedDate,
      form: createEmptyForm(selectedDate)
    })
    this.loadCheckinData()
    this.loadRemoteCheckin()
  },

  onPullDownRefresh() {
    this.loadRemoteCheckin().finally(() => wx.stopPullDownRefresh())
  },

  loadCheckinData() {
    const data = wx.getStorageSync('checkinData') || { streak: 0, totalDays: 0, days: [] }
    const todayKey = dateKeyFromApi(this.data.selectedDate || formatDateForApi(new Date()))
    const isCheckedIn = data.days.includes(todayKey)
    const rewards = this.data.rewards.map(item => ({
      ...item,
      unlocked: data.totalDays >= item.days
    }))

    this.setData({
      isCheckedIn,
      streak: data.streak,
      totalDays: data.totalDays,
      checkinDays: data.days,
      rewards
    })
    this.generateCurrentWeek()
  },

  async loadRemoteCheckin() {
    this.setData({ loading: true })
    try {
      const date = this.data.selectedDate
      const [todayRes, summaryRes] = await Promise.all([
        app.request({ url: `/api/v1/lifestyle/checkin?date=${date}` }),
        app.request({ url: '/api/v1/lifestyle/summary?days=30' })
      ])

      const checkin = todayRes.checkin
      if (checkin) {
        const form = this.normalizeCheckin(checkin)
        this.setData({ form })
        this.syncSelectorState(form)
        this.markLocalCheckin(false)
      }

      this.setData({
        summary: summaryRes.summary || null,
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
      wx.showToast({ title: '打卡数据加载失败', icon: 'none' })
    }
  },

  normalizeCheckin(checkin) {
    const form = createEmptyForm(checkin.checkinDate || this.data.selectedDate)
    return {
      ...form,
      ...checkin,
      dietTags: checkin.dietTags || [],
      symptoms: checkin.symptoms || [],
      waterMl: checkin.waterMl || 0,
      exerciseMinutes: checkin.exerciseMinutes || 0,
      steps: checkin.steps || 0,
      sleepHours: checkin.sleepHours || 0,
      stressLevel: checkin.stressLevel || 0
    }
  },

  syncSelectorState(form) {
    const dietTags = form.dietTags || []
    const symptoms = form.symptoms || []
    const exerciseTypeIndex = Math.max(0, this.data.exerciseTypes.indexOf(form.exerciseType || '休息'))
    const intensityIndex = Math.max(0, this.data.intensityOptions.indexOf(form.exerciseIntensity || '未记录'))
    const moodIndex = Math.max(0, this.data.moodOptions.indexOf(form.mood || '平稳'))

    this.setData({
      exerciseTypeIndex,
      intensityIndex,
      moodIndex,
      dietTagOptions: this.data.dietTagOptions.map(item => ({
        ...item,
        selected: dietTags.includes(item.label)
      })),
      symptomOptions: this.data.symptomOptions.map(item => ({
        ...item,
        selected: symptoms.includes(item.label)
      }))
    })
  },

  generateCurrentWeek() {
    const now = new Date()
    const dayOfWeek = now.getDay() || 7
    const monday = new Date(now)
    monday.setDate(now.getDate() - dayOfWeek + 1)

    const week = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      week.push({
        date: d.getDate(),
        isToday: d.toDateString() === now.toDateString(),
        isChecked: this.data.checkinDays.includes(d.toDateString())
      })
    }
    this.setData({ currentWeek: week })
  },

  onFieldInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onSwitchChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onExerciseTypeChange(e) {
    const index = Number(e.detail.value)
    this.setData({
      exerciseTypeIndex: index,
      'form.exerciseType': this.data.exerciseTypes[index]
    })
  },

  onIntensityChange(e) {
    const index = Number(e.detail.value)
    this.setData({
      intensityIndex: index,
      'form.exerciseIntensity': this.data.intensityOptions[index]
    })
  },

  onMoodChange(e) {
    const index = Number(e.detail.value)
    this.setData({
      moodIndex: index,
      'form.mood': this.data.moodOptions[index]
    })
  },

  toggleDietTag(e) {
    const index = Number(e.currentTarget.dataset.index)
    const options = this.data.dietTagOptions.map((item, i) => (
      i === index ? { ...item, selected: !item.selected } : item
    ))
    this.setData({
      dietTagOptions: options,
      'form.dietTags': options.filter(item => item.selected).map(item => item.label)
    })
  },

  toggleSymptom(e) {
    const index = Number(e.currentTarget.dataset.index)
    const options = this.data.symptomOptions.map((item, i) => (
      i === index ? { ...item, selected: !item.selected } : item
    ))
    this.setData({
      symptomOptions: options,
      'form.symptoms': options.filter(item => item.selected).map(item => item.label)
    })
  },

  applyQuickPreset(e) {
    const key = e.currentTarget.dataset.key
    const preset = this.data.quickPresets.find(item => item.key === key)
    if (!preset) return

    const form = {
      ...this.data.form,
      ...preset.values,
      checkinDate: this.data.selectedDate
    }
    this.setData({ form })
    this.syncSelectorState(form)
    wx.showToast({ title: '已填入模板', icon: 'success' })
  },

  async submitCheckin() {
    if (this.data.saving) return

    const payload = {
      ...this.data.form,
      checkinDate: this.data.selectedDate,
      waterMl: Number(this.data.form.waterMl || 0),
      caffeineCups: Number(this.data.form.caffeineCups || 0),
      exerciseMinutes: Number(this.data.form.exerciseMinutes || 0),
      steps: Number(this.data.form.steps || 0),
      sleepHours: Number(this.data.form.sleepHours || 0),
      stressLevel: Number(this.data.form.stressLevel || 0)
    }

    this.setData({ saving: true })
    try {
      const res = await app.request({
        url: '/api/v1/lifestyle/checkin',
        method: 'POST',
        data: payload
      })
      const form = this.normalizeCheckin(res.checkin || payload)
      this.setData({
        form,
        summary: res.summary || this.data.summary,
        saving: false
      })
      this.syncSelectorState(form)
      this.markLocalCheckin(true)
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (err) {
      this.setData({ saving: false })
      wx.showToast({ title: err.message || '保存失败', icon: 'none' })
    }
  },

  markLocalCheckin(showChangedToast) {
    const todayKey = dateKeyFromApi(this.data.selectedDate)
    const yesterday = new Date(Date.now() - 86400000).toDateString()
    const data = wx.getStorageSync('checkinData') || { streak: 0, totalDays: 0, days: [] }

    if (!data.days.includes(todayKey)) {
      data.streak = data.days.includes(yesterday) ? data.streak + 1 : 1
      data.totalDays += 1
      data.days.push(todayKey)
      wx.setStorageSync('checkinData', data)
      if (showChangedToast) {
        console.log(`连续打卡${data.streak}天`)
      }
    }

    this.loadCheckinData()
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
