import Vue from 'vue'
import Vuex from 'vuex'
import nextPage from './nextPage'

Vue.use(Vuex)

export default new Vuex.Store({
    modules: {
        nextPage
    }
})

