import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/axios'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => !!user.value?.is_admin)

  const login = async (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await request.post('/auth/login', formData)
    user.value = response.user
    token.value = response.access_token
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    return response
  }

  const register = async (userData) => {
    return await request.post('/auth/register', userData)
  }

  const logout = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const fetchCurrentUser = async () => {
    try {
      const data = await request.get('/auth/me')
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
      return data
    } catch (error) {
      logout()
      throw error
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    login,
    register,
    logout,
    fetchCurrentUser
  }
})
