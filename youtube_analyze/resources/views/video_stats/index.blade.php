<!--resorceファイル内のvue.jsを反映させるときはnpm run dev をcmdで行う
v-bind で渡す際はケバブケース(aaa-bbb)
vue側で受け取る場合はキャメルケースで指定する(aaaBbb)
参考元: https://tech.manafukurou.com/article/laravel8-vue-param/
table header固定の参考元: https://lv1meg.hatenablog.com/entry/2020/05/03/080558
-->

@extends('layouts/template')
@section('head')
    @component('layouts/head')
    @endcomponent
@endsection
@section('content')
    <div class="container">
        <div class="row">
            <div class="col-md-12" id="menubar">
                <menubar-component></menubar-component>
            </div>

            <div class="col-md-12" id="video-table">
                <video-table-component :order="{{json_encode($order)}}" :videos="{{json_encode($videos)}}"></video-table-component>
            </div>

            <div class="col-md-2 offset-5 mb-4" id="next-page-button">
                <next-page-component><next-page-component>
            </div>
        </div>

    </div>
@endsection


