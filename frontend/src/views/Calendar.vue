<template>
  <div class="calendar-page">
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="room-filter">
          <span class="filter-label">选择会议室：</span>
          <el-select v-model="selectedRoomId" placeholder="全部会议室" style="width: 200px" @change="fetchBookings">
            <el-option label="全部会议室" :value="null" />
            <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id" />
          </el-select>
        </div>
        <div class="date-nav">
          <el-button-group>
            <el-button @click="changeDate(-1)">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button @click="goToToday">今天</el-button>
            <el-button @click="changeDate(1)">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
          <span class="current-date">{{ currentDateStr }}</span>
        </div>
        <el-button type="primary" @click="openBookingDialog">
          <el-icon><Plus /></el-icon>
          新建预约
        </el-button>
      </div>
    </el-card>

    <el-card class="calendar-card">
      <div v-loading="loading" class="time-grid">
        <div class="time-header">
          <div class="time-label-col"></div>
          <div v-for="room in filteredRooms" :key="room.id" class="room-header">
            <div class="room-name">{{ room.name }}</div>
            <div class="room-info">
              <el-tag size="small" type="info">容纳 {{ room.capacity }} 人</el-tag>
            </div>
          </div>
        </div>
        <div class="time-body">
          <div class="time-slots">
            <div v-for="slot in timeSlots" :key="slot" class="time-slot-label">
              {{ slot }}
            </div>
          </div>
          <div class="booking-areas">
            <div v-for="room in filteredRooms" :key="room.id" class="room-column" @click="(e) => handleSlotClick(room, e)">
              <div v-for="slot in timeSlots" :key="slot" class="slot-cell" :data-time="slot">
              </div>
              <div
                v-for="booking in getRoomBookings(room.id)"
                :key="booking.id"
                class="booking-block"
                :class="{ 'is-cancelled': booking.is_cancelled, 'is-mine': booking.user_id === userStore.user?.id }"
                :style="getBookingStyle(booking)"
                @click.stop="showBookingDetail(booking)"
              >
                <div class="booking-title">{{ booking.title }}</div>
                <div class="booking-time">{{ formatTime(booking.start_time) }} - {{ formatTime(booking.end_time) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="bookingDialogVisible" :title="isEditing ? '编辑预约' : '新建预约'" width="500px">
      <el-form :model="bookingForm" :rules="bookingRules" ref="bookingFormRef" label-width="100px">
        <el-form-item label="会议室" prop="room_id">
          <el-select v-model="bookingForm.room_id" placeholder="请选择会议室" style="width: 100%">
            <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="会议主题" prop="title">
          <el-input v-model="bookingForm.title" placeholder="请输入会议主题" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="bookingForm.start_time"
            type="datetime"
            :disabled-date="disabledDate"
            :disabled-hours="disabledHours"
            :disabled-minutes="disabledMinutes"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="bookingForm.end_time"
            type="datetime"
            :disabled-date="disabledDate"
            :disabled-hours="disabledHours"
            :disabled-minutes="disabledMinutes"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="参会人数" prop="attendees">
          <el-input-number v-model="bookingForm.attendees" :min="1" :max="selectedRoom?.capacity || 100" />
          <span v-if="selectedRoom" class="capacity-hint">（最多 {{ selectedRoom.capacity }} 人）</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="bookingForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bookingDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBooking">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="预约详情" width="450px">
      <div v-if="currentBooking" class="booking-detail">
        <div class="detail-item">
          <span class="label">会议主题：</span>
          <span class="value">{{ currentBooking.title }}</span>
        </div>
        <div class="detail-item">
          <span class="label">会议室：</span>
          <span class="value">{{ getRoomName(currentBooking.room_id) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">时间：</span>
          <span class="value">{{ formatDateTime(currentBooking.start_time) }} - {{ formatTime(currentBooking.end_time) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">参会人数：</span>
          <span class="value">{{ currentBooking.attendees }} 人</span>
        </div>
        <div v-if="currentBooking.description" class="detail-item">
          <span class="label">备注：</span>
          <span class="value">{{ currentBooking.description }}</span>
        </div>
        <div v-if="currentBooking.is_cancelled" class="detail-item cancelled">
          <el-tag type="danger">已取消</el-tag>
          <span class="cancel-info">
            取消时间：{{ formatDateTime(currentBooking.cancelled_at) }}
            <br>
            取消原因：{{ currentBooking.cancel_reason || '无' }}
          </span>
        </div>
      </div>
      <template #footer>
        <template v-if="canCancel(currentBooking)">
          <el-button type="danger" @click="cancelBooking(currentBooking)">取消预约</el-button>
        </template>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { roomApi, bookingApi } from '@/utils/api'

const userStore = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const rooms = ref([])
const bookings = ref([])
const selectedRoomId = ref(null)
const currentDate = ref(dayjs())

const bookingDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const currentBooking = ref(null)
const bookingFormRef = ref()

const bookingForm = reactive({
  room_id: null,
  title: '',
  start_time: null,
  end_time: null,
  attendees: 1,
  description: ''
})

const bookingRules = {
  room_id: [{ required: true, message: '请选择会议室', trigger: 'change' }],
  title: [{ required: true, message: '请输入会议主题', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  attendees: [{ required: true, message: '请输入参会人数', trigger: 'blur' }]
}

const timeSlots = computed(() => {
  const slots = []
  for (let h = 8; h <= 20; h++) {
    slots.push(`${h.toString().padStart(2, '0')}:00`)
    if (h < 20) {
      slots.push(`${h.toString().padStart(2, '0')}:30`)
    }
  }
  return slots
})

const currentDateStr = computed(() => currentDate.value.format('YYYY年MM月DD日 dddd'))

const filteredRooms = computed(() => {
  if (selectedRoomId.value) {
    return rooms.value.filter(r => r.id === selectedRoomId.value)
  }
  return rooms.value
})

const selectedRoom = computed(() => {
  return rooms.value.find(r => r.id === bookingForm.room_id)
})

const fetchRooms = async () => {
  try {
    const data = await roomApi.getRooms()
    rooms.value = data
  } catch (error) {
    console.error(error)
  }
}

const fetchBookings = async () => {
  loading.value = true
  try {
    const startOfDay = currentDate.value.startOf('day').format('YYYY-MM-DDTHH:mm:ss')
    const endOfDay = currentDate.value.endOf('day').format('YYYY-MM-DDTHH:mm:ss')
    const params = {
      start_date: startOfDay,
      end_date: endOfDay
    }
    if (selectedRoomId.value) {
      params.room_id = selectedRoomId.value
    }
    const data = await bookingApi.getBookings(params)
    bookings.value = data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const changeDate = (offset) => {
  currentDate.value = currentDate.value.add(offset, 'day')
}

const goToToday = () => {
  currentDate.value = dayjs()
}

watch(currentDate, () => {
  fetchBookings()
})

const getRoomBookings = (roomId) => {
  return bookings.value.filter(b => b.room_id === roomId)
}

const getRoomName = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.name : '未知'
}

const formatTime = (timeStr) => {
  return dayjs(timeStr).format('HH:mm')
}

const formatDateTime = (timeStr) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

const getBookingStyle = (booking) => {
  const start = dayjs(booking.start_time)
  const end = dayjs(booking.end_time)
  const dayStart = currentDate.value.startOf('day').hour(8)

  const startMinutes = start.diff(dayStart, 'minute')
  const durationMinutes = end.diff(start, 'minute')

  const top = (startMinutes / 30) * 48
  const height = (durationMinutes / 30) * 48 - 4

  return {
    top: `${top}px`,
    height: `${height}px`
  }
}

const openBookingDialog = (room = null, time = null) => {
  isEditing.value = false
  editingId.value = null
  bookingForm.room_id = room?.id || null
  bookingForm.title = ''
  bookingForm.start_time = time || currentDate.value.hour(9).minute(0).second(0).format('YYYY-MM-DDTHH:mm:ss')
  bookingForm.end_time = time ? dayjs(time).add(1, 'hour').format('YYYY-MM-DDTHH:mm:ss') : currentDate.value.hour(10).minute(0).second(0).format('YYYY-MM-DDTHH:mm:ss')
  bookingForm.attendees = 1
  bookingForm.description = ''
  bookingDialogVisible.value = true
}

const handleSlotClick = (room, event) => {
  const cell = event.target.closest('.slot-cell')
  if (cell) {
    const timeStr = cell.dataset.time
    const [hour, minute] = timeStr.split(':').map(Number)
    const time = currentDate.value.hour(hour).minute(minute).second(0)
    if (time.isAfter(dayjs())) {
      openBookingDialog(room, time.format('YYYY-MM-DDTHH:mm:ss'))
    }
  }
}

const showBookingDetail = (booking) => {
  currentBooking.value = booking
  detailDialogVisible.value = true
}

const canCancel = (booking) => {
  if (!booking || booking.is_cancelled) return false
  return booking.user_id === userStore.user?.id || userStore.isAdmin
}

const cancelBooking = async (booking) => {
  try {
    await ElMessageBox.prompt('请输入取消原因（可选）', '取消预约', {
      confirmButtonText: '确定取消',
      cancelButtonText: '返回',
      type: 'warning',
      inputPlaceholder: '请输入取消原因',
      inputRequired: false
    }).then(async ({ value }) => {
      await bookingApi.cancelBooking(booking.id, { reason: value || '' })
      ElMessage.success('取消成功')
      detailDialogVisible.value = false
      fetchBookings()
    })
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const submitBooking = async () => {
  try {
    await bookingFormRef.value.validate()

    const start = dayjs(bookingForm.start_time)
    const end = dayjs(bookingForm.end_time)

    if (end.diff(start, 'minute') < 30) {
      ElMessage.error('预约时长至少30分钟')
      return
    }

    if (start.minute() % 30 !== 0 || end.minute() % 30 !== 0) {
      ElMessage.error('预约必须以30分钟为单位')
      return
    }

    submitting.value = true

    const conflictData = await bookingApi.checkConflict({
      room_id: bookingForm.room_id,
      start_time: bookingForm.start_time,
      end_time: bookingForm.end_time
    })

    if (conflictData.has_conflict) {
      ElMessage.error('该时段已有预约，请选择其他时间')
      return
    }

    await bookingApi.createBooking(bookingForm)
    ElMessage.success('预约成功')
    bookingDialogVisible.value = false
    fetchBookings()
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

const disabledHours = () => {
  const hours = []
  for (let i = 0; i < 8; i++) hours.push(i)
  for (let i = 21; i <= 23; i++) hours.push(i)
  return hours
}

const disabledMinutes = (hour) => {
  if (hour >= 8 && hour <= 20) {
    return [1, 2, 14, 16, 29, 31, 44, 46, 59].filter(m => m !== 0 && m !== 30)
  }
  return []
}

onMounted(() => {
  fetchRooms()
  fetchBookings()
})
</script>

<style scoped>
.calendar-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.room-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
}

.date-nav {
  display: flex;
  align-items: center;
  gap: 16px;
}

.current-date {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.time-grid {
  user-select: none;
}

.time-header {
  display: flex;
  border-bottom: 2px solid #e4e7ed;
  background: #f5f7fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.time-label-col {
  width: 60px;
  min-width: 60px;
  flex-shrink: 0;
}

.room-header {
  flex: 1;
  min-width: 180px;
  padding: 12px;
  text-align: center;
  border-left: 1px solid #e4e7ed;
}

.room-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.room-info {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.time-body {
  display: flex;
  position: relative;
}

.time-slots {
  width: 60px;
  min-width: 60px;
  flex-shrink: 0;
  background: #fafafa;
}

.time-slot-label {
  height: 48px;
  padding: 4px 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
  border-bottom: 1px solid #ebeef5;
}

.booking-areas {
  flex: 1;
  display: flex;
  min-width: 0;
}

.room-column {
  flex: 1;
  min-width: 180px;
  position: relative;
  border-left: 1px solid #e4e7ed;
  cursor: pointer;
}

.slot-cell {
  height: 48px;
  border-bottom: 1px solid #ebeef5;
}

.slot-cell:hover {
  background: #ecf5ff;
}

.booking-block {
  position: absolute;
  left: 4px;
  right: 4px;
  background: #409EFF;
  color: white;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  overflow: hidden;
  cursor: pointer;
  z-index: 5;
  transition: all 0.2s;
}

.booking-block:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.booking-block.is-mine {
  background: #67C23A;
}

.booking-block.is-cancelled {
  background: #909399;
  text-decoration: line-through;
  opacity: 0.7;
}

.booking-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.booking-time {
  font-size: 11px;
  opacity: 0.9;
}

.booking-detail {
  font-size: 14px;
}

.detail-item {
  display: flex;
  margin-bottom: 12px;
}

.detail-item .label {
  width: 80px;
  color: #909399;
  flex-shrink: 0;
}

.detail-item .value {
  color: #303133;
}

.detail-item.cancelled {
  flex-direction: column;
  gap: 8px;
  background: #fef0f0;
  padding: 12px;
  border-radius: 4px;
}

.cancel-info {
  font-size: 13px;
  color: #f56c6c;
}

.capacity-hint {
  margin-left: 8px;
  font-size: 13px;
  color: #909399;
}
</style>
