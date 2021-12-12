# [OCT Github Pages](https://uchida-labo.github.io/OCT/)  
plotly のグラフをアップロードするためだけに作りました。  
このブランチをマージしたり、ローカルからプッシュしたりしないでください。

## Description
当初は ChartStudio や Datapane のようなサービスを使えばいいだろうと思ったんですが、  
- グラフが重すぎて ChartStudio にアップロードできない
- 開発環境が32bitなので Datapane が動かない  

等の問題があったため、仕方なく GitHub Pages を使うことになりました。  
リポジトリを Public にしたのもこれが理由です。  

## Usage
以下の手順で、グラフをアップロードします。  
- plotly でグラフを描画し、HTMLファイルとして出力する。
- 出力されたHTMLファイルを[ここ](https://github.com/uchida-labo/OCT/tree/gh-pages/docs/graphs)にアップロードする。
- ブラウザで https://uchida-labo.github.io/OCT/graphs/アップロードしたグラフのファイル名.html と入力すると、グラフを閲覧できる。  

拡大・縮小などのグラフの基本操作はローカルで表示した場合と同じです。  
また、上記のURLとPowerPointのアドインを組み合わせることで、グラフをグリグリ動かせるプレゼン資料をつくることができます。
