<template>
    <form>
        <button type="button" class="btn btn-info" @click="getNextPage()">次の動画を表示</button>
    </form>
</template>

<script>
export default{
    data: ()=>({
    }),
    methods: {
        getNextPage(){
            console.log(this.$store.state.nextPage.load)    //stateの後に名前空間を挟む
            this.$store.dispatch('nextPage/getNextPage')    //moduleでdispatchを使う場合はmodule名/action名
        }
    }
}
</script>
