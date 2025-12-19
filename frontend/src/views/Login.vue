<template>
  <v-app :class="isDark ? 'bg-background' : 'bg-grey-lighten-5'">
    <!-- Theme Toggle -->
    <div class="position-absolute" style="top: 16px; right: 16px;">
      <v-btn icon variant="text" @click="toggleTheme">
        <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </div>

    <v-container class="fill-height" fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="5" lg="4">
          
          <!-- Brand Logo Area -->
          <div class="text-center mb-8">
            <v-avatar color="deep-orange" size="80" class="elevation-4 mb-4">
              <v-icon color="white" size="40">mdi-food-fork-drink</v-icon>
            </v-avatar>
            <h1 class="text-h4 font-weight-black" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">EduLunch</h1>
            <p class="text-subtitle-1" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'">Premium School Dining Experience</p>
          </div>

          <v-card class="rounded-xl elevation-8" border>
            <v-card-text class="pa-8">
              <h2 class="text-h5 font-weight-bold text-center mb-1" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">Welcome Back</h2>
              <p class="text-center text-caption mb-6" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'">
                Please use your official <strong>Edupage</strong> credentials
              </p>
              
              <v-form @submit.prevent="handleLogin">
                <v-text-field
                  label="Username"
                  v-model="username"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  color="deep-orange"
                  :bg-color="isDark ? 'grey-darken-3' : 'grey-lighten-5'"
                  type="text"
                  required
                  class="mb-4"
                ></v-text-field>
                
                <v-text-field
                  label="Password"
                  v-model="password"
                  prepend-inner-icon="mdi-lock"
                  variant="outlined"
                  color="deep-orange"
                  :bg-color="isDark ? 'grey-darken-3' : 'grey-lighten-5'"
                  type="password"
                  required
                  class="mb-6"
                ></v-text-field>

                <v-alert 
                  v-if="error" 
                  type="error" 
                  variant="tonal" 
                  class="mb-6 rounded-lg"
                  icon="mdi-alert-circle-outline"
                >
                  {{ error }}
                </v-alert>

                <v-btn 
                  color="deep-orange" 
                  size="large" 
                  block 
                  flat 
                  class="font-weight-bold text-uppercase letter-spacing-1"
                  @click="handleLogin" 
                  :loading="loading"
                  height="56"
                >
                  Sign In
                </v-btn>
              </v-form>
            </v-card-text>
          </v-card>
          
          <div class="text-center mt-6 text-caption text-grey">
            &copy; {{ new Date().getFullYear() }} EduLunch App
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'

const authStore = useAuthStore()
const router = useRouter()
const theme = useTheme()

// Theme Logic
const isDark = computed(() => theme.current.value.dark)
const toggleTheme = () => {
    theme.toggle()
    localStorage.setItem('theme', theme.name.value)
}

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const success = await authStore.login(username.value, password.value, '1sg')
    if (success) {
      router.push('/')
    } else {
      error.value = 'Invalid credentials'
    }
  } catch (e) {
    error.value = 'An error occurred'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Load saved theme
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    theme.change(savedTheme)
  }
})
</script>

<style scoped>
.letter-spacing-1 {
  letter-spacing: 1px !important;
}
</style>
