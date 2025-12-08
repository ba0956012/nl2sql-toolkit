import requests, time
import dashscope
import torch
import json
import re
import os
from runner.logger import Logger
from llm.prompts import prompts_fewshot_parse

# 使用統一的配置管理
try:
    from config import config

    AZURE_ENDPOINT = config.AZURE_OPENAI_ENDPOINT
    AZURE_API_KEY = config.AZURE_OPENAI_API_KEY
except ImportError:
    try:
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        from azure_openai_config import AZURE_OPENAI_CONFIG

        AZURE_ENDPOINT = AZURE_OPENAI_CONFIG.get("endpoint", "")
        AZURE_API_KEY = AZURE_OPENAI_CONFIG.get("api_key", "")
    except (ImportError, Exception):
        # 最後從環境變數讀取
        AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")


def model_chose(step, model="gpt-4 32K"):
    if (
        model.startswith("gpt")
        or model.startswith("claude35_sonnet")
        or model.startswith("gemini")
    ):
        return gpt_req(step, model)
    if model == "deepseek":
        return deep_seek(model)
    if model.startswith("qwen"):
        return qwenmax(model)
    if model.startswith("sft"):
        return sft_req()


class req:
    def __init__(self, step, model) -> None:
        self.Cost = 0
        self.model = model
        self.step = step

    def log_record(self, prompt_text, output):
        logger = Logger()
        logger.log_conversation(prompt_text, "Human", self.step)
        logger.log_conversation(output, "AI", self.step)

    def fewshot_parse(self, question, evidence, sql):
        s = prompts_fewshot_parse().parse_fewshot.format(question=question, sql=sql)
        ext = self.get_ans(s)
        ext = ext.replace("```", "").strip()
        ext = ext.split("#SQL:")[0]  # 防止没按格式生成 至少保留SQL
        ans = self.convert_table(ext, sql)
        return ans

    def convert_table(self, s, sql):
        l = re.findall(" ([^ ]*) +AS +([^ ]*)", sql)
        x, v = s.split("#values:")
        t, s = x.split("#SELECT:")
        for li in l:
            s = s.replace(f"{li[1]}.", f"{li[0]}.")
        return t + "#SELECT:" + s + "#values:" + v


def request(url, model, messages, temperature, top_p, n, key, **k):
    # 判斷是否為 Azure OpenAI（URL 包含 azure.com）
    is_azure = "azure.com" in url if url else False

    # 設定 headers
    if is_azure:
        headers = {"api-key": key, "Content-Type": "application/json"}
    else:
        headers = {
            "Authorization": f"Bearer {key}"
            if key and not key.startswith("Bearer")
            else key,
            "Content-Type": "application/json",
        }

    # Azure OpenAI 不需要在 body 中傳 model（已在 URL 中指定）
    request_body = {
        "messages": [
            {
                "role": "system",
                "content": "You are an SQL expert, skilled in handling various SQL-related issues.",
            },
            {"role": "user", "content": messages},
        ],
        "max_tokens": 800,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        **k,
    }

    # 只有非 Azure 才需要 model 參數
    if not is_azure:
        request_body["model"] = model

    res = requests.post(url=url, json=request_body, headers=headers).json()

    return res


class gpt_req(req):
    def __init__(self, step, model="gpt-4o-0513") -> None:
        super().__init__(step, model)

    def get_ans(self, messages, temperature=0.0, top_p=None, n=1, single=True, **k):
        count = 0
        res = None
        response_clean = None
        
        # Debug: 打印完整 prompt 到控制台（不寫入日誌文件）
        if config.DEBUG_PRINT_PROMPT:
            print(f"\n{'='*80}")
            print(f"🔍 [{self.step}] 完整 LLM Prompt")
            print("="*80)
            print(messages)
            print("="*80 + "\n")

        while count < 50:
            # print(messages) #保存prompt和答案
            try:
                # 使用 Azure OpenAI 配置（如果有設定）
                url = AZURE_ENDPOINT if AZURE_ENDPOINT else ""
                key = AZURE_API_KEY if AZURE_API_KEY else ""

                res = request(
                    url=url,
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    n=n,
                    key=key,
                    **k,
                )
                if n == 1 and single:
                    response_clean = res["choices"][0]["message"]["content"]
                else:
                    response_clean = res["choices"]
                # print(self.step)
                if self.step != "prepare_train_queries":
                    self.log_record(messages, response_clean)  # 记录对话内容
                break

            except Exception as e:
                count += 1
                time.sleep(2)
                # print(messages)
                print(f"Error: {e}, attempt {count}, Cost: {self.Cost}")
                if res:
                    print(f"Response: {res}")

        if res and "usage" in res:
            self.Cost += (
                res["usage"]["prompt_tokens"] / 1000 * 0.042
                + res["usage"]["completion_tokens"] / 1000 * 0.126
            )

        return response_clean


class deep_seek(req):
    def __init__(self, model) -> None:
        super().__init__(model)

    def get_ans(self, messages, temperature=0.0, debug=False):
        count = 0

        while count < 8:
            try:
                url = "https://api.deepseek.com/chat/completions"
                headers = {"Content-Type": "application/json", "Authorization": ""}

                # 定义请求体
                jsons = {
                    "model": "deepseek-coder",
                    "temperture": temperature,
                    "top_p": 0.9,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": messages},
                    ],
                }

                # 发送POST请求
                response = requests.post(url, headers=headers, json=jsons)
                if debug:
                    print(response.json)
                ans = response.json()["choices"][0]["message"]["content"]
                break
            except Exception as e:
                count += 1
                time.sleep(2)
                print(e, count, self.Cost, response.json())
        return ans


class qwenmax(req):
    def __init__(self, model) -> None:
        super().__init__(model)
        dashscope.api_key = ""

    def get_ans(self, messages, temperature=0.0, debug=False):
        count = 0

        while count < 8:
            try:
                response = dashscope.Generation.call(
                    model=self.model, temperature=temperature, prompt=messages
                )
                self.Cost += (
                    response.usage.input_tokens / 1000 * 0.04
                    + response.usage.output_tokens / 1000 * 0.12
                )
                return response.output["text"]
            except:
                count += 1
                time.sleep(5)
                print(response.code, response.message)


class sft_req(req):
    def __init__(self, model) -> None:
        super().__init__(model)
        self.device = "cuda:0"
        self.tokenizer = AutoTokenizer.from_pretrained(
            "", trust_remote_code=True, padding_side="right", use_fast=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token = "<|EOT|>"
        # drop device_map if running on CPU
        self.model = AutoModelForCausalLM.from_pretrained(
            "", torch_dtype=torch.bfloat16, device_map=self.device
        ).eval()

    def get_ans(self, text, temperature=0.0):
        messages = [
            {
                "role": "system",
                "content": "You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer.",
            },
            {"role": "user", "content": text},
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        model_inputs = self.tokenizer(
            [inputs], return_tensors="pt", max_length=8000
        ).to("cuda")
        # tokenizer.eos_token_id is the id of <|EOT|> token
        generated_ids = self.model.generate(
            model_inputs.input_ids,
            attention_mask=model_inputs["attention_mask"],
            max_new_tokens=800,
            do_sample=False,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.decode(
            generated_ids[0][:-1], skip_special_tokens=True
        ).strip()
        return response
