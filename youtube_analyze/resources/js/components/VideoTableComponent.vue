<template>
    <table class="table table-striped table-hover">
        <thead >
            <tr>
                <th class="fw-bold text-nowrap rank">順位</th>
                <th v-if="order=='published_date'" class="published_date text-nowrap">投稿日時 </th>
                <th v-else class="view-count text-nowrap">再生回数</th>
                <th class="thumbnail"></th>
                <th class="title">動画タイトル</th>
                <th class="text-nowrap ch_name">チャンネル名</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(video, i) in topVideos" :key="video.view_count">
                <td class="fw-bold rank">{{i + 1}}</td>
                <td class="view-count text-nowrap">{{video.view_count}}回</td>
                <td class="thumbnail">
                    <div><img :src="video.thumbnail_url"></div>
                </td>
                <td><div class="title-box">{{video.title}}</div></td>
                <td class="text-nowrap ch_name">{{video.ch_name}}</td>
            </tr>
        </tbody>
    </table>
</template>

<script>
    export default {
        data(){
            return{
            topVideos: this.videos,
            }
        },

        props: {
            videos:{},
            order:{
                type: String,
                required: true
            }
        },

        computed: {
            newVideos: function(){
                return this.$store.getters['nextPage/getVideos']
            }
        },

        watch: {
            newVideos(nVideos) {
                console.log(nVideos)
                if(nVideos){
                    nVideos.forEach(video => {
                        this.topVideos.push(video)
                    });
                }
            }
        }
    }
</script>

<style scoped>
table {
    height: 100px;
    margin-top: 100px;
}

th {
    position: sticky;
    top: 55px;
    z-index: 1;
    background: #f5f5f5;
}


.thumbnail img {
    width: 160px;
    height: 90px;
}
</style>