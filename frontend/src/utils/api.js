import request from './axios'

export const roomApi = {
  getRooms: () => request.get('/rooms'),
  getAllRooms: () => request.get('/rooms/all'),
  getRoom: (id) => request.get(`/rooms/${id}`),
  createRoom: (data) => request.post('/rooms', data),
  updateRoom: (id, data) => request.put(`/rooms/${id}`, data),
  deleteRoom: (id) => request.delete(`/rooms/${id}`)
}

export const bookingApi = {
  getBookings: (params) => request.get('/bookings', { params }),
  getMyBookings: (params) => request.get('/bookings/my', { params }),
  getBooking: (id) => request.get(`/bookings/${id}`),
  createBooking: (data) => request.post('/bookings', data),
  updateBooking: (id, data) => request.put(`/bookings/${id}`, data),
  cancelBooking: (id, data) => request.post(`/bookings/${id}/cancel`, data),
  deleteBooking: (id) => request.delete(`/bookings/${id}`),
  checkConflict: (params) => request.get('/bookings/conflict/check', { params })
}
