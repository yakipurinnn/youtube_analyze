<!--resorceファイル内のvue.jsを反映させるときはnpm run dev をcmdで行う-->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>holo_analyze</title>
    <script src="{{ asset('js\app.js')}}" defer></script>
    <link href="{{ asset('css\app.css') }}" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <link rel="stylesheet" href="{{ asset('css\video_stats\index.css') }}">

</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col-md-12" id="app">
                <table height="100" class="table table-striped table-primary">
                    <tr>
                        <th class="fw-bold rank">順位</th>
                        <th class="view-count">再生回数</th>
                        <th class="thumbnail"></th>
                        <th class="title">動画タイトル</th>
                        <th class="text-nowrap ch_name">チャンネル名</th>
                    </tr>
                    @foreach($videos as $index=>$video)
                    <tr>
                        <td class="fw-bold rank">{{$index + 1}}</td>
                        <td class="view-count">{{$video->view_count}}回</td>
                        <td class="thumbnail">
                            <div><img width="160" height="90" src="{{$video->thumbnail_url}}"></div>
                        </td>
                        <td><div class="title-box">{{$video->title}}</div></td>
                        <td class="text-nowrap ch_name">{{$video->ch_name}}</td>
                    </tr>
                    @endforeach
                </table>
            </div>

            <div class="col-md-2 offset-5 mb-4">
                <form action="/analyze" method="post">
                    <input type="hidden" name="_token" value="{{csrf_token()}}">
                    <input type="hidden" name="video_count" value="{{count($videos)}}">
                    <button type="submit" class="btn btn-info">次の動画を表示</button>
                </form>
            </div>
        </div>

    </div>
</body>
</html>


