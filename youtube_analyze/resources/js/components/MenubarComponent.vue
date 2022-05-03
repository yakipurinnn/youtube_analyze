<template>
    <header>
        <nav class="navbar fixed-top navbar-expand-md navbar-dark bg-dark">
            <div class="containar-fluid">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/analyze?order=view_count">総再生回数</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link">直近再生数</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analyze?order=published_date">新着順</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analyze?order=published_date_asc">投稿順</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analyze?order=like_count">高評価数</a>
                    </li>
                </ul>
            </div>
        </nav>
    </header>
</template>

<script>
export default{
    data: ()=>({
    }), 
}
</script>

<style scoped>
li:first-of-type{
    padding-left: 6rem;
}
</style>