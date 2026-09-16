"""鲁棒性单元测试：覆盖 LLM 输出的各种"不完美"格式。

目的：保证即使用户接入了真实 LLM（DeepSeek/OpenAI），遇到常见格式问题也能正确解析。

覆盖：
    - _clean_json_text（markdown 代码块 / 前缀 / 空字符串）
    - PlannerAgent._parse_plan（各种边界）
    - ExecutorAgent._parse_action（tool_name=null 等）
    - CriticAgent._parse_verdict（satisfied 字段解析）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 强制 mock 模式（无需 API Key）
os.environ["LLM_PROVIDER"] = "mock"

# 让 pytest 能找到 backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ===== _clean_json_text 测试 =====


def test_clean_json_plain():
    """纯 JSON，无杂质。"""
    from backend.agents.planner import _clean_json_text

    cleaned, err = _clean_json_text('{"a": 1}')
    assert err is None
    assert cleaned == '{"a": 1}'


def test_clean_json_markdown_block():
    """```json ... ``` 代码块。"""
    from backend.agents.planner import _clean_json_text

    raw = '```json\n{"a": 1}\n```'
    cleaned, err = _clean_json_text(raw)
    assert err is None
    assert cleaned == '{"a": 1}'


def test_clean_json_plain_code_block():
    """``` ... ``` 无 json 标记。"""
    from backend.agents.planner import _clean_json_text

    raw = '```\n{"a": 1}\n```'
    cleaned, err = _clean_json_text(raw)
    assert err is None
    assert cleaned == '{"a": 1}'


def test_clean_json_prefix_english():
    """JSON: 前缀。"""
    from backend.agents.planner import _clean_json_text

    raw = 'JSON: {"a": 1}'
    cleaned, err = _clean_json_text(raw)
    assert err is None
    assert cleaned == '{"a": 1}'


def test_clean_json_prefix_chinese():
    """中文前缀：以下是 JSON"""
    from backend.agents.planner import _clean_json_text

    raw = '以下是 JSON：{"a": 1}'
    cleaned, err = _clean_json_text(raw)
    assert err is None
    assert cleaned == '{"a": 1}'


def test_clean_json_with_surrounding_text():
    """JSON 前后有解释文字。"""
    from backend.agents.planner import _clean_json_text

    raw = '好的，我的分析如下：\n{"a": 1}\n希望对你有帮助'
    # 这种情况下 _clean_json_text 直接返回原文本（让上层正则提取）
    cleaned, err = _clean_json_text(raw)
    # err 应为 None（清理成功），但 cleaned 会包含全部（由正则提取）
    assert err is None


def test_clean_json_empty():
    """空字符串。"""
    from backend.agents.planner import _clean_json_text

    cleaned, err = _clean_json_text("")
    assert err is None
    assert cleaned == ""

    cleaned, err = _clean_json_text("   \n  ")
    assert err is None
    assert cleaned == ""


# ===== PlannerAgent._parse_plan 测试 =====


def test_planner_parse_clean_json():
    """标准 JSON 输入。"""
    from backend.agents.planner import PlannerAgent

    raw = '{"thought": "测试", "plan": [{"step_id": 1, "subtask": "做某事", "expected_tool": "calculator"}]}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is None
    assert thought == "测试"
    assert len(plan) == 1
    assert plan[0]["subtask"] == "做某事"


def test_planner_parse_markdown_block():
    """LLM 输出 ```json ... ``` 包裹。"""
    from backend.agents.planner import PlannerAgent

    raw = '```json\n{"thought":"分析","plan":[{"step_id":1,"subtask":"步骤","expected_tool":"none"}]}\n```'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is None
    assert thought == "分析"
    assert len(plan) == 1


def test_planner_parse_with_explanation():
    """LLM 在 JSON 前加了说明文字。"""
    from backend.agents.planner import PlannerAgent

    raw = '好的，我来分析：{"thought":"分析","plan":[{"step_id":1,"subtask":"步骤","expected_tool":"none"}]}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is None
    assert thought == "分析"
    assert len(plan) == 1


def test_planner_parse_empty_plan():
    """plan 是空列表（合法）。"""
    from backend.agents.planner import PlannerAgent

    raw = '{"thought": "无需分解", "plan": []}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is None
    assert plan == []


def test_planner_parse_plan_not_list():
    """plan 不是 list（错误）。"""
    from backend.agents.planner import PlannerAgent

    raw = '{"thought": "x", "plan": "not a list"}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is not None
    assert "plan 字段不是 list" in err


def test_planner_parse_item_not_dict():
    """plan[0] 不是 dict。"""
    from backend.agents.planner import PlannerAgent

    raw = '{"thought":"x","plan":["invalid"]}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is not None
    assert "plan[0] 不是 dict" in err


def test_planner_parse_missing_subtask():
    """plan[0] 缺 subtask 字段。"""
    from backend.agents.planner import PlannerAgent

    raw = '{"thought":"x","plan":[{"step_id":1}]}'
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is not None
    assert "缺少 subtask" in err


def test_planner_parse_empty_content():
    """空字符串。"""
    from backend.agents.planner import PlannerAgent

    thought, plan, err = PlannerAgent._parse_plan(None, "")
    assert err is not None
    assert "空内容" in err


def test_planner_parse_garbage():
    """完全乱码。"""
    from backend.agents.planner import PlannerAgent

    raw = "asdklfjasldkjfa"
    thought, plan, err = PlannerAgent._parse_plan(None, raw)
    assert err is not None
    assert len(plan) == 0


# ===== ExecutorAgent._parse_action 测试 =====


def test_executor_parse_with_tool():
    """需要工具。"""
    from backend.agents.executor import ExecutorAgent

    raw = '{"thought":"调计算器","action":{"tool_name":"calculator","tool_input":"1+1"}}'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    assert err is None
    assert action is not None
    assert action.tool_name == "calculator"
    assert action.tool_input == "1+1"


def test_executor_parse_no_tool_null():
    """不需要工具（tool_name=null）。"""
    from backend.agents.executor import ExecutorAgent

    raw = '{"thought":"无需工具","action":{"tool_name":null,"tool_input":""}}'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    assert err is None
    assert action is None


def test_executor_parse_no_tool_string_null():
    """tool_name 是字符串 "null"。"""
    from backend.agents.executor import ExecutorAgent

    raw = '{"thought":"x","action":{"tool_name":"null","tool_input":""}}'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    assert err is None
    assert action is None


def test_executor_parse_no_tool_empty_string():
    """tool_name 是空字符串。"""
    from backend.agents.executor import ExecutorAgent

    raw = '{"thought":"x","action":{"tool_name":"","tool_input":""}}'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    assert err is None
    assert action is None


def test_executor_parse_markdown_block():
    """markdown 代码块。"""
    from backend.agents.executor import ExecutorAgent

    raw = '```json\n{"thought":"x","action":{"tool_name":"calculator","tool_input":"2+3"}}\n```'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    assert err is None
    assert action.tool_name == "calculator"


def test_executor_parse_missing_action_field():
    """缺 action 字段。"""
    from backend.agents.executor import ExecutorAgent

    raw = '{"thought":"x"}'
    thought, action, err = ExecutorAgent._parse_action(None, raw)
    # 没有 action 字段 → action=None（合法情况：纯思考）
    assert err is None
    assert action is None


# ===== CriticAgent._parse_verdict 测试 =====


def test_critic_parse_satisfied_true():
    """满意。"""
    from backend.agents.critic import CriticAgent

    raw = '{"thought":"正确","satisfied":true,"answer":"答案是9","suggestion":""}'
    thought, satisfied, answer, suggestion, err = CriticAgent._parse_verdict(None, raw)
    assert err is None
    assert satisfied is True
    assert answer == "答案是9"


def test_critic_parse_satisfied_false():
    """不满意。"""
    from backend.agents.critic import CriticAgent

    raw = '{"thought":"x","satisfied":false,"answer":"","suggestion":"重做"}'
    thought, satisfied, answer, suggestion, err = CriticAgent._parse_verdict(None, raw)
    assert err is None
    assert satisfied is False
    assert suggestion == "重做"


def test_critic_parse_markdown_block():
    """markdown 代码块。"""
    from backend.agents.critic import CriticAgent

    raw = '```json\n{"thought":"x","satisfied":true,"answer":"yes","suggestion":""}\n```'
    thought, satisfied, answer, suggestion, err = CriticAgent._parse_verdict(None, raw)
    assert err is None
    assert satisfied is True


def test_critic_parse_default_satisfied_false():
    """缺 satisfied 字段 → 默认 False（保守）。"""
    from backend.agents.critic import CriticAgent

    raw = '{"thought":"x","answer":"y"}'
    thought, satisfied, answer, suggestion, err = CriticAgent._parse_verdict(None, raw)
    assert err is None
    assert satisfied is False  # 关键：默认不满意，更安全


def test_critic_parse_empty():
    """空字符串。"""
    from backend.agents.critic import CriticAgent

    thought, satisfied, answer, suggestion, err = CriticAgent._parse_verdict(None, "")
    assert err is not None
    assert satisfied is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])