# SwitchBot GUI Controller for Windows 11

このリポジトリには、Windows 11 上で SwitchBot デバイス（テレビや照明など）を GUI からオン／オフ制御するための Python スクリプトが含まれています。Tkinter を用いたシンプルなデスクトップアプリで、SwitchBot のクラウド API を呼び出してコマンドを実行します。

## 機能概要

- SwitchBot クラウド API への署名付きリクエストの送信
- 複数デバイス（テレビ、照明など）のオン／オフボタンを GUI 上に表示
- 実行結果やエラーメッセージを GUI 内に表示
- 設定ファイルでデバイスやコマンドを柔軟に管理

## 必要条件

- Windows 11
- Python 3.10 以上（[Python 公式サイト](https://www.python.org/downloads/windows/) からインストール）
- SwitchBot Hub および制御したいデバイス（赤外線リモコン登録済みのテレビ・照明など）
- SwitchBot アプリで取得した `Open Token` と `Secret`

## セットアップ手順

1. 本リポジトリをクローン、または ZIP をダウンロードして任意のフォルダーに展開します。

   ```powershell
   git clone https://github.com/your-account/gpt-python.git
   cd gpt-python
   ```

2. Python 仮想環境を作成（任意）し、依存パッケージをインストールします。

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. `config.example.json` を `config.json` にコピーし、`token`、`secret`、`devices` 内の `deviceId` を SwitchBot アプリの情報に合わせて編集します。

   ```powershell
   copy config.example.json config.json
   ```

   - `deviceId`: SwitchBot アプリの「クラウドサービス」>「API リスト」から取得
   - `command`: `turnOn` / `turnOff` など、デバイスに応じたコマンドを設定
   - `commandType`: 通常は `command`（赤外線リモコンの場合も `command`）
   - `parameter`: 多くのデバイスは `default` を指定

4. アプリを起動します。

   ```powershell
   python switchbot_gui.py
   ```

5. GUI 上に各デバイスのオン／オフボタンが表示されるので、操作したいボタンをクリックします。結果は画面下部のステータス欄に表示されます。

## トラブルシューティング

- **署名エラーが表示される**: `token` と `secret` が正しいか、時刻ズレがないかを確認してください。
- **403 Forbidden**: SwitchBot アプリで対象デバイスがクラウドサービスに連携されているか確認してください。
- **GUI が応答しない**: ネットワーク状況によって API 応答が遅延する場合があります。数秒待っても改善しない場合はアプリを再起動してください。

## ライセンス

MIT License