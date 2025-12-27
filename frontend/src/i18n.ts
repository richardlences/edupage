import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import sk from './locales/sk.json'

const i18n = createI18n({
    legacy: false, // Usage with Composition API
    locale: localStorage.getItem('locale') || 'en', // set locale from local storage or default to en
    fallbackLocale: 'en', // set fallback locale
    messages: {
        en,
        sk
    }
})

export default i18n
