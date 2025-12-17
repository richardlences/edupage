<template>
  <v-app class="bg-grey-lighten-5">
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
            EduLunch
          </v-toolbar-title>
          <span class="text-caption text-white font-weight-medium" style="opacity: 0.9;">Premium School Dining</span>
        </div>
        
        <v-spacer></v-spacer>
        
        <div class="d-flex align-center">
          <span class="text-body-2 mr-4 text-white font-weight-medium hidden-sm-and-down">
            Hello, {{ authStore.user?.username }}
          </span>
          <v-btn 
            variant="flat" 
            color="white" 
            size="small" 
            class="text-deep-orange font-weight-bold"
            prepend-icon="mdi-logout"
            @click="handleLogout"
          >
            Logout
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container class="py-8" style="max-width: 1000px;">
        
        <!-- Date Navigation - Floating Card Style -->
        <v-card class="mb-8 rounded-xl mx-auto" elevation="4" max-width="600" border>
          <div class="d-flex justify-space-between align-center pa-2">
            <v-btn icon="mdi-chevron-left" variant="text" size="large" color="deep-orange" @click="changeDay(-1)"></v-btn>
            
            <div class="text-center py-2">
              <div class="text-h5 font-weight-black text-grey-darken-3">{{ formattedDate }}</div>
              <div class="text-subtitle-1 text-uppercase text-deep-orange font-weight-bold letter-spacing-2">{{ dayName }}</div>
            </div>
            
            <v-btn icon="mdi-chevron-right" variant="text" size="large" color="deep-orange" @click="changeDay(1)"></v-btn>
          </div>
        </v-card>

        <!-- Ordered Meal Summary -->
        <v-card
          v-if="orderedLunch"
          class="mb-6 rounded-xl border-success-glow"
          elevation="4"
          color="green-lighten-5"
        >
          <div class="d-flex align-center justify-space-between pa-4">
            <div class="d-flex align-center">
              <v-avatar color="success" size="40" class="mr-4 elevation-2">
                <v-icon color="white">mdi-check</v-icon>
              </v-avatar>
              <div>
                <div class="text-caption text-green-darken-3 font-weight-bold mb-0">YOU HAVE ORDERED</div>
                <div class="text-subtitle-1 font-weight-black text-grey-darken-3" style="line-height: 1.2;">
                  {{ orderedLunch.name }}
                </div>
              </div>
            </div>
            
            <v-btn
              v-if="canModifyLunch(orderedLunch)"
              color="error"
              variant="text"
              class="font-weight-bold"
              prepend-icon="mdi-close-circle"
              @click="cancelLunch(orderedLunch.index)"
            >
              Cancel
            </v-btn>
            <v-chip
              v-else
              color="success"
              variant="tonal"
              class="font-weight-bold"
              prepend-icon="mdi-check-circle"
            >
              Confirmed
            </v-chip>
          </div>
        </v-card>

        <!-- Loading State -->
        <div v-if="loading" class="d-flex flex-column align-center justify-center py-16">
          <v-progress-circular indeterminate color="deep-orange" size="64" width="6"></v-progress-circular>
          <div class="mt-4 text-h6 text-grey-darken-1 font-weight-light">Preparing menu...</div>
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
          <v-avatar color="grey-lighten-4" size="120" class="mb-6">
            <v-icon size="64" color="grey-lighten-1">mdi-silverware-clean</v-icon>
          </v-avatar>
          <div class="text-h5 text-grey-darken-2 font-weight-bold">No Service Today</div>
          <div class="text-body-1 text-grey-darken-1 mt-2">The kitchen is closed for this date.</div>
        </div>

        <!-- Lunches List -->
        <div v-else class="d-flex flex-column gap-6">
          
          <!-- Soup Section -->
          <v-card 
            v-if="soup" 
            class="rounded-xl overflow-hidden mb-6" 
            elevation="3"
            border
          >
            <div class="d-flex flex-column flex-md-row">
              <!-- Soup Image Area -->
              <div class="position-relative bg-grey-lighten-4 d-flex align-center justify-center" style="width: 100%; max-width: 300px; min-height: 220px;">
                
                <!-- Image Carousel -->
                <v-carousel
                  v-if="soup.photos && soup.photos.length > 0"
                  height="100%"
                  hide-delimiter-background
                  show-arrows="hover"
                  cycle
                  interval="5000"
                >
                  <v-carousel-item
                    v-for="(photo, i) in soup.photos"
                    :key="i"
                    :src="photo"
                    cover
                    @click="openLightbox(soup.photos, i)"
                    style="cursor: zoom-in;"
                  ></v-carousel-item>
                </v-carousel>

                <!-- No Image Placeholder (Clickable if can rate) -->
                <div 
                  v-else 
                  class="d-flex flex-column align-center justify-center h-100 w-100 text-grey-lighten-1 transition-swing"
                  :class="{'cursor-pointer hover-bg-grey-lighten-3': canRateMeal(soup)}"
                  @click="canRateMeal(soup) ? triggerFileInput('soup') : null"
                >
                  <v-icon size="48" class="mb-2" :color="canRateMeal(soup) ? 'deep-orange-lighten-2' : 'grey-lighten-1'">
                    {{ canRateMeal(soup) ? 'mdi-camera-plus' : 'mdi-soup' }}
                  </v-icon>
                  <span class="text-caption font-weight-bold text-uppercase">
                    {{ canRateMeal(soup) ? 'Add Photo' : 'Soup of the Day' }}
                  </span>
                </div>

                <!-- Photo Management Button (Top Right) -->
                <div 
                  v-if="canRateMeal(soup)"
                  class="position-absolute"
                  style="top: 12px; right: 12px; z-index: 5;"
                >
                  <!-- If user has photo: Menu with Change/Remove -->
                  <v-menu v-if="soup.user_has_photo" location="bottom end">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        v-bind="props"
                        icon
                        size="small"
                        color="white"
                        class="text-deep-orange"
                        elevation="2"
                      >
                        <v-icon>mdi-camera-cog</v-icon>
                      </v-btn>
                    </template>
                    <v-list density="compact" elevation="3" class="rounded-lg">
                      <v-list-item @click="triggerFileInput('soup')" prepend-icon="mdi-upload" class="text-body-2">
                        <v-list-item-title>Change Photo</v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="deletePhoto(soup.name)" prepend-icon="mdi-delete" class="text-error text-body-2">
                        <v-list-item-title>Remove Photo</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>

                  <!-- If user has NO photo but photos exist (limit check): Simple Add Button -->
                  <!-- If photos exist, we show a small button. If no photos, the big placeholder handles it. -->
                  <v-btn
                    v-else-if="soup.photos && soup.photos.length > 0 && soup.photos.length < 5"
                    icon
                    size="small"
                    color="white"
                    class="text-deep-orange"
                    elevation="2"
                    @click="triggerFileInput('soup')"
                  >
                    <v-icon>mdi-camera-plus</v-icon>
                    <v-tooltip activator="parent" location="bottom">Add Photo</v-tooltip>
                  </v-btn>

                  <!-- Hidden Input -->
                  <input 
                    type="file" 
                    :ref="(el) => setFileInputRef(el, 'soup')"
                    class="d-none" 
                    @change="(e) => handleFileUpload(e, soup.name)"
                    accept="image/*"
                  >
                </div>
              </div>

              <!-- Soup Content -->
              <div class="flex-grow-1 pa-5 d-flex flex-column justify-space-between bg-orange-lighten-5">
                <div>
                  <div class="d-flex justify-space-between align-start mb-3">
                    <v-chip color="deep-orange" variant="flat" size="small" class="font-weight-bold text-uppercase px-3">
                      Included
                    </v-chip>
                    <div class="d-flex align-center">
                      <v-icon color="amber-darken-2" size="small" class="mr-1">mdi-star</v-icon>
                      <span class="text-h6 font-weight-bold text-grey-darken-3">{{ soup.avg_rating || '--' }}</span>
                      <span class="text-caption text-grey-darken-1 ml-1 font-weight-medium" v-if="soup.avg_rating">/ 5</span>
                    </div>
                  </div>
                  <div class="text-h5 font-weight-bold text-grey-darken-3 mb-2" style="line-height: 1.2;">
                    {{ soup.name }}
                  </div>
                </div>

                <div class="d-flex align-center justify-space-between mt-4 pt-4 border-t border-orange-lighten-4">
                  <div class="d-flex flex-column" v-if="canRateMeal(soup)">
                    <span class="text-caption text-grey-darken-1 font-weight-medium mb-1">YOUR RATING</span>
                    <v-rating
                      v-model="userRatings[soup.name]"
                      color="amber-darken-2"
                      active-color="amber-darken-2"
                      density="compact"
                      hover
                      half-increments
                      @update:modelValue="(val) => rateLunch(soup.name, Number(val))"
                      size="small"
                    ></v-rating>
                  </div>
                  <div v-else></div> <!-- Spacer -->
                  <v-icon color="orange-lighten-3" size="40">mdi-spoon-sugar</v-icon>
                </div>
              </div>
            </div>
          </v-card>

          <!-- Main Meals Grid -->
          <v-row>
            <v-col cols="12" v-for="lunch in mainMeals" :key="lunch.index">
              <v-card 
                class="rounded-xl overflow-hidden transition-swing" 
                :elevation="lunch.is_ordered ? 8 : 2"
                :class="{'border-success-glow': lunch.is_ordered}"
                border
              >
                <div class="d-flex flex-column flex-md-row">
                  
                  <!-- Meal Image Area -->
                  <div class="position-relative bg-grey-lighten-4 d-flex align-center justify-center" style="width: 100%; max-width: 300px; min-height: 220px;">
                    
                    <!-- Ordered Badge -->
                    <div v-if="lunch.is_ordered" class="position-absolute z-index-10" style="top: 12px; left: 12px;">
                      <v-chip color="success" variant="flat" class="font-weight-bold elevation-2" prepend-icon="mdi-check-circle">
                        ORDERED
                      </v-chip>
                    </div>

                    <!-- Image Carousel -->
                    <v-carousel
                      v-if="lunch.photos && lunch.photos.length > 0"
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
                        @click="openLightbox(lunch.photos, i)"
                        style="cursor: zoom-in;"
                      ></v-carousel-item>
                    </v-carousel>
                    
                    <!-- No Image Placeholder (Clickable if can rate) -->
                    <div 
                      v-else 
                      class="d-flex flex-column align-center justify-center h-100 w-100 text-grey-lighten-1 transition-swing"
                      :class="{'cursor-pointer hover-bg-grey-lighten-3': canRateMeal(lunch)}"
                      @click="canRateMeal(lunch) ? triggerFileInput(lunch.index) : null"
                    >
                      <v-icon size="48" class="mb-2" :color="canRateMeal(lunch) ? 'deep-orange-lighten-2' : 'grey-lighten-1'">
                        {{ canRateMeal(lunch) ? 'mdi-camera-plus' : 'mdi-food-off' }}
                      </v-icon>
                      <span class="text-caption font-weight-bold text-uppercase">
                        {{ canRateMeal(lunch) ? 'Add Photo' : 'No Photo' }}
                      </span>
                    </div>

                    <!-- Photo Management Button (Top Right) -->
                    <div 
                      v-if="canRateMeal(lunch)"
                      class="position-absolute"
                      style="top: 12px; right: 12px; z-index: 5;"
                    >
                      <!-- If user has photo: Menu with Change/Remove -->
                      <v-menu v-if="lunch.user_has_photo" location="bottom end">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            v-bind="props"
                            icon
                            size="small"
                            color="white"
                            class="text-deep-orange"
                            elevation="2"
                          >
                            <v-icon>mdi-camera-cog</v-icon>
                          </v-btn>
                        </template>
                        <v-list density="compact" elevation="3" class="rounded-lg">
                          <v-list-item @click="triggerFileInput(lunch.index)" prepend-icon="mdi-upload" class="text-body-2">
                            <v-list-item-title>Change Photo</v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="deletePhoto(lunch.name)" prepend-icon="mdi-delete" class="text-error text-body-2">
                            <v-list-item-title>Remove Photo</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>

                      <!-- If user has NO photo but photos exist (limit check): Simple Add Button -->
                      <v-btn
                        v-else-if="lunch.photos && lunch.photos.length > 0 && lunch.photos.length < 5"
                        icon
                        size="small"
                        color="white"
                        class="text-deep-orange"
                        elevation="2"
                        @click="triggerFileInput(lunch.index)"
                      >
                        <v-icon>mdi-camera-plus</v-icon>
                        <v-tooltip activator="parent" location="bottom">Add Photo</v-tooltip>
                      </v-btn>

                      <!-- Hidden Input -->
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
                    class="flex-grow-1 pa-5 d-flex flex-column justify-space-between"
                    :class="lunch.is_ordered ? 'bg-green-lighten-5' : 'bg-white'"
                  >
                    <div>
                      <div class="d-flex justify-space-between align-start mb-3">
                        <v-avatar 
                          :color="lunch.is_ordered ? 'success' : 'grey-lighten-3'" 
                          size="36" 
                          class="elevation-1"
                        >
                          <span 
                            class="font-weight-black text-body-1"
                            :class="lunch.is_ordered ? 'text-white' : 'text-grey-darken-2'"
                          >
                            {{ lunch.number || lunch.index }}
                          </span>
                        </v-avatar>
                        
                        <div class="d-flex align-center">
                          <v-icon color="amber-darken-2" size="small" class="mr-1">mdi-star</v-icon>
                          <span class="text-h6 font-weight-bold text-grey-darken-3">{{ lunch.avg_rating || '--' }}</span>
                          <span class="text-caption text-grey-darken-1 ml-1 font-weight-medium" v-if="lunch.avg_rating">/ 5</span>
                        </div>
                      </div>
                      
                      <div class="text-h5 font-weight-bold text-grey-darken-3 mb-2" style="line-height: 1.2;">
                        {{ lunch.name }}
                      </div>
                    </div>

                    <div class="d-flex align-center justify-space-between mt-4 pt-4 border-t" :class="lunch.is_ordered ? 'border-green-lighten-4' : 'border-grey-lighten-4'">
                      
                      <!-- Rating Area (Only show if user can rate) -->
                      <div class="d-flex flex-column" v-if="canRateMeal(lunch)">
                        <span class="text-caption font-weight-medium mb-1" :class="lunch.is_ordered ? 'text-green-darken-2' : 'text-grey-darken-1'">
                          RATE THIS MEAL
                        </span>
                        <v-rating
                          v-model="userRatings[lunch.name]"
                          color="amber-darken-2"
                          active-color="amber-darken-2"
                          density="compact"
                          hover
                          half-increments
                          @update:modelValue="(val) => rateLunch(lunch.name, Number(val))"
                          size="small"
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
                          @click="cancelLunch(lunch.index)"
                          class="text-capitalize font-weight-bold"
                        >
                          Cancel Order
                        </v-btn>
                        
                        <!-- Order Button -->
                        <v-btn
                          v-else
                          color="deep-orange"
                          variant="flat"
                          elevation="2"
                          prepend-icon="mdi-silverware-fork-knife"
                          @click="orderLunch(lunch.index)"
                          class="text-capitalize font-weight-bold px-6"
                        >
                          Order Meal
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </div>
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

const authStore = useAuthStore();
const router = useRouter();

const currentDate = ref(new Date());
const lunches = ref<any[]>([]);
const loading = ref(false);
const error = ref('');
const userRatings = ref<Record<string, number>>({});
const fileInputRefs = ref<Record<string, HTMLInputElement>>({});
const lightboxOpen = ref(false);
const lightboxPhotos = ref<string[]>([]);
const lightboxIndex = ref(0);

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
  if (!confirm('Are you sure you want to remove your photo?')) return;
  
  try {
    await api.post('/api/social/delete_photo', {
      meal_identifier: mealName
    }, {
      headers: { 'user-id': authStore.user?.id }
    });
    fetchLunches();
  } catch (e) {
    alert('Failed to delete photo.');
    console.error(e);
  }
};

const formattedDate = computed(() => {
  return currentDate.value.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
});

const orderedLunch = computed(() => {
    if (!lunches.value || lunches.value.length === 0) return null;
    // Find the ordered meal in the main meals (index > 0)
    return lunches.value.slice(1).find(l => l.is_ordered);
});

const dayName = computed(() => {
  return currentDate.value.toLocaleDateString('en-US', { weekday: 'long' });
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
    return ((lunchDate === today && new Date().getHours() >= 11) || (lunchDate < today)) && lunch.is_ordered;
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
            return "Too late to change order";
        } else {
            return "Ordering closed";
        }
    }
    return null;
};

const fetchLunches = async () => {
  loading.value = true;
  error.value = '';
  const dateStr = currentDate.value.toISOString().split('T')[0];
  try {
    const response = await api.get(`/api/lunches/?day=${dateStr}`, {
      headers: { 'user-id': authStore.user?.id }
    });
    lunches.value = response.data;
  } catch (e) {
    console.error(e);
    error.value = 'Failed to load lunches.';
  } finally {
    loading.value = false;
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
  fetchLunches();
};

const orderLunch = async (index: number) => {
  const dateStr = currentDate.value.toISOString().split('T')[0];
  try {
    await api.post(`/api/lunches/order?meal_index=${index}&day=${dateStr}`, {}, {
      headers: { 'user-id': authStore.user?.id }
    });
    await fetchLunches();
  } catch (e) {
    alert('Failed to order lunch.');
  }
};

const cancelLunch = async (index: number) => {
  const deadline = new Date(currentDate.value);
  deadline.setDate(deadline.getDate() - 1);
  deadline.setHours(14, 0, 0, 0);
  if (new Date() > deadline) {
    if (!confirm("Are you sure you want to cancel your lunch? You can't reorder if you cancel now.")) return;
  }
  const dateStr = currentDate.value.toISOString().split('T')[0];
  try {
    await api.post(`/api/lunches/cancel?meal_index=${index}&day=${dateStr}`, {}, {
      headers: { 'user-id': authStore.user?.id }
    });
    await fetchLunches();
  } catch (e) {
    alert('Failed to cancel lunch.');
  }
};

const rateLunch = async (mealName: string, stars: number) => {
  try {
    await api.post('/api/social/rate', {
      meal_identifier: mealName,
      stars: stars
    }, {
      headers: { 'user-id': authStore.user?.id }
    });
    userRatings.value[mealName] = stars;
    fetchLunches();
  } catch (e) {
    console.error(e);
  }
};

const handleFileUpload = async (event: Event, mealName: string) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const formData = new FormData();
    formData.append('file', target.files[0]);
    formData.append('meal_identifier', mealName);
    
    try {
      await api.post('/api/social/upload', formData, {
        headers: { 
            'user-id': authStore.user?.id,
            'Content-Type': 'multipart/form-data'
        }
      });
      fetchLunches();
    } catch (e: any) {
      if (e.response && e.response.status === 400) {
        alert(e.response.data.detail);
      } else {
        alert('Failed to upload photo.');
      }
      console.error(e);
    }
  }
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

onMounted(() => {
  fetchLunches();
});
</script>

<style scoped>
.bg-black-transparent {
  background-color: rgba(0, 0, 0, 0.3);
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
  gap: 24px;
}
</style>
