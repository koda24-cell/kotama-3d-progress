# コタマ 3D制作進捗ギャラリー

ブラウザRPG『コタマのぼうけん』の**制作進捗を閲覧する独立リポジトリ**です。

- ギャラリー: [index.html](index.html) （GitHub Pages / raw.githack等で公開）
- 画像台帳と実レンダリング: `3d-progress-data` ブランチの `index.json` と `renders/`
- 登録ツール: `tools/3d-progress/register.py`、`backfill.py`
- レンダリングは制作中・未承認・未マージを含め**閲覧用**。ゲーム採用承認ではありません
- 画像は検査・公開許可を確認したものだけ登録。元モデルの変更やゲーム本体への自動組み込みはしません
- 制作元Actions: [kotama-no-bouken](https://github.com/koda24-cell/kotama-no-bouken/actions)

## 移行

旧リポジトリの `3d-progress-data` の画像56枚・14モデルを、ハッシュ／形式／ウイルス検査して新リポジトリ同名ブランチにコピーするActionsを用意しています。移行先の台帳／PNGの実在を確認してから旧データを整理します。

## モデル登録と設計図

各モデルに安定したIDを割り当て、レンダリング `kind=render` と設計図 `kind=design` を独立管理します。小型部品、壁、天井、床、装備、植物も表示対象。設計図の存在しないモデルは「未取得」と表示します。

## チェック

```sh
python3 -m unittest discover -s tools/3d-progress -v
```
