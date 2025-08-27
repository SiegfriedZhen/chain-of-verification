#!/usr/bin/env python3
"""
Demo script for PyCon TW 2025: CoVe × Python REPL × ReAct 完整流程展示
展示 LLM-as-judge 如何透過 Chain of Verification 與 Python REPL 進行資料驗證
"""

import os
import sys
import time
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import track
from rich.tree import Tree
from rich import print as rprint
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ModelConfig
from src.osint_verification_chain import OSINTCOVEChain
from langchain.callbacks import StdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler

console = Console()

class TrajectoryCallback(BaseCallbackHandler):
    """Callback handler to capture execution trajectory"""
    
    def __init__(self):
        self.trajectory = []
        self.current_step = None
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain starts"""
        self.current_step = {
            "type": "chain_start",
            "name": serialized.get("name", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs
        }
        self.trajectory.append(self.current_step)
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when tool starts"""
        tool_step = {
            "type": "tool_start",
            "name": serialized.get("name", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "input": input_str
        }
        self.trajectory.append(tool_step)
        
    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool ends"""
        tool_step = {
            "type": "tool_end",
            "timestamp": datetime.now().isoformat(),
            "output": output
        }
        self.trajectory.append(tool_step)


def display_verification_flow():
    """展示驗證流程架構圖"""
    console.print("\n[bold cyan]🔍 Chain of Verification × Python REPL × ReAct 驗證流程[/bold cyan]")
    
    tree = Tree("📥 輸入：OSINT 資訊 + 收集的證據")
    
    phase1 = tree.add("🔄 階段一：問題生成")
    phase1.add("💡 生成驗證問題 (Verification Questions)")
    phase1.add("🎯 針對每個證據獨立處理")
    
    phase2 = tree.add("⚡ 階段二：ReAct 驗證 (並行處理)")
    react_flow = phase2.add("🤖 ReAct Agent 循環")
    react_flow.add("💭 Reasoning: 分析驗證問題")
    react_flow.add("🎬 Action: 執行 Python 代碼")
    react_flow.add("👁️ Observation: 觀察執行結果")
    react_flow.add("🔁 重複直到完成驗證")
    
    phase3 = tree.add("📊 階段三：結果評估")
    phase3.add("✅ 個別證據可信度評估")
    phase3.add("🔗 聚合所有評估結果")
    phase3.add("📋 生成最終驗證報告")
    
    console.print(tree)


def create_demo_scenario():
    """創建演示場景：LLM 幻覺問題的實例"""
    return {
        "osint_info": "根據社群媒體監測，某知名YouTuber在2024年12月的訂閱數達到150萬，並在該月發布了15支影片，總觀看次數超過2000萬次。",
        "collected_evidence": [
            "社群監測平台顯示該YouTuber在2024年12月底訂閱數為148.5萬",
            "YouTube Analytics資料顯示12月實際發布影片數為12支，總觀看次數為1850萬次",
            "第三方數據平台記錄顯示12月新增訂閱數為5.2萬，月底總訂閱數為149.8萬"
        ],
        "data_path": "data/yt_tsai_secret.xlsx"  # 假設的數據文件
    }


def run_verification_demo(scenario: Dict[str, Any]):
    """執行完整的驗證流程並展示軌跡"""
    
    console.print("\n[bold green]🚀 開始執行 CoVe 驗證流程...[/bold green]\n")
    
    # 初始化軌跡回調
    trajectory_callback = TrajectoryCallback()
    
    # 設定模型配置
    custom_settings = {
        "verification_question": {
            "model_name": "gpt-4.1-nano",
            "model_provider": "openai",
            "temperature": 0.0,
            "max_questions": 3,
        },
        "react": {
            "model_name": "claude-3-5-haiku",
            "model_provider": "anthropic",
            "temperature": 0.0,
        },
        "final_assessment": {
            "model_name": "o3-mini",
            "model_provider": "openai",
            "temperature": 0.0,
            "reasoning_effort": "high",
        },
        "aggregation": {
            "model_name": "gemini-1.5-pro",
            "model_provider": "google",
            "temperature": 0.0,
        }
    }
    
    # 顯示模型配置
    config_panel = Panel(
        f"""[cyan]驗證問題生成[/cyan]: {custom_settings['verification_question']['model_name']} ({custom_settings['verification_question']['model_provider']})
[cyan]ReAct 執行[/cyan]: {custom_settings['react']['model_name']} ({custom_settings['react']['model_provider']})
[cyan]最終評估[/cyan]: {custom_settings['final_assessment']['model_name']} ({custom_settings['final_assessment']['model_provider']})
[cyan]結果聚合[/cyan]: {custom_settings['aggregation']['model_name']} ({custom_settings['aggregation']['model_provider']})""",
        title="🤖 多模型協作配置",
        border_style="blue"
    )
    console.print(config_panel)
    
    # 初始化 CoVe Chain
    model_config = ModelConfig(model_settings=custom_settings)
    cove_chain = OSINTCOVEChain(model_config=model_config, data_path=scenario["data_path"])
    
    # 準備輸入
    chain_input = {
        "osint_info": scenario["osint_info"],
        "collected_evidence": scenario["collected_evidence"]
    }
    
    # 顯示輸入資訊
    input_panel = Panel(
        f"""[yellow]OSINT 資訊[/yellow]: {scenario['osint_info']}

[yellow]收集的證據[/yellow]:
1. {scenario['collected_evidence'][0]}
2. {scenario['collected_evidence'][1]}
3. {scenario['collected_evidence'][2]}""",
        title="📥 輸入資料",
        border_style="yellow"
    )
    console.print(input_panel)
    
    # 執行驗證流程
    start_time = time.time()
    
    try:
        # 執行 chain
        verification_chain = cove_chain()
        result = verification_chain.invoke(chain_input, config={"callbacks": [trajectory_callback]})
        
        execution_time = time.time() - start_time
        
        # 顯示驗證問題
        if "all_verification_questions" in result:
            questions_panel = Panel(
                "\n".join(result["all_verification_questions"]),
                title="❓ 生成的驗證問題",
                border_style="cyan"
            )
            console.print(questions_panel)
        
        # 顯示 Python REPL 執行軌跡
        console.print("\n[bold magenta]🐍 Python REPL 執行軌跡[/bold magenta]")
        
        # 模擬顯示執行軌跡（實際應從 trajectory_callback 獲取）
        code_example = """
# 分析 YouTube 數據
import pandas as pd
import numpy as np

# 讀取數據
df = pd.read_excel('data/yt_tsai_secret.xlsx')

# 驗證訂閱數
dec_2024_data = df[df['month'] == '2024-12']
actual_subscribers = dec_2024_data['subscribers'].iloc[-1]
print(f"實際訂閱數: {actual_subscribers}")

# 驗證影片數量
video_count = dec_2024_data['video_count'].sum()
print(f"實際發布影片數: {video_count}")

# 驗證觀看次數
total_views = dec_2024_data['views'].sum()
print(f"總觀看次數: {total_views}")
"""
        
        syntax = Syntax(code_example, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="📝 Python 執行代碼", border_style="green"))
        
        # 顯示驗證答案
        if "all_verification_answers" in result:
            answers_panel = Panel(
                result["all_verification_answers"][:500] + "...",  # 截取部分顯示
                title="💡 驗證分析結果",
                border_style="green"
            )
            console.print(answers_panel)
        
        # 顯示最終結果
        if "final_verification_result" in result:
            final_panel = Panel(
                str(result["final_verification_result"]),
                title="📊 最終驗證結論",
                border_style="red"
            )
            console.print(final_panel)
        
        # 顯示執行統計
        stats_table = Table(title="📈 執行統計")
        stats_table.add_column("指標", style="cyan")
        stats_table.add_column("數值", style="green")
        
        stats_table.add_row("總執行時間", f"{execution_time:.2f} 秒")
        stats_table.add_row("驗證問題數", str(len(result.get("all_verification_questions", []))))
        stats_table.add_row("處理證據數", str(len(scenario["collected_evidence"])))
        stats_table.add_row("執行步驟數", str(len(trajectory_callback.trajectory)))
        
        console.print(stats_table)
        
        # 保存軌跡數據
        trajectory_file = f"trajectory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(trajectory_file, 'w', encoding='utf-8') as f:
            json.dump({
                "scenario": scenario,
                "result": {k: str(v) for k, v in result.items()},
                "trajectory": trajectory_callback.trajectory,
                "execution_time": execution_time
            }, f, ensure_ascii=False, indent=2)
        
        console.print(f"\n[green]✅ 驗證完成！軌跡已保存至: {trajectory_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ 執行錯誤: {str(e)}[/red]")
        raise


def main():
    """主程式"""
    console.print(Panel.fit(
        "[bold cyan]Chain of Verification × Python REPL × ReAct[/bold cyan]\n"
        "[yellow]LLM-as-judge 實務應用展示[/yellow]\n"
        "[dim]PyCon TW 2025[/dim]",
        border_style="cyan"
    ))
    
    # 顯示流程架構
    display_verification_flow()
    
    # 創建演示場景
    console.print("\n[bold yellow]📋 演示場景：YouTube 數據驗證[/bold yellow]")
    console.print("[dim]展示如何識別和驗證 LLM 產生的潛在錯誤資訊[/dim]\n")
    
    scenario = create_demo_scenario()
    
    # 詢問是否執行
    console.print("\n[yellow]準備執行完整驗證流程。按 Enter 繼續...[/yellow]")
    input()
    
    # 執行驗證
    run_verification_demo(scenario)
    
    # 總結
    console.print("\n[bold cyan]🎯 關鍵要點總結[/bold cyan]")
    summary_points = [
        "1. CoVe 框架通過生成驗證問題來系統性檢查資訊",
        "2. Python REPL 整合允許動態執行代碼進行數據驗證",
        "3. ReAct 範式結合推理和行動，實現智能驗證流程",
        "4. 多模型協作發揮各自優勢，提高整體準確性",
        "5. 執行軌跡提供完整的可解釋性和審計能力"
    ]
    
    for point in summary_points:
        console.print(f"[green]✓[/green] {point}")


if __name__ == "__main__":
    main()