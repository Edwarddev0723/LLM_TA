import { createApp } from 'vue';
import { createPinia } from 'pinia';
import PrimeVue from 'primevue/config';
import 'primeicons/primeicons.css';
import './style.css';

import App from './App.vue';
import router from './router';
import { useSessionStore } from './stores/session';

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(PrimeVue);

const sessionStore = useSessionStore();
sessionStore.initialize();

app.mount('#app');


