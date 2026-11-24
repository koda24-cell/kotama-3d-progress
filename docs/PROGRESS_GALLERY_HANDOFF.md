# 3D制作進捗ギャラリー — 引継ぎ（2026-11-24）

## 保存場所
- Web: `koda24-cell/kotama-3d-progress` の `main/index.html`
- データ: 同リポジトリ `3d-progress-data` の `index.json` と `renders/`
- 元3D制作・Blender・GLB: `koda24-cell/kotama-no-bouken`（ギャラリー用の画像保存はしない）

## 初回移行の検証済み結果
- 元ゲームリポジトリ `3d-progress-data` から、14モデル・56枚をコピー。
- PNG 56枚の全SHA256照合とパス検査に合格。
- ClamAV 1.5.4で56ファイル検査、感染0。
- 新リポジトリ `3d-progress-data` へのpush成功、git treeのPNG56件を確認。
- 実Chromiumのギャラリー表示・更新・設計図モック・拡大テスト成功。
- Runs: [移行](https://github.com/koda24-cell/kotama-3d-progress/actions/runs/45317731572) / [ブラウザ](https://github.com/koda24-cell/kotama-3d-progress/actions/runs/45317821492) / [登録テスト](https://github.com/koda24-cell/kotama-3d-progress/actions/runs/45317840815)。
- *初回移行分には既存の設計図画像はまだ含まれない。設計図表示機能を実装しただけで、既存設計図の全取得は未完了。*

## マニフェスト（例）
```json
{
 "id":"b2-waterwheel-beam",
 "name":"水車の下部横梁",
 "floor":"第2層",
 "version":"V03",
 "status":"制作中",
 "kind":"render",
 "publication_cleared":true,
 "run_id":1234567,
 "source_sha":"0123456789012345678901234567890123456789",
 "updated_at":"2026-11-24T01:00:00Z",
 "images":[{"view":"正面","file":"front.png"},{"view":"側面","file":"side.png"}]
}
```
`kind=design` も同じIDで登録でき、設計版とレンダリング版は独立更新。設計中モデルは `status=設計中`。登録後は `python3 -m unittest discover -s tools/3d-progress -v` と実ブラウザ確認を実施。

## 追加予定・境界
- 全階層・天井・床・小物・設計図の既存Artifactsからの安全な追加取り込み。
- 元ゲームRepoのBlender Actionsから新サイトRepoへのデータ登録経路を確立。呼び出し元 `GITHUB_TOKEN` は通常別Repoへの書込み権限を持たないため、安易な直接pushは避ける。**新リポジトリ側のActionsで読み取って登録**するか、明示的に安全な認証方法を選ぶ。
- ユーザーの「更新」ボタンは現在台帳の最新を再読み込みする。未取得Artifactsの取り込みJob自体をブラウザから起動するわけではない。
- 元ゲームRepoの別作業用Actions/モデル/GLB/正式素材を消さない。削除対象は進捗サイト専用の旧ブランチと未マージPR。
