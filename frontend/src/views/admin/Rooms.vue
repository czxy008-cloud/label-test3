<template>
  <div class="admin-rooms-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">会议室管理</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新增会议室
          </el-button>
        </div>
      </template>

      <el-table :data="rooms" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="会议室名称" min-width="150" />
        <el-table-column prop="capacity" label="容纳人数" width="100" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="设备标签" min-width="250">
          <template #default="{ row }">
            <el-tag
              v-for="facility in row.facilities"
              :key="facility"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ facility }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
            <el-tag v-else type="info" size="small">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && rooms.length === 0" description="暂无会议室" />
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑会议室' : '新增会议室'"
      width="550px"
    >
      <el-form :model="roomForm" :rules="roomRules" ref="roomFormRef" label-width="100px">
        <el-form-item label="会议室名称" prop="name">
          <el-input v-model="roomForm.name" placeholder="请输入会议室名称" />
        </el-form-item>
        <el-form-item label="容纳人数" prop="capacity">
          <el-input-number v-model="roomForm.capacity" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="roomForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="设备标签" prop="facilities">
          <el-select
            v-model="roomForm.facilities"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入设备标签"
            style="width: 100%"
          >
            <el-option
              v-for="facility in availableFacilities"
              :key="facility"
              :label="facility"
              :value="facility"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isEditing" label="状态">
          <el-switch v-model="roomForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { roomApi } from '@/utils/api'

const loading = ref(false)
const submitting = ref(false)
const rooms = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const roomFormRef = ref()

const availableFacilities = [
  '投影仪', '白板', '视频会议', '音响系统', '麦克风', '电视', '电脑', '空调', '饮水机', '白板笔'
]

const roomForm = reactive({
  name: '',
  capacity: 10,
  description: '',
  facilities: [],
  is_active: true
})

const roomRules = {
  name: [{ required: true, message: '请输入会议室名称', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容纳人数', trigger: 'blur' }]
}

const fetchRooms = async () => {
  loading.value = true
  try {
    const data = await roomApi.getAllRooms()
    rooms.value = data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const formatDateTime = (timeStr) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

const openCreateDialog = () => {
  isEditing.value = false
  editingId.value = null
  roomForm.name = ''
  roomForm.capacity = 10
  roomForm.description = ''
  roomForm.facilities = []
  roomForm.is_active = true
  dialogVisible.value = true
}

const openEditDialog = (room) => {
  isEditing.value = true
  editingId.value = room.id
  roomForm.name = room.name
  roomForm.capacity = room.capacity
  roomForm.description = room.description || ''
  roomForm.facilities = [...room.facilities]
  roomForm.is_active = room.is_active
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await roomFormRef.value.validate()
    submitting.value = true

    if (isEditing.value) {
      await roomApi.updateRoom(editingId.value, roomForm)
      ElMessage.success('更新成功')
    } else {
      await roomApi.createRoom(roomForm)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchRooms()
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const toggleStatus = async (room) => {
  try {
    await ElMessageBox.confirm(
      `确定要${room.is_active ? '停用' : '启用'}会议室「${room.name}」吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await roomApi.updateRoom(room.id, { is_active: !room.is_active })
    ElMessage.success('操作成功')
    fetchRooms()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

onMounted(() => {
  fetchRooms()
})
</script>

<style scoped>
.admin-rooms-page {
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
</style>
