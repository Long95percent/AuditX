# OpenAI LLM 岗位模板生成骨架验收说明

## 验收目标

确认用户自定义岗位模板创建走 LLM 接口骨架，而不是规则解析 fallback：

- API key 由用户在设置面板输入。
- 后端保存 OpenAI 设置时不回显 API key。
- 无 API key 时，`POST /api/job-templates/from-jd` 明确失败。
- `OpenAIJobTemplateProvider` 预留 Responses API + Structured Outputs payload。
- 测试中的 `FakeJobTemplateLLMProvider` 仅用于自动化测试，不作为生产 fallback。

## 自动化验收

```powershell
python -m pytest backend\tests\unit\test_job_template_llm_provider.py -q -p no:cacheprovider
python -m pytest backend\tests\integration\test_job_templates_api.py -q -p no:cacheprovider
python -m pytest backend\tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

## UI 手工验收

1. 启动桌面应用。
2. 点击 `OpenAI 设置 / 岗位模板`。
3. 填入 API key、model、base URL。
4. 点击 `保存设置`。
5. 确认状态显示 configured，但界面不会展示完整 API key。
6. 输入岗位名称和 JD。
7. 点击 `调用 LLM 创建岗位模板`。
8. 当前骨架尚未真正发起联网 OpenAI 调用；无 key 时应明确报错，不应生成规则模板。

## 后续实现点

- 在 `OpenAIJobTemplateProvider.generate_from_jd()` 中接入真实 OpenAI Responses API。
- 解析 structured output 并校验为 `JobTemplate`。
- 将生成模板持久化到本地模板库。
