import { defineStore } from 'pinia'
import api from '@/api'
import { ref } from 'vue'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
    const user = ref<{ id: number, username: string } | null>(null)
    const isAuthenticated = ref(false)

    // Initialize from local storage
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
        user.value = JSON.parse(storedUser)
        isAuthenticated.value = true
    }

    async function login(username: string, password: string, subdomain: string) {
        try {
            const response = await api.post('/api/auth/login', {
                username,
                password,
                subdomain
            })
            user.value = response.data
            isAuthenticated.value = true
            localStorage.setItem('user', JSON.stringify(user.value))
            router.push('/')
            return true
        } catch (error) {
            console.error('Login failed', error)
            return false
        }
    }

    function logout() {
        user.value = null
        isAuthenticated.value = false
        localStorage.removeItem('user')
        router.push('/login')
    }

    return { user, isAuthenticated, login, logout }
})
