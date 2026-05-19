<template>
  <div class="my-bookings-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">我的预约</span>
          <el-switch
            v-model="includeCancelled"
            active-text="显示已取消"
            inactive-text="仅有效"
            @change="fetchBookings"
          />
        </div>
      </template>

      <el-table :data="bookings" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="会议主题" min-width="150" />
        <el-table-column label="会议室" width="140">
          <template #default="{ row }">
            {{ getRoomName(row.room_id) }}
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="260">
          <template #default="{ row }">
            <div>{{ formatDateTime(row.start_time) }}</div>
            <div class="time-to">至</div>
            <div>{{ formatDateTime(row.end_time) }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="attendees" label="人数" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_cancelled" type="danger" size="small">已取消</el-tag>
            <el-tag v-else type="success" size="small">有效</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="!row.is_cancelled"
              size="small"
              type="danger"
              @click="cancelBooking(row)
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && bookings.length === 0" description="暂无预约记录" />
    </el-card>

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
          <span class="label">开始时间：</span>
          <span class="value">{{ formatDateTime(currentBooking.start_time) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">结束时间：</span>
          <span class="value">{{ formatDateTime(currentBooking.end_time) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">参会人数：</span>
          <span class="value">{{ currentBooking.attendees }} 人</span>
        </div>
        <div v-if="currentBooking.description" class="detail-item">
          <span class="label">备注：</span>
          <span class="value">{{ currentBooking.description }}</span>
        </div>
        <div class="detail-item">
          <span class="label">创建时间：</span>
          <span class="value">{{ formatDateTime(currentBooking.created_at) }}</span>
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
        <template v-if="!currentBooking?.is_cancelled">
          <el-button type="danger" @click="cancelBooking(currentBooking)">取消预约</el-button>
        </template>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roomApi, bookingApi } from '@/utils/api'

const loading = ref(false)
const bookings = ref([])
const rooms = ref([])
const includeCancelled = ref(false)
const detailDialogVisible = ref(false)
const currentBooking = ref(null)

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
    const data = await bookingApi.getMyBookings({ include_cancelled: includeCancelled.value })
    bookings.value = data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const getRoomName = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.name : '未知'
}

const formatDateTime = (timeStr) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

const showDetail = (booking) => {
  currentBooking.value = booking
  detailDialogVisible.value = true
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

onMounted(() => {
  fetchRooms()
  fetchBookings()
})
</script>

<style scoped>
.my-bookings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

.time-to {
  color: #909399;
  font-size: 12px;
  margin: 2px 0;
}

.booking-detail {
  font-size: 14px;
}

.detail-item {
  display: flex;
  margin-bottom: 12px;
}

.detail-item .label {
  width: 100px;
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
</style>
