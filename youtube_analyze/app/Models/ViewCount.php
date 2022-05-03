<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;



class ViewCount extends Model
{
    use HasFactory;
    protected $table;

    public function __construct(array $attributes=[])    //テーブルに動的な名前を用いる場合はコンストラクタを用いる
    {
        $now_dt = date('Ym');

        parent::__construct($attributes);
        $this->table = $now_dt.'_views';
    }
}
