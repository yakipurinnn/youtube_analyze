<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class VideoStats extends Model
{
    use HasFactory;
    protected $table = 'video_stats';
    protected $primarykey = 'video_id';
}
