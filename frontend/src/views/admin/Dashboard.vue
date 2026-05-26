<template>
  <div class="dashboard-page">
    <el-card class="filter-card">
      <div class="filter-row">
        <span class="filter-label">统计周期：</span>
        <el-radio-group v-model="period" size="default" @change="fetchAll">
          <el-radio-button value="7d">近 7 天</el-radio-button>
          <el-radio-button value="30d">近 30 天</el-radio-button>
          <el-radio-button value="90d">近 90 天</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Refresh" @click="fetchAll" style="margin-left: 12px;">
          刷新
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="20" class="summary-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon total">
            <el-icon><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_bookings }}</div>
            <div class="stat-label">总预订次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon used">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatMinutes(summary.total_used_minutes) }}</div>
            <div class="stat-label">实际使用时长</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon util">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.average_utilization_rate }}%</div>
            <div class="stat-label">平均利用率</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon rooms">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_rooms }}</div>
            <div class="stat-label">会议室总数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">会议室利用率排行</span>
              <span class="card-sub">按实际使用时长占比排序</span>
            </div>
          </template>
          <div ref="utilizationBarRef" class="chart-container" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">预订 vs 实际使用</span>
              <span class="card-sub">各会议室预订时长与实际使用时长（小时）</span>
            </div>
          </template>
          <div ref="compareBarRef" class="chart-container" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">各时段预订频次分布</span>
              <span class="card-sub">24 小时内预订开始时间分布</span>
            </div>
          </template>
          <div ref="hourlyLineRef" class="chart-container" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">每日预订趋势</span>
              <span class="card-sub">周期内每日预订次数变化</span>
            </div>
          </template>
          <div ref="dailyLineRef" class="chart-container" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">会议室利用率明细表</span>
          <span class="card-sub">红色为低利用率（<30%），绿色为高利用率（>70%）</span>
        </div>
      </template>
      <el-table :data="roomStats" stripe style="width: 100%">
        <el-table-column prop="room_name" label="会议室名称" min-width="140" />
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column prop="total_bookings" label="预订次数" width="100" />
        <el-table-column label="预订时长" width="140">
          <template #default="{ row }">
            {{ formatMinutes(row.total_booked_minutes) }}
          </template>
        </el-table-column>
        <el-table-column label="实际使用" width="140">
          <template #default="{ row }">
            {{ formatMinutes(row.actual_used_minutes) }}
          </template>
        </el-table-column>
        <el-table-column label="签到率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.check_in_rate"
              :stroke-width="10"
              :color="progressColor(row.check_in_rate)"
            />
          </template>
        </el-table-column>
        <el-table-column label="取消率" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.cancel_rate > 30 ? 'danger' : row.cancel_rate > 10 ? 'warning' : 'success'"
              size="small"
            >
              {{ row.cancel_rate }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="利用率" min-width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="row.utilization_rate"
              :stroke-width="12"
              :color="utilColor(row.utilization_rate)"
            />
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="roomStats.length === 0" description="暂无数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import {
  Refresh, Calendar, Clock, DataAnalysis, OfficeBuilding
} from '@element-plus/icons-vue'
import { statsApi } from '@/utils/api'

const period = ref('30d')
const roomStats = ref([])
const hourlyStats = ref([])
const dailyStats = ref([])
const summary = reactive({
  total_bookings: 0,
  total_used_minutes: 0,
  average_utilization_rate: 0,
  total_rooms: 0
})

const utilizationBarRef = ref(null)
const compareBarRef = ref(null)
const hourlyLineRef = ref(null)
const dailyLineRef = ref(null)

let utilizationBarChart = null
let compareBarChart = null
let hourlyLineChart = null
let dailyLineChart = null

const formatMinutes = (minutes) => {
  if (!minutes) return '0 小时'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m} 分钟`
  if (m === 0) return `${h} 小时`
  return `${h}小时${m}分钟`
}

const utilColor = (rate) => {
  if (rate >= 70) return '#67C23A'
  if (rate >= 30) return '#409EFF'
  return '#F56C6C'
}

const progressColor = (rate) => {
  if (rate >= 70) return '#67C23A'
  if (rate >= 40) return '#E6A23C'
  return '#F56C6C'
}

const fetchUtilization = async () => {
  try {
    const data = await statsApi.getUtilization({ period: period.value })
    roomStats.value = data.rooms || []
    Object.assign(summary, data.summary || {})
    await nextTick()
    renderUtilizationBar()
    renderCompareBar()
  } catch (error) {
    console.error(error)
  }
}

const fetchHourly = async () => {
  try {
    const data = await statsApi.getHourly({ period: period.value })
    hourlyStats.value = data.hourly || []
    await nextTick()
    renderHourlyLine()
  } catch (error) {
    console.error(error)
  }
}

const fetchDaily = async () => {
  try {
    const data = await statsApi.getDaily({ period: period.value })
    dailyStats.value = data.daily || []
    await nextTick()
    renderDailyLine()
  } catch (error) {
    console.error(error)
  }
}

const fetchAll = () => {
  fetchUtilization()
  fetchHourly()
  fetchDaily()
}

const renderUtilizationBar = () => {
  if (!utilizationBarRef.value) return
  if (!utilizationBarChart) {
    utilizationBarChart = echarts.init(utilizationBarRef.value)
  }
  const rooms = [...roomStats.value].sort((a, b) => a.utilization_rate - b.utilization_rate)
  utilizationBarChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 120, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'value',
      name: '利用率 (%)',
      axisLabel: { formatter: '{value}%' }
    },
    yAxis: {
      type: 'category',
      data: rooms.map(r => r.room_name)
    },
    series: [{
      type: 'bar',
      data: rooms.map(r => ({
        value: r.utilization_rate,
        itemStyle: { color: utilColor(r.utilization_rate) }
      })),
      label: {
        show: true,
        position: 'right',
        formatter: '{c}%'
      },
      barMaxWidth: 20
    }]
  })
}

const renderCompareBar = () => {
  if (!compareBarRef.value) return
  if (!compareBarChart) {
    compareBarChart = echarts.init(compareBarRef.value)
  }
  const rooms = roomStats.value
  compareBarChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['预订时长', '实际使用时长'] },
    grid: { left: 50, right: 20, top: 50, bottom: 40 },
    xAxis: { type: 'category', data: rooms.map(r => r.room_name) },
    yAxis: { type: 'value', name: '小时' },
    series: [
      {
        name: '预订时长',
        type: 'bar',
        data: rooms.map(r => +(r.total_booked_minutes / 60).toFixed(1)),
        itemStyle: { color: '#409EFF' },
        barMaxWidth: 25
      },
      {
        name: '实际使用时长',
        type: 'bar',
        data: rooms.map(r => +(r.actual_used_minutes / 60).toFixed(1)),
        itemStyle: { color: '#67C23A' },
        barMaxWidth: 25
      }
    ]
  })
}

const renderHourlyLine = () => {
  if (!hourlyLineRef.value) return
  if (!hourlyLineChart) {
    hourlyLineChart = echarts.init(hourlyLineRef.value)
  }
  hourlyLineChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: hourlyStats.value.map(h => `${h.hour}:00`),
      boundaryGap: false
    },
    yAxis: { type: 'value', name: '预订次数' },
    series: [{
      type: 'line',
      data: hourlyStats.value.map(h => h.count),
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.4)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      lineStyle: { color: '#409EFF', width: 2 },
      itemStyle: { color: '#409EFF' }
    }]
  })
}

const renderDailyLine = () => {
  if (!dailyLineRef.value) return
  if (!dailyLineChart) {
    dailyLineChart = echarts.init(dailyLineRef.value)
  }
  dailyLineChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dailyStats.value.map(d => d.date),
      boundaryGap: false,
      axisLabel: { rotate: 30 }
    },
    yAxis: { type: 'value', name: '预订次数' },
    series: [{
      type: 'line',
      data: dailyStats.value.map(d => d.count),
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(103, 194, 58, 0.4)' },
          { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
        ])
      },
      lineStyle: { color: '#67C23A', width: 2 },
      itemStyle: { color: '#67C23A' }
    }]
  })
}

const handleResize = () => {
  utilizationBarChart && utilizationBarChart.resize()
  compareBarChart && compareBarChart.resize()
  hourlyLineChart && hourlyLineChart.resize()
  dailyLineChart && dailyLineChart.resize()
}

onMounted(() => {
  fetchAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  utilizationBarChart && utilizationBarChart.dispose()
  compareBarChart && compareBarChart.dispose()
  hourlyLineChart && hourlyLineChart.dispose()
  dailyLineChart && dailyLineChart.dispose()
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  margin-bottom: 4px;
}

.filter-row {
  display: flex;
  align-items: center;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  margin-right: 12px;
}

.summary-row {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}

.stat-icon.total { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-icon.used { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-icon.util { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-icon.rooms { background: linear-gradient(135deg, #43e97b, #38f9d7); color: #303133; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.card-sub {
  font-size: 12px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 360px;
}
</style>
