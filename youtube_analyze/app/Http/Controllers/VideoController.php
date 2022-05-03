<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\support\Facades\Log;
use App\Http\Controllers\Controller;
use App\Models\VideoStats;
use App\Models\ViewCount;
use Dflydev\DotAccessData\Data;
use Psy\CodeCleaner\EmptyArrayDimFetchPass;

class VideoController extends Controller
{
    public function index(Request $request)
    {
        $order = $request->order;
        if (empty($order)){
            $order = 'view_count';
        };

        if ($order == 'published_date_asc'){
            $videos = VideoStats::orderBy('published_date', 'ASC')->take(50)->get();
        }else{
            $videos = VideoStats::orderBy($order, 'DESC')->take(50)->get();
        }

        $view_stats = ViewCount::take(100)->get();

        Log::debug(print_r($order, true));    //print_rの引数をtrueとすると表示するのではなく戻り値を返す

        return view('video_stats/index', compact('order', 'videos', 'view_stats'));
    }

    public function nextPage(Request $request)
    {
        $page_number = $request->input('page');
        $videos = VideoStats::orderBy('view_count', 'DESC')->skip(50*$page_number)->take(50)->get();

        return compact('videos');
    }
    
    public function store(Request $request)
    {//次へ表示ボタンを押すと50動画ずつ読み込まれる
        $video_count = 50;
        $video_count += $request->video_count;

        Log::debug(print_r($video_count, true));

        $videos = VideoStats::orderBy('view_count', 'DESC')->take($video_count)->get();
        return view('video_stats/index', compact('videos'));
    }
}
