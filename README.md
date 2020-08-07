# 文字起こし

Google Cloud Speech-to-Textを利用して音声ファイルから文字起こしして、ローカルにテキストファイルを保存します

## Features

* GCSのアップロード
  * 入力ファイル: mp4, m4a, mp3, wav
* Speech-to-Textが読みやすいようにFLACファイルへの変換

## Requirement

* docker

## Installation

```bash
docker-compose build
```

## Initialize

* GCP サービスアカウントのJSONファイルをカレントフォルダに設置してください
  ```bash
  $ service-account.json
  ```

* 設定の定義を更新してください
  ```bash
  $ vim routes.py
  ```
* 設定の記述
  * GCSのバケット名
  * 音声適正ブースト(https://cloud.google.com/speech-to-text/docs/boost?hl=ja)
  ```bash
  GCS_BUCKET_NAME = 'example-bucket'
  SELECTED_PHRASES = [{"phrases": ["例"], "boost": 20}]
  ```

## Usage

```bash
docker-compose up -d
```
* data/input_fileフォルダに文字起こししたい動画・音声を設置してください。
* ブラウザで http://localhost:5000 にアクセス

## Author

* acronhub(https://github.com/acronhub)

## License

[MIT license](https://en.wikipedia.org/wiki/MIT_License).
