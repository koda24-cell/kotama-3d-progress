# 制作Artifacts自動収集・台帳仕様

## 受け渡し契約
元リポジトリ `koda24-cell/kotama-no-bouken` の成功したActions runが、Artifact内にモデル単位の `manifest.json` とPNGを含める。マニフェスト例:

```json
{
  "id": "b2-waterwheel-beam",
  "name": "水車の下部横梁",
  "floor": "第2層",
  "version": "V03",
  "status": "制作中",
  "kind": "progress",
  "approval_state": "NOT_APPROVED",
  "publication_cleared": true,
  "run_id": 1234567,
  "source_sha": "0123456789012345678901234567890123456789",
  "updated_at": "2026-11-24T01:00:00Z",
  "images": [
    {"view": "正面", "file": "front.png"},
    {"view": "側面", "file": "side.png"}
  ]
}
```

- `kind`: `design`（設計図）/ `progress`（途中画像）/ `render`（完成レンダリング）
- `approval_state`: `NOT_APPROVED` または `APPROVED`。未指定は未承認。
- `publication_cleared`: 公開用リポジトリへの掲載許可。ゲームへの正式採用承認とは別。
- `id`: 同一部品の改版では固定。別部品と組立品は別ID。
- `version`: 種類ごとの版を記録。run ID、commit SHA、UTC日時は必須。
- PNGはmanifestの相対パスだけを許可し、PNG signature / IHDR / dimensions / CRC / IEND / SHA256を検証。

## 収集処理
`.github/workflows/collect-kotama-artifacts.yml` は毎時および手動で実行する。source repoの成功runを最大30件調べ、Artifactsを取得しClamAVでスキャンしてからマニフェストを検証する。既存の画像はSHA256アドレスで重複排除し、同じkindの新しいUTC timestampのみ最新版に反映する。古いrunや壊れたPNGは台帳を更新しない。

## 認証セットアップ（必要）
このリポジトリのSettings → Secrets and variables → Actionsに `SOURCE_REPO_READ_TOKEN` を登録する。対象は `koda24-cell/kotama-no-bouken` のActions Artifactsを読み取れる最小権限のFine-grained token。トークン未設定時は安全に失敗し、データを変更しない。秘密情報をmanifestやArtifactsへ含めない。

## 履歴・承認
- 各種類の最新版を `designs` / `progress_images` / `images` に別々に保持。
- 更新前の版、run、commit、画像参照、承認状態を `history[]` に追記。
- `APPROVED` はmanifestに明示されたものだけ。公開許可 `publication_cleared` とゲーム正式採用承認は独立。
- 登録時に未承認へ自動昇格させない。公開台帳に表示することとゲームに採用することを混同しない。

## 現在の境界
自動収集側はArtifact内にこのmanifest契約があることを前提とする。既存の過去Artifactsにmanifestがない場合、ファイル名からIDや承認状態を推測して登録しない。元リポジトリの制作Actionsへmanifest出力を組み込む作業と、上記secret設定は別途必要。これらが完了するまでは自動収集が全制作runを網羅したとは扱わない。
