import axios from 'axios'

const state = {
    itemLoading: false,
    load: true,
    page: 1,
    newVideos: {}
}

const getters = {
    getVideos (state){
        return state.newVideos
    }, 
    
    getItemLoading (state){
        return state.itemLoading
    },

    getLoad (state){
        return state.load
    },
    getCurrentPage(state){
        return state.page
    }
}

const mutations = {
    setVideos (state, data){
        state.newVideos = data
    },
    
    changeItemLoading (state, flag){
        state.itemLoading = flag
    },

    changeLoad (state, flag){
        state.load = flag
    },

    pageIncrement (state){
        state.page++
    }

}

const actions = {
    async getNextPage(context){
        if (context.state.load){
            if (!context.state.itemLoading){
                context.commit('changeItemLoading', true)
                try{
                    let response = await axios.get('api/videos?page=' + context.state.page)
                    if (response.data){
                        context.commit('setVideos', response.data.videos)
                    }
                    context.commit('pageIncrement')
                }catch (e) {
                    console.log(e.response)
                    context.commit('changeItemLoading', false)
                }finally{
                    context.commit('changeItemLoading', false)
                }
            }
        }
    }
}

const nextPage = {
    namespaced: true,
    state,
    getters,
    mutations,
    actions,
}

export default nextPage;