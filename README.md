# 商品交易半自动助手

## 1. 项目用途

本项目用于本地商品交易界面的半自动辅助：固定区域截图、界面图像分析、开仓建议、持仓反馈和半自动填单。默认不自动提交订单，只做安全的辅助流程。

## 2. 安装依赖方式

```bash
pip install -r requirements.txt
```

## 3. `.env` 配置方式

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=你的密钥
```

第一版代码即使没有该配置也可以运行，会自动使用 mock/占位结果。

## 4. 如何修改固定截图区域坐标

请编辑 `src/config.py` 中以下配置：

- `CHART_REGION`
- `ORDER_PANEL_REGION`
- `POSITION_REGION`
- `PRICE_REGION`

以及半自动填单的点击坐标：

- `BUY_BUTTON_POS`
- `SELL_BUTTON_POS`
- `PRICE_INPUT_POS`
- `LOT_INPUT_POS`

这些值当前只是示例，需要你根据真实交易软件界面人工调整。

## 5. 如何运行 VS Code tasks

打开 VS Code 后，进入“终端 -> 运行任务”，即可选择：

- 安装依赖
- 运行主程序
- 测试截图模块
- 测试OCR模块
- 测试GPT分析模块
- 测试自动填单模块
- 运行 pytest
- 格式化代码
- 查看 git status

### replay 测试说明

replay 测试数据位于 `data/replay_cases/*.json`，用于离线回放校验，不依赖网络、不需要登录 GitHub，也不需要新增依赖。

常见字段包括：

- `case_id`
- `position_state`
- `analysis_result`
- `last_exit_time`
- `meta`

replay 测试链路：`replay_loader -> result_validator -> decision_engine`

运行示例：

```bash
pytest tests/test_replay_loader.py
pytest tests/test_replay_cases.py
pytest tests/test_replay_decision_engine.py
pytest
```

示例片段：

```json
{
  "case_id": "sample_case_x",
  "position_state": {"has_position": false, "direction": "none", "lots": 0},
  "analysis_result": {"action": "BUY", "allowed": true, "direction": "long"},
  "last_exit_time": null,
  "meta": {"source": "replay"}
}
```

## 6. 如何运行 `main.py`

推荐使用包方式启动：

```bash
python -m src.main
```

当前版本只执行一次完整流程，不包含无限循环。

## 7. 安全声明

默认不自动提交订单，只做半自动填单辅助。`order_filler.py` 默认 `dry_run=True`，并且主流程不会点击最终提交按钮。
