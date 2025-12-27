<template>
  <v-app :class="isDark ? 'bg-background' : 'bg-grey-lighten-5'">
    <!-- Modern Header with Gradient -->
    <v-app-bar app elevation="0" class="px-2" color="transparent">
      <template v-slot:image>
        <div class="d-flex w-100 h-100 bg-deep-orange-lighten-1" style="opacity: 0.95;"></div>
      </template>
      
      <v-container class="d-flex align-center py-0" style="max-width: 1000px;">
        <v-avatar color="white" size="42" class="mr-3 elevation-2">
          <v-icon color="deep-orange" size="24">mdi-food-fork-drink</v-icon>
        </v-avatar>
        
        <div class="d-flex flex-column">
          <v-toolbar-title class="font-weight-black text-h6 text-white" style="line-height: 1.1;">
            {{ $t('app.title') }}
          </v-toolbar-title>
          <span class="text-caption text-white font-weight-medium" style="opacity: 0.9;">{{ $t('app.short_subtitle') }}</span>
        </div>
        
        <v-spacer></v-spacer>
        
        <div class="d-flex align-center">
          <span class="text-body-2 mr-4 text-white font-weight-medium hidden-sm-and-down">
            {{ $t('dashboard.hello', { name: authStore.user?.username }) }}
          </span>
          
          <v-btn 
            icon 
            variant="text" 
            color="white" 
            class="mr-2"
            @click="toggleLanguage"
          >
            <span class="text-button font-weight-bold">{{ locale.toUpperCase() }}</span>
          </v-btn>
          
          <v-btn 
            icon 
            variant="text" 
            color="white" 
            class="mr-2"
            @click="toggleTheme"
          >
            <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
          </v-btn>

          <v-btn 
            variant="flat" 
            color="white" 
            size="small" 
            class="text-deep-orange font-weight-bold"
            prepend-icon="mdi-logout"
            @click="handleLogout"
          >
            {{ $t('dashboard.logout') }}
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container class="py-4" style="max-width: 1000px;">
        
        <!-- Date Navigation - Floating Card Style -->
        <v-card class="mb-4 rounded-xl mx-auto" elevation="4" max-width="600" border>
          <div class="d-flex justify-space-between align-center pa-1">
            <v-btn icon="mdi-chevron-left" variant="text" size="large" color="deep-orange" @click="changeDay(-1)"></v-btn>
            
            <div class="text-center py-2">
              <div class="text-h6 font-weight-black" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">{{ formattedDate }}</div>
              <div class="text-subtitle-2 text-uppercase text-deep-orange font-weight-bold letter-spacing-2">{{ dayName }}</div>
            </div>
            
            <v-btn icon="mdi-chevron-right" variant="text" size="large" color="deep-orange" @click="changeDay(1)"></v-btn>
          </div>
        </v-card>

        <div class="position-relative">
          <!-- Ordered Meal Summary -->
        <v-card
          v-if="orderedLunch"
          class="mb-4 rounded-xl border-success-glow"
          elevation="4"
          :color="isDark ? 'green-darken-4' : 'green-lighten-5'"
        >
          <div class="d-flex align-center justify-start pa-2" style="gap: 8px;">
            <div class="d-flex align-center flex-grow-1" style="min-width: 0;">
              <v-avatar color="success" size="32" class="mr-2 elevation-2 flex-shrink-0">
                <v-icon color="white" size="18">mdi-check</v-icon>
              </v-avatar>
              <div style="min-width: 0;">
                <div class="text-caption font-weight-bold mb-0" style="font-size: 0.65rem !important; line-height: 1;" :class="isDark ? 'text-green-lighten-2' : 'text-green-darken-3'">{{ $t('dashboard.ordered_label') }}</div>
                <div class="text-subtitle-1 font-weight-black" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'" style="line-height: 1.2; white-space: normal;">
                  {{ orderedLunch.name }}
                </div>
              </div>
            </div>
            
            <div class="flex-shrink-0">
              <v-btn
                v-if="canModifyLunch(orderedLunch)"
                color="error"
                variant="text"
                class="font-weight-bold"
                prepend-icon="mdi-close-circle"
                :loading="actionLoading['cancel-' + orderedLunch.index]"
                :disabled="refreshing"
                @click="cancelLunch(orderedLunch.index)"
              >
                {{ $t('dashboard.cancel') }}
              </v-btn>
              <v-chip
                v-else
                color="success"
                variant="tonal"
                class="font-weight-bold"
                prepend-icon="mdi-check-circle"
              >
                {{ $t('dashboard.confirmed') }}
              </v-chip>
            </div>
          </div>
        </v-card>

        <!-- Initial Loading State -->
        <div v-if="loading && (!lunches || lunches.length === 0)" class="d-flex flex-column align-center justify-center py-16">
          <v-progress-circular indeterminate color="deep-orange" size="64" width="6"></v-progress-circular>
          <div class="mt-4 text-h6 font-weight-light" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'">{{ $t('dashboard.preparing_menu') }}</div>
        </div>

        <!-- Error State -->
        <v-alert 
          v-else-if="error" 
          type="error" 
          variant="tonal" 
          border="start" 
          class="mb-6 rounded-lg"
          icon="mdi-alert-circle-outline"
        >
          {{ error }}
        </v-alert>

        <!-- No Lunches State -->
        <div v-else-if="!lunches || lunches.length === 0" class="text-center py-16">
          <v-avatar :color="isDark ? 'grey-darken-3' : 'grey-lighten-4'" size="120" class="mb-6">
            <v-icon size="64" :color="isDark ? 'grey-darken-1' : 'grey-lighten-1'">mdi-silverware-clean</v-icon>
          </v-avatar>
          <div class="text-h5 font-weight-bold" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-2'">{{ $t('dashboard.no_service_title') }}</div>
          <div class="text-body-1 mt-2" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'">{{ $t('dashboard.no_service_desc') }}</div>
        </div>

        <!-- Lunches List -->
        <div v-else class="d-flex flex-column" :class="{'stale-data': isStale}">
          
          <!-- Soup Section - Ultra Compact -->
          <v-card 
            v-if="soup" 
            class="rounded-xl mb-4 overflow-hidden" 
            elevation="2"
            border
            :color="isDark ? 'brown-darken-4' : 'orange-lighten-5'"
          >
            <div class="px-4 py-2 d-flex align-center">
              <v-icon color="deep-orange" class="mr-3" size="small">mdi-bowl-mix</v-icon>
              <div class="d-flex flex-column">
                <span class="text-caption font-weight-bold text-deep-orange text-uppercase" style="line-height: 1; font-size: 0.65rem !important;">{{ $t('dashboard.soup_label') }}</span>
                <div class="text-subtitle-1 font-weight-bold mt-0" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">
                  {{ soup.name }}
                </div>
              </div>
            </div>
          </v-card>

          <!-- Main Meals Grid -->
          <v-row class="ma-0">
            <v-col cols="12" v-for="lunch in mainMeals" :key="lunch.index" class="pa-0 mb-4">
              <v-card 
                class="rounded-xl overflow-hidden transition-swing" 
                :elevation="lunch.is_ordered ? 8 : 2"
                :class="{'border-success-glow': lunch.is_ordered}"
                border
              >
                <div class="d-flex flex-column flex-md-row">
                  
                  <!-- Meal Image Area (Only if photos exist) -->
                  <div 
                    v-if="lunch.photos && lunch.photos.length > 0" 
                    class="meal-image-container position-relative d-flex align-center justify-center shrink-0" 
                    :class="isDark ? 'bg-grey-darken-4' : 'bg-grey-lighten-4'" 
                  >
                    <!-- Ordered Badge Removed from here -->

                    <!-- Image Carousel -->
                    <v-carousel
                      height="100%"
                      hide-delimiter-background
                      show-arrows="hover"
                      cycle
                      interval="5000"
                    >
                      <v-carousel-item
                        v-for="(photo, i) in lunch.photos"
                        :key="i"
                        :src="photo"
                        cover
                        @click="openLightbox(lunch.photos, Number(i))"
                        style="cursor: zoom-in;"
                      ></v-carousel-item>
                    </v-carousel>
                    
                    <!-- Photo Management Button (Top Right) -->
                    <div 
                      v-if="canRateMeal(lunch)"
                      class="position-absolute"
                      style="top: 8px; right: 8px; z-index: 5;"
                    >
                      <!-- If user has photo: Menu with Change/Remove -->
                      <v-menu v-if="lunch.user_has_photo" location="bottom end">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            v-bind="props"
                            icon
                            size="x-small"
                            color="white"
                            class="text-deep-orange"
                            elevation="2"
                            :loading="actionLoading[lunch.name]"
                            :disabled="refreshing"
                          >
                            <v-icon size="small">mdi-cog</v-icon>
                          </v-btn>
                        </template>
                        <v-list density="compact" elevation="3" class="rounded-lg">
                          <v-list-item @click="triggerFileInput(lunch.index)" prepend-icon="mdi-upload" class="text-body-2">
                            <v-list-item-title>{{ $t('dashboard.change_photo') }}</v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="deletePhoto(lunch.name)" prepend-icon="mdi-delete" class="text-error text-body-2">
                            <v-list-item-title>{{ $t('dashboard.remove_photo') }}</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>

                      <!-- If user has NO photo but photos exist: Simple Add Button -->
                      <v-btn
                        v-else-if="lunch.photos.length < 5"
                        icon
                        size="x-small"
                        color="white"
                        class="text-deep-orange"
                        elevation="2"
                        :loading="actionLoading[lunch.name]"
                        :disabled="refreshing"
                        @click="triggerFileInput(lunch.index)"
                      >
                        <v-icon size="small">mdi-camera-plus</v-icon>
                      </v-btn>

                      <input 
                        type="file" 
                        :ref="(el) => setFileInputRef(el, lunch.index)"
                        class="d-none" 
                        @change="(e) => handleFileUpload(e, lunch.name)"
                        accept="image/*"
                      >
                    </div>
                  </div>

                  <!-- Meal Content -->
                  <div 
                    class="flex-grow-1 pa-3 d-flex flex-column justify-space-between"
                    :class="lunch.is_ordered ? (isDark ? 'bg-green-darken-4' : 'bg-green-lighten-5') : (isDark ? 'bg-surface' : 'bg-white')"
                  >
                    <div>
                      <div class="d-flex justify-space-between align-start mb-1">
                        <div class="d-flex align-center">
                          <v-avatar 
                            :color="lunch.is_ordered ? 'success' : 'grey-lighten-3'" 
                            size="32" 
                            class="elevation-1 mr-2"
                          >
                            <span 
                              class="font-weight-black text-body-2"
                              :class="lunch.is_ordered ? 'text-white' : 'text-grey-darken-2'"
                            >
                              {{ lunch.number || lunch.index }}
                            </span>
                          </v-avatar>
                          
                          <!-- Dynamic Ordered Chip (Always show if ordered) -->
                          <v-chip 
                            v-if="lunch.is_ordered"
                            color="success" 
                            variant="flat" 
                            size="x-small"
                            class="font-weight-bold px-2"
                            prepend-icon="mdi-check-circle"
                          >
                            {{ $t('dashboard.ordered') }}
                          </v-chip>
                        </div>
                        
                        <div class="d-flex align-center">
                          <v-icon color="amber-darken-2" size="x-small" class="mr-1">mdi-star</v-icon>
                          <span class="text-body-2 font-weight-bold" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'">{{ lunch.avg_rating || '--' }}</span>
                          <span class="text-caption ml-1 font-weight-medium" style="font-size: 0.7rem !important;" :class="isDark ? 'text-medium-emphasis' : 'text-grey-darken-1'" v-if="lunch.avg_rating">/ 5</span>
                        </div>
                      </div>
                      
                      <div class="text-subtitle-1 font-weight-bold mb-1" :class="isDark ? 'text-high-emphasis' : 'text-grey-darken-3'" style="line-height: 1.2;">
                        {{ lunch.name }}
                      </div>

                      <!-- Compact Photo Upload (Only if no photo) -->
                      <div v-if="!lunch.photos || lunch.photos.length === 0" class="mt-1">
                        <div v-if="canRateMeal(lunch)" class="d-flex align-center">
                           <v-btn
                            variant="tonal"
                            size="x-small"
                            color="deep-orange"
                            prepend-icon="mdi-camera-plus"
                            class="font-weight-bold text-caption"
                            :loading="actionLoading[lunch.name]"
                            :disabled="refreshing"
                            @click="triggerFileInput(lunch.index)"
                            style="height: 24px;"
                          >
                            {{ $t('dashboard.add_photo') }}
                          </v-btn>
                          <input 
                            type="file" 
                            :ref="(el) => setFileInputRef(el, lunch.index)"
                            class="d-none" 
                            @change="(e) => handleFileUpload(e, lunch.name)"
                            accept="image/*"
                          >
                        </div>
                        <div v-else class="text-caption d-flex align-center" :class="isDark ? 'text-grey-lighten-1' : 'text-grey-darken-1'" style="font-size: 0.75rem !important;">
                          <v-icon size="x-small" class="mr-1">mdi-camera-off</v-icon>
                          {{ $t('dashboard.no_photos') }}
                        </div>
                      </div>
                    </div>

                    <div class="d-flex align-center justify-space-between mt-2 pt-2 border-t" :class="lunch.is_ordered ? 'border-green-lighten-4' : 'border-grey-lighten-4'">
                      
                      <!-- Rating Area (Only show if user can rate) -->
                      <div class="d-flex flex-column" v-if="canRateMeal(lunch)">
                        <span class="text-caption font-weight-bold mb-0" style="font-size: 0.6rem !important;" :class="lunch.is_ordered ? 'text-green-darken-2' : 'text-grey-darken-1'">
                          {{ $t('dashboard.rate_meal') }}
                        </span>
                        <v-rating
                          v-model="userRatings[lunch.name]"
                          color="amber-darken-2"
                          active-color="amber-darken-2"
                          density="compact"
                          hover
                          half-increments
                          :disabled="refreshing || actionLoading[lunch.name]"
                          @update:modelValue="(val) => rateLunch(lunch.name, Number(val))"
                          size="32"
                        ></v-rating>
                      </div>
                      <div v-else></div> <!-- Spacer if no rating -->

                      <!-- Action Buttons -->
                      <div>
                        <!-- Deadline/Status Message -->
                        <v-chip
                          v-if="!canModifyLunch(lunch)"
                          :color="lunch.is_ordered ? 'success' : 'grey'"
                          variant="tonal"
                          class="font-weight-medium"
                          :prepend-icon="lunch.is_ordered ? 'mdi-check' : 'mdi-lock'"
                        >
                          {{ getModificationMessage(lunch) }}
                        </v-chip>
                                                <!-- Cancel Button -->
                        <v-btn
                          v-else-if="lunch.is_ordered"
                          color="error"
                          variant="flat"
                          prepend-icon="mdi-close-circle-outline"
                          :loading="actionLoading['cancel-' + lunch.index]"
                          :disabled="refreshing"
                          @click="cancelLunch(lunch.index)"
                          class="text-capitalize font-weight-bold"
                        >
                          {{ $t('dashboard.cancel_order') }}
                        </v-btn>
                        
                        <!-- Order Button -->
                        <v-btn
                          v-else
                          color="deep-orange"
                          variant="flat"
                          elevation="2"
                          prepend-icon="mdi-silverware-fork-knife"
                          :loading="actionLoading['order-' + lunch.index]"
                          :disabled="refreshing"
                          @click="orderLunch(lunch.index)"
                          class="text-capitalize font-weight-bold px-6"
                        >
                          {{ $t('dashboard.order_meal') }}
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- Scoped Refreshing Overlay (Covers everything below navigation) -->
        <v-overlay
          :model-value="refreshing"
          class="align-center justify-center"
          contained
          persistent
          :scrim="isDark ? 'black' : 'white'"
          :opacity="isDark ? 0.3 : 0.5"
        >
          <v-progress-circular indeterminate color="deep-orange" size="48"></v-progress-circular>
        </v-overlay>
        </div> <!-- End of position-relative wrapper -->

      </v-container>
    </v-main>
    <!-- Lightbox Dialog -->
    <v-dialog v-model="lightboxOpen" fullscreen bg-color="black" transition="dialog-bottom-transition">
      <v-card color="black" class="d-flex align-center justify-center fill-height position-relative">
        <v-btn icon="mdi-close" variant="text" color="white" size="large" class="position-absolute" style="top: 20px; right: 20px; z-index: 100;" @click="lightboxOpen = false"></v-btn>
        
        <v-carousel
          v-model="lightboxIndex"
          height="100%"
          hide-delimiter-background
          show-arrows="hover"
          :show-arrows-on-hover="false"
        >
          <v-carousel-item
            v-for="(photo, i) in lightboxPhotos"
            :key="i"
            :src="photo"
            contain
          ></v-carousel-item>
        </v-carousel>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import api from '@/api';
import { useRouter } from 'vue-router';
import { useTheme } from 'vuetify';
import imageCompression from 'browser-image-compression';
import { useI18n } from 'vue-i18n';

const authStore = useAuthStore();
const router = useRouter();
const theme = useTheme();
const { t, locale } = useI18n();

// Theme Logic
const isDark = computed(() => theme.current.value.dark);
const toggleTheme = () => {
  theme.toggle();
  localStorage.setItem('theme', theme.name.value);
};

const toggleLanguage = () => {
    const newLocale = locale.value === 'en' ? 'sk' : 'en'
    locale.value = newLocale
    localStorage.setItem('locale', newLocale)
}

const currentDate = ref(new Date());
const lunches = ref<any[]>([]);
const loading = ref(false);
const refreshing = ref(false);
const isStale = ref(false); // True when showing cached data while fetching fresh
const actionLoading = ref<Record<string, boolean>>({});
const error = ref('');
const userRatings = ref<Record<string, number>>({});
const fileInputRefs = ref<Record<string, HTMLInputElement>>({});
const lightboxOpen = ref(false);
const lightboxPhotos = ref<string[]>([]);
const lightboxIndex = ref(0);

// Request cancellation and caching
let fetchController: AbortController | null = null;
const lunchCache = new Map<string, any[]>();
const lastRequestId = ref(0);

const setFileInputRef = (el: any, key: string | number) => {
  if (el) {
    fileInputRefs.value[key] = el as HTMLInputElement;
  }
};

const triggerFileInput = (key: string | number) => {
  fileInputRefs.value[key]?.click();
};

const openLightbox = (photos: string[], index: number) => {
  lightboxPhotos.value = photos;
  lightboxIndex.value = index;
  lightboxOpen.value = true;
};

const deletePhoto = async (mealName: string) => {
  if (!confirm(t('dialogs.remove_photo_confirm'))) return;
  
  actionLoading.value[mealName] = true;
  try {
    await api.post('/api/social/delete_photo', {
      meal_identifier: mealName
    }, {
      headers: { 'user-id': authStore.user?.id }
    });
    await fetchLunches();
  } catch (e) {
    alert(t('errors.delete_photo_failed'));
    console.error(e);
  } finally {
    actionLoading.value[mealName] = false;
  }
};

const formattedDate = computed(() => {
  return currentDate.value.toLocaleDateString(locale.value === 'sk' ? 'sk-SK' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' });
});

const orderedLunch = computed(() => {
    if (!lunches.value || lunches.value.length === 0) return null;
    // Find the ordered meal in the main meals (index > 0)
    return lunches.value.slice(1).find(l => l.is_ordered);
});

const dayName = computed(() => {
  return currentDate.value.toLocaleDateString(locale.value === 'sk' ? 'sk-SK' : 'en-US', { weekday: 'long' });
});

// Filter soup and main meals
const soup = computed(() => {
    if (lunches.value.length > 0) {
        return lunches.value[0];
    }
    return null;
});

const mainMeals = computed(() => {
    if (lunches.value.length > 0) {
        return lunches.value.slice(1);
    }
    return [];
});

// Check if a meal can be rated (must be in the past and must have been ordered)
const canRateMeal = (lunch: any) => {
    // Check if lunch date is in the past
    if (!lunch.date) return false;
    const lunchDate = new Date(lunch.date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    lunchDate.setHours(0, 0, 0, 0);
    
    // Can only rate if date is in the past and the meal was ordered
    return ((lunchDate.getTime() === today.getTime() && new Date().getHours() >= 11) || (lunchDate < today)) && lunch.is_ordered;
};

// Check if a lunch can still be modified (ordered/canceled/changed)
const canModifyLunch = (lunch: any) => {
    // Check if there's a deadline
    if (!lunch.can_be_changed_until) return true; // No deadline means always modifiable
    
    // Parse deadline and current time
    const deadline = new Date(lunch.can_be_changed_until);
    const now = new Date();
    
    // Can modify if we're before the deadline
    if (!orderedLunch.value) {
      deadline.setDate(deadline.getDate() - 1);
      deadline.setHours(14, 0, 0, 0);
    }
    return now < deadline;
};

// Get message for why modification is disabled
const getModificationMessage = (lunch: any) => {
    if (!canModifyLunch(lunch)) {
        if (lunch.is_ordered) {
            return t('dashboard.status.too_late');
        } else {
            return t('dashboard.status.ordering_closed');
        }
    }
    return null;
};

const syncUserRatings = (lunchesList: any[]) => {
  for (const lunch of lunchesList) {
    if (lunch.user_rating !== null && lunch.user_rating !== undefined) {
      userRatings.value[lunch.name] = lunch.user_rating;
    }
  }
};

const fetchLunches = async (forceRefresh = false) => {
  const dateStr = currentDate.value.toISOString().split('T')[0] as string;
  const requestId = ++lastRequestId.value;
  
  // Abort any in-flight request
  if (fetchController) {
    fetchController.abort();
  }
  fetchController = new AbortController();
  
  // Check cache first
  const cached = lunchCache.get(dateStr);
  if (cached && cached.length > 0) {
    lunches.value = cached;
    syncUserRatings(cached);
    isStale.value = true; // Mark as stale while we refresh
    refreshing.value = true;
  } else {
    lunches.value = []; // Clear previous data on cache miss so the loading spinner shows
    loading.value = true;
    isStale.value = false;
  }
  
  error.value = '';
  
  try {
    const response = await api.get(`/api/lunches/?day=${dateStr}`, {
      headers: { 'user-id': String(authStore.user?.id) },
      signal: fetchController.signal
    });
    
    // Only update state if this is still the most recent request
    if (requestId === lastRequestId.value) {
      // Update cache and state
      lunchCache.set(dateStr, response.data);
      lunches.value = response.data;
      syncUserRatings(response.data);
      isStale.value = false;
    }
  } catch (e: any) {
    // Ignore aborted requests
    if (e.name === 'CanceledError' || e.code === 'ERR_CANCELED') {
      return;
    }
    console.error(e);
    // Only show error if we don't have cached data to show and this is still current
    if (requestId === lastRequestId.value && (!cached || cached.length === 0)) {
      error.value = t('errors.fetch_failed') || 'Failed to load lunches.';
    }
  } finally {
    // Only clear loading state if this is still the latest request
    if (requestId === lastRequestId.value) {
      loading.value = false;
      refreshing.value = false;
    }
  }
};

const changeDay = (days: number) => {
  const newDate = new Date(currentDate.value);
  newDate.setDate(newDate.getDate() + days);
  
  // Skip weekends
  if (newDate.getDay() === 0) { // Sunday -> Friday (if going back) or Monday (if going forward)
      newDate.setDate(newDate.getDate() + (days > 0 ? 1 : -2));
  } else if (newDate.getDay() === 6) { // Saturday -> Friday (if going back) or Monday (if going forward)
      newDate.setDate(newDate.getDate() + (days > 0 ? 2 : -1));
  }
  
  currentDate.value = newDate;
  
  // Abort previous request and fetch new day (non-blocking)
  fetchLunches();
};

const orderLunch = async (index: number) => {
  const dateStr = currentDate.value.toISOString().split('T')[0];
  const mealKey = `order-${index}`;
  actionLoading.value[mealKey] = true;
  try {
    await api.post(`/api/lunches/order?meal_index=${index}&day=${dateStr}`, {}, {
      headers: { 'user-id': authStore.user?.id }
    });
    await fetchLunches();
  } catch (e) {
    alert(t('errors.order_failed'));
  } finally {
    actionLoading.value[mealKey] = false;
  }
};

const cancelLunch = async (index: number) => {
  const deadline = new Date(currentDate.value);
  deadline.setDate(deadline.getDate() - 1);
  deadline.setHours(14, 0, 0, 0);
  if (new Date() > deadline) {
    if (!confirm(t('dialogs.cancel_lunch_confirm'))) return;
  }
  const dateStr = currentDate.value.toISOString().split('T')[0];
  const mealKey = `cancel-${index}`;
  actionLoading.value[mealKey] = true;
  try {
    await api.post(`/api/lunches/cancel?meal_index=${index}&day=${dateStr}`, {}, {
      headers: { 'user-id': authStore.user?.id }
    });
    await fetchLunches();
  } catch (e) {
    alert(t('errors.cancel_failed'));
  } finally {
    actionLoading.value[mealKey] = false;
  }
};

const rateLunch = async (mealName: string, stars: number) => {
  actionLoading.value[mealName] = true;
  try {
    await api.post('/api/social/rate', {
      meal_identifier: mealName,
      stars: stars
    }, {
      headers: { 'user-id': authStore.user?.id }
    });
    userRatings.value[mealName] = stars;
    await fetchLunches();
  } catch (e) {
    console.error(e);
  } finally {
    actionLoading.value[mealName] = false;
  }
};

const handleFileUpload = async (event: Event, mealName: string) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const originalFile = target.files[0];
    
    actionLoading.value[mealName] = true;
    try {
      // Image compression options
      const options = {
        maxSizeMB: 1,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        fileType: 'image/jpeg'
      };

      // Compress image
      const compressedFile = await imageCompression(originalFile, options);
      
      const formData = new FormData();
      // Ensure we have a filename, browser-image-compression might return a generic 'image.jpeg' if not specified
      // But usually it keeps the name or we can provide one.
      formData.append('file', compressedFile, originalFile.name.replace(/\.[^/.]+$/, "") + ".jpg");
      formData.append('meal_identifier', mealName);
      
      await api.post('/api/social/upload', formData, {
        headers: { 
            'user-id': authStore.user?.id,
            'Content-Type': 'multipart/form-data'
        }
      });
      await fetchLunches();
    } catch (e: any) {
      if (e.response && e.response.status === 400) {
        alert(e.response.data.detail);
      } else {
        alert(t('errors.upload_failed'));
      }
      console.error(e);
    } finally {
      actionLoading.value[mealName] = false;
      // Reset the file input so the same file can be selected again
      target.value = '';
    }
  }
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

onMounted(() => {
  // Load saved theme
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    theme.change(savedTheme);
  }
  
  fetchLunches();
});
</script>

<style scoped>
.bg-black-transparent {
  background-color: rgba(0, 0, 0, 0.3);
}

.meal-image-container {
  width: 100%;
  max-width: 220px; /* Keep compact size */
  min-height: 200px;
  margin: 0 auto; /* Center on mobile */
}

@media (min-width: 960px) {
  .meal-image-container {
    max-width: 220px;
    min-height: 100%;
    margin: 0; /* Reset location for side-by-side */
  }
}

.hover-reveal {
  opacity: 0;
}

.hover-reveal:hover {
  opacity: 1;
}

.border-success-glow {
  border: 2px solid #4CAF50 !important;
  box-shadow: 0 0 15px rgba(76, 175, 80, 0.2) !important;
}

.letter-spacing-2 {
  letter-spacing: 2px !important;
}

.gap-6 {
  gap: 16px;
}

.stale-data {
  opacity: 0.6;
  transition: opacity 0.2s ease-in-out;
}
</style>
