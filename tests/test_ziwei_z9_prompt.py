"""
Tests for Z-9: AI prompt 结构化输出协议升级

验证 ZIWEI_ANALYSIS_INSTRUCTION 含完整七步指令 + 引用标签格式协议。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.context_builder import ZIWEI_ANALYSIS_INSTRUCTION


def test_instruction_has_seven_steps():
    """验证 INSTRUCTION 含七步标题"""
    print("=" * 70)
    print("TEST 1: 七步章节标题完整")
    print("=" * 70)
    expected_steps = [
        "第一步：命格定位",
        "第二步：来因宫论核心命题",
        "第三步：生年四化论吉凶",
        "第四步：飞星派飞化语象",
        "第五步：大限流年应期",
        "第六步：用户问题精答",
        "第七步：结论与建议",
    ]
    for step in expected_steps:
        assert step in ZIWEI_ANALYSIS_INSTRUCTION, f"缺失 {step}"
    print(f"  ✓ 七步章节标题全部存在")
    print()


def test_instruction_has_output_protocol():
    """验证含【输出格式协议】section"""
    print("=" * 70)
    print("TEST 2: 输出格式协议存在")
    print("=" * 70)
    assert "输出格式协议" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失输出格式协议 section"
    assert "## 第一步" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失章节示例"
    print(f"  ✓ 含输出格式协议章节")
    print()


def test_instruction_has_citation_format():
    """验证 [依据：xxx·yyy] 格式说明"""
    print("=" * 70)
    print("TEST 3: 引用溯源标签格式说明")
    print("=" * 70)
    assert "[依据：" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失引用格式说明"
    # 所有 section 名都被声明
    sections = [
        "主星亮度评级", "经典格局", "飞星派飞化", "冲宫连锁",
        "生年四化", "来因宫", "三方四正", "大限盘", "流年盘",
    ]
    for s in sections:
        assert s in ZIWEI_ANALYSIS_INSTRUCTION, f"section '{s}' 未在协议中"
    print(f"  ✓ 9 个 section 名全部声明")
    print()


def test_instruction_has_examples():
    """验证含正确和错误示例"""
    print("=" * 70)
    print("TEST 4: 正反示例")
    print("=" * 70)
    # 正面示例
    assert "[依据：主星亮度评级" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失主星亮度评级正例"
    assert "[依据：经典格局" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失经典格局正例"
    # 反面示例
    assert "禁止" in ZIWEI_ANALYSIS_INSTRUCTION, "缺失禁止规则"
    assert "❌" in ZIWEI_ANALYSIS_INSTRUCTION or "不要" in ZIWEI_ANALYSIS_INSTRUCTION
    print(f"  ✓ 含正反示例")
    print()


def test_full_prompt_can_be_generated():
    """验证完整 prompt 仍能生成（不报错）"""
    print("=" * 70)
    print("TEST 5: 完整 prompt 生成不报错")
    print("=" * 70)
    try:
        from core.ziwei.context_builder import build_ziwei_context

        # 测试用 mock 数据
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from test_ziwei_context import make_mock_chart_2000_8_16
        data = make_mock_chart_2000_8_16()
        text = build_ziwei_context(data)
        # 应能完整生成并包含 INSTRUCTION 的"输出格式协议"已加入新版
        # （build_ziwei_context 不自动加 INSTRUCTION，那是 agent.py 拼装的）
        assert len(text) > 1000
        print(f"  ✓ build_ziwei_context 成功，长度 {len(text)} chars")
    except ImportError:
        print("  · 跳过：缺少 mock data")
    print()


def test_agent_system_prompt_updated():
    """验证 api/agent.py 的 ziwei system prompt 也升级了"""
    print("=" * 70)
    print("TEST 6: agent.py ziwei system prompt 升级")
    print("=" * 70)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.agent import INTERPRET_SYSTEMS
    ziwei_sys = INTERPRET_SYSTEMS.get("ziwei", "")
    assert "Z-9" in ziwei_sys or "强制结构化" in ziwei_sys, "system prompt 未升级"
    assert "[依据：" in ziwei_sys, "system prompt 缺溯源标签"
    print(f"  ✓ ziwei system prompt 含 Z-9 结构化协议")
    print()


if __name__ == "__main__":
    test_instruction_has_seven_steps()
    test_instruction_has_output_protocol()
    test_instruction_has_citation_format()
    test_instruction_has_examples()
    test_full_prompt_can_be_generated()
    test_agent_system_prompt_updated()
    print("=" * 70)
    print("ALL Z-9 PROMPT TESTS PASSED")
    print("=" * 70)
