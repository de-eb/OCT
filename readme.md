# OCT
OCT（Optical Coherence Tomography：光干渉断層撮影）の実験に使用するソースコードをまとめました。

## Description
ソースコード（以後スクリプトといいます）は全てPythonで記述しているので、使用するにはPythonをそこそこ理解する必要があります。  
リポジトリの構成は以下のようになっています。
- **OCT（いちばん上）**  
主に自作モジュールを呼び出すスクリプトを置くフォルダです。Pythonの実行ディレクトリにもなるので、ファイルなどの相対パスはここが基準になります。
    - **modules**  
    実験機器の制御や信号処理などに使用する自作モジュールを置くフォルダです。
        - **tools**  
        自作モジュールで使用するDLLファイルなどを置くフォルダです。
    - **data**  
    測定データなどの一時保存先として使用するフォルダです。.gitignoreに記載しているので同期されません。

## Requirement
**32bit版**の Python 3.7 以上が必要です。  
依存パッケージは requirements.txt に記載しています。  

※ Visual Studio Code を開発環境とすることを推奨します。また Windows10 以外のOSでの動作は保証しません。

## Usage
各スクリプトのコメントに使い方を記載しています。

## Install
予め Visual Studio Code、Python、Git をインストールし、初期設定を済ませてください。  
任意のフォルダで下記のコマンドを実行することで、このリポジトリをコピーできます。
```
$ git clone https://github.com/uchida-labo/OCT.git
```
その後、ルートディレクトリで下記コマンドを実行すると、依存パッケージを一括インストールできます。
```
$ pip install -r requirements.txt
```

## Licence
このリポジトリは外部に公開・譲渡しないでください。

## Author

[de-eb](https://github.com/de-eb)