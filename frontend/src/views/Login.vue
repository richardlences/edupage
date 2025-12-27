<template>
  <v-app :class="isDark ? 'bg-background' : 'bg-grey-lighten-5'">
    <!-- Theme Toggle -->
    <div class="position-absolute d-flex align-center" style="top: 16px; right: 16px;">
      <v-btn icon variant="text" @click="toggleLanguage" class="mr-2">
        <span class="text-button font-weight-bold">{{ locale.toUpperCase() }}</span>
      </v-btn>
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
            <h1 class="text-h4 font-weight-black" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">{{ $t('app.title') }}</h1>
            <p class="text-subtitle-1" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'">{{ $t('app.subtitle') }}</p>
          </div>

          <v-card class="rounded-xl elevation-8" border>
            <v-card-text class="pa-8">
              <h2 class="text-h5 font-weight-bold text-center mb-1" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">{{ $t('login.welcome') }}</h2>
              <p class="text-center text-caption mb-6" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'" v-html="$t('login.instruction')"></p>
              
              <v-form @submit.prevent="handleLogin">
                <v-text-field
                  :label="$t('login.username')"
                  v-model="username"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  color="deep-orange"
                  :bg-color="isDark ? 'grey-darken-3' : 'grey-lighten-5'"
                  type="text"
                  required
                  class="mb-4"
                  name="username"
                  autocomplete="username"
                ></v-text-field>
                
                <v-text-field
                  :label="$t('login.password')"
                  v-model="password"
                  prepend-inner-icon="mdi-lock"
                  variant="outlined"
                  color="deep-orange"
                  :bg-color="isDark ? 'grey-darken-3' : 'grey-lighten-5'"
                  :type="visible ? 'text' : 'password'"
                  :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append-inner="visible = !visible"
                  required
                  class="mb-6"
                  name="password"
                  autocomplete="current-password"
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
                  type="submit"
                  color="deep-orange" 
                  size="large" 
                  block 
                  flat 
                  class="font-weight-bold text-uppercase letter-spacing-1"
                  @click="handleLogin" 
                  :loading="loading"
                  height="56"
                >
                  {{ $t('login.sign_in') }}
                </v-btn>
              </v-form>
            </v-card-text>
          </v-card>
          
          <div class="text-center mt-6 text-caption text-grey">
            &copy; {{ new Date().getFullYear() }} {{ $t('app.copyright') }}
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
import { useI18n } from 'vue-i18n'

const authStore = useAuthStore()
const router = useRouter()
const theme = useTheme()
const { t, locale } = useI18n()

// Theme Logic
const isDark = computed(() => theme.current.value.dark)
const toggleTheme = () => {
    theme.toggle()
    localStorage.setItem('theme', theme.name.value)
}

const toggleLanguage = () => {
    const newLocale = locale.value === 'en' ? 'sk' : 'en'
    locale.value = newLocale
    localStorage.setItem('locale', newLocale)
}

const username = ref('')
const password = ref('')
const visible = ref(false)
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
      error.value = t('login.invalid_credentials')
    }
  } catch (e) {
    error.value = t('login.error')
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
