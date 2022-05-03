/**
 * First we will load all of this project's JavaScript dependencies which
 * includes Vue and other libraries. It is a great starting point when
 * building robust, powerful web applications using Vue and Laravel.
 */
import BootstrapVue from 'bootstrap-vue'

//require('./bootstrap');

window.Vue = require('vue').default;
Vue.use(BootstrapVue);

import store from './store/index'

/**
 * The following block of code may be used to automatically register your
 * Vue components. It will recursively scan this directory for the Vue
 * components and automatically register them with their "basename".
 *
 * Eg. ./components/ExampleComponent.vue -> <example-component></example-component>
 */

// const files = require.context('./', true, /\.vue$/i)
// files.keys().map(key => Vue.component(key.split('/').pop().split('.')[0], files(key).default))
Vue.component('video-table-component', require('./components/VideoTableComponent.vue').default);

Vue.component('next-page-component', require('./components/NextPageComponent.vue').default);

Vue.component('menubar-component', require('./components/MenubarComponent.vue').default);

/**
 * Next, we will create a fresh Vue application instance and attach it to
 * the page. Then, you may begin adding components to this application
 * or customize the JavaScript scaffolding to fit your unique needs.
 */
const video = new Vue({
    el: '#video-table',
    data: {
    },
    store: store
});

const next_page_button = new Vue({
    el: '#next-page-button',
    data: {
    },
    store: store
});

const menubar = new Vue({
    el: '#menubar',
    data: {
    },
    store: store
});

