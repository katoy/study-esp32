#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

def check_openai_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が環境変数に設定されていません。")
        return

    try:
        client = OpenAI(api_key=api_key)
        # モデル一覧チェック
        models = client.models.list()
        print("✅ OPENAI_API_KEY は有効です。利用可能モデル数:", len(models.data))
        # chat/completionsで実際に推論できるかテスト
        try:
            model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
            params = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello!"}],
            }
            # まずmax_tokensで試す
            params["max_tokens"] = 5
            try:
                resp = client.chat.completions.create(**params)
                print(f"✅ chat/completions APIも利用可能です（モデル: {model}）。応答例:", resp.choices[0].message.content)
            except APIError as e:
                # max_tokensがサポートされていない場合はmax_completion_tokensで再試行
                if "max_tokens" in str(e) and "max_completion_tokens" in str(e):
                    params.pop("max_tokens", None)
                    params["max_completion_tokens"] = 5
                    try:
                        resp = client.chat.completions.create(**params)
                        print(f"✅ chat/completions APIも利用可能です（モデル: {model}、max_completion_tokens使用）。応答例:", resp.choices[0].message.content)
                    except Exception as e2:
                        print("⚠️ chat/completions APIで再試行も失敗:", e2)
                else:
                    print("⚠️ chat/completions APIでエラーが発生しました:", e)
        except RateLimitError:
            print("⚠️ chat/completions APIは有効ですが、利用上限に達しています（クレジット不足）。")
        except Exception as e:
            print("⚠️ chat/completions APIで予期せぬエラー:", e)
    except AuthenticationError:
        print("❌ OPENAI_API_KEY が無効です（認証エラー）。")
    except RateLimitError:
        print("⚠️ OPENAI_API_KEY は有効ですが、利用上限に達しています。")
    except APIError as e:
        print("⚠️ API エラーが発生しました:", e)
    except Exception as e:
        print("⚠️ 予期せぬエラー:", e)

if __name__ == "__main__":
    check_openai_api_key()
