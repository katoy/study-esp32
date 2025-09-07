# Reversi GUI + ChatGPT (オセロAI対戦)

このリポジトリは、Tkinterベースのリバーシ（オセロ）GUIアプリケーションです。
ChatGPT (OpenAI API) をAI対戦相手として利用でき、APIキーがない場合はローカルAIで動作します。

## 特徴
- マウス操作で黒石を配置（あなた=黒、AI=白）
- ChatGPT (OpenAI API) を使った高機能AI対戦（APIキーが必要）
- APIキーがない場合やクォータ超過時はローカルAIで自動応答
- macOS/Windows/Linux で動作
- Python 3.8以降 + Tkinter

## 必要なもの
- Python 3.8以降
- Tkinter（標準で付属。macOSはHomebrew版推奨）
- OpenAI APIキー（ChatGPT対戦を使う場合）
- 必要なパッケージ: openai

## インストール
```sh
# 仮想環境推奨
python3 -m venv venv
source venv/bin/activate
pip install openai
```

## 環境変数の設定
```sh
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export OPENAI_MODEL=gpt-3.5-turbo  # または gpt-4o など利用可能なモデル名
```

## 実行方法
```sh
python3 reversi_gui_chatgpt.py
```

## ファイル構成
- `reversi_gui_chatgpt.py` : メインのリバーシGUIアプリ
- `reversi_gui_chatgpt_offline.py` : ローカルAI専用バージョン
- `check_api_key.py` : OpenAI APIキーの動作確認用スクリプト

## よくある質問
- **APIキーが無効/クォータ超過の場合は？**
  - 自動的にローカルAIで対戦できます。
- **Tkinterが動かない場合は？**
  - macOSではHomebrewで `python-tk` をインストールしてください。
- **モデル名の指定例**
  - `gpt-3.5-turbo`（高速・安価）
  - `gpt-4o`（高精度・新API）

## ライセンス
MIT License

---
ご質問・不具合はIssueまたはPRでご連絡ください。
