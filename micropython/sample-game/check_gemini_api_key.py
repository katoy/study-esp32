#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import google.generativeai as genai
from google.api_core import exceptions

def check_gemini_api_key():
    """Checks the validity of the GEMINI_API_KEY."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY が環境変数に設定されていません。")
        return

    try:
        genai.configure(api_key=api_key)
        
        # モデル一覧チェック
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models:
            print("⚠️ 有効なモデルが見つかりませんでした。")
            return
            
        print(f"✅ GEMINI_API_KEY は有効です。利用可能モデル数: {len(models)}")

        # コンテンツ生成で実際に推論できるかテスト
        try:
            # 利用可能なモデルからテストに使うモデルを選択する
            test_model_name = None
            model_names = [m.name for m in models]

            # 希望のモデルを探す
            preferred_models = ['gemini-1.5-pro-latest', 'gemini-1.0-pro', 'gemini-pro']
            for p_model in preferred_models:
                if f'models/{p_model}' in model_names:
                    test_model_name = p_model
                    break
            
            # 見つからない場合、visionを含まない最初のモデルを使用する
            if not test_model_name:
                for m_name in model_names:
                    if 'vision' not in m_name and 'embedding' not in m_name:
                        test_model_name = m_name.split('/')[-1]
                        break

            if not test_model_name:
                print("⚠️ コンテンツを生成できる適切なテキストモデルが見つかりませんでした。")
                return

            model = genai.GenerativeModel(test_model_name)
            
            resp = model.generate_content("Hello!")
            
            # 応答にテキストがあるかチェック
            if resp.text:
                print(f"✅ generate_content APIも利用可能です（モデル: {test_model_name}）。応答例:", resp.text)
            else:
                # テキストがない場合、ブロックされた可能性
                print("⚠️ generate_content APIは呼び出せましたが、応答が空でした。ブロックされた可能性があります。")
                if resp.prompt_feedback:
                    print("Prompt Feedback:", resp.prompt_feedback)

        except exceptions.PermissionDenied as e:
            print(f"❌ generate_content APIの呼び出しで権限エラーが発生しました。APIが有効になっていない可能性があります。: {e}")
        except exceptions.ResourceExhausted:
            print("⚠️ generate_content APIは有効ですが、利用上限に達しています（クォータ不足）。")
        except Exception as e:
            print(f"⚠️ generate_content APIで予期せぬエラー: {e}")

    except exceptions.PermissionDenied as e:
        print(f"❌ GEMINI_API_KEY が無効か、APIが有効になっていません（権限エラー）。: {e}")
    except exceptions.ResourceExhausted:
        print("⚠️ GEMINI_API_KEY は有効ですが、利用上限に達しています。")
    except Exception as e:
        print(f"⚠️ 予期せぬエラー: {e}")

if __name__ == "__main__":
    check_gemini_api_key()
