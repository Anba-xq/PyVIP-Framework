import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge,FallingEdge,ReadOnly
import random
import queue


# ---------------------------------------------------------
# 验证组件 1：Monitor
# ---------------------------------------------------------
async def monitor_output(dut,expected_q):
    """
    监控器：死循环盯着时钟，只要 rd_en 为1 且不为空
    就在下一个时钟读取数据，并于 Scoreboard(expected_q)对比。
    """
    while True:
        await RisingEdge(dut.clk)

        # 使用 ReadOnly 确保我们是在时钟沿之后读取稳定的数据
        await ReadOnly()

        # 如果当前周期有有效的读操作
        if dut.rd_en.value == 1 and dut.empty.value == 0:
            await RisingEdge(dut.clk)
            await ReadOnly()
            actual_data = int(dut.rd_data.value)
            if expected_q.empty():
                dut._log.info("读出了数据，但Scoreboard 里没有期望数据！")
            expected_data = expected_q.get()
            dut._log.info(f"[Monitor] 读出数据：{actual_data},期望：{expected_data}" )
            assert actual_data == expected_data, f"数据不匹配！期望 {expected_data}，实际 {actual_data}"
# ---------------------------------------------------------
# 验证组件 2：Driver 函数
# ---------------------------------------------------------
async def writr_fifo(dut,data,expected_q):
    """往fifo写入一个数据，并把数据存入计分板（expected_q）"""
    await RisingEdge(dut.clk)
    if dut.full.value == 1:
        dut._log.info("FIFO 已满，无法写入！")
        return
    dut.wr_en.value = 1
    dut.wr_data.value = data
    expected_q.put(data)  # 【关键】同时发给计分板
    dut._log.info(f"[Driver] 写入数据：{data}")

    await RisingEdge(dut.clk)
    dut.wr_en.value = 0 # 及时拉低使能


async def read_fifo(dut):
    """发起一次读操作"""
    await RisingEdge(dut.clk)
    if dut.empty.value == 1:
        dut._log.warning("FIFO 已空，无法读取！")
        return

    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    dut.rd_en.value = 0

@cocotb.test()
async def test_fifo_random_traffic(dut):
    """测试fifo 随机读写"""
    # 1.初始化时钟
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.wr_en.value =0
    dut.rd_en.value =0
    dut.rst_n.value =0

    # 创建计分板队列
    expected_q=queue.Queue()

    # 2.启动后台 Monitor 协程
    cocotb.start_soon(monitor_output(dut,expected_q))

    await RisingEdge(dut.clk)
    dut.rst_n.value =1
    await RisingEdge(dut.clk)

    # 4.产生随机激励数据
    dut._log.info("--- 开始随机测试 ---")

    for i in range(20):
        action = random.choice(["write","read"])
        if action == "write":
            random_data = random.randint(0,255)
            await writr_fifo(dut,random_data,expected_q)
        else:
            await read_fifo(dut)
    # 5. 最后把里面剩下的数据全部读空
    dut._log.info("--- 清空剩余数据 ---")
    while not expected_q.empty():
        await read_fifo(dut)

    dut._log.info("--- FIFO 验证全部 PASS！ ---")
