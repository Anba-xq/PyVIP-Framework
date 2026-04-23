# 文件名: test_axis_vip.py
import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotbext.axi import AxiStreamBus, AxiStreamSource, AxiStreamSink

# +++ 1. 定义一个“随机延迟生成器” +++
def random_stall_gen():
    """每次调用，随机返回 0 到 4 之间的整数，代表要暂停的时钟周期数"""
    while True:
        yield random.randint(0, 4)

@cocotb.test()
async def test_axis_magic(dut):

    # 基础时钟和复位
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # ========================================================
    # .from_prefix 能够自动寻找代码里所有以 s_axis 和 m_axis 开头的引脚，自动捆绑！
    # ========================================================
    source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "s_axis"), dut.clk, dut.rst_n)
    sink = AxiStreamSink(AxiStreamBus.from_prefix(dut, "m_axis"), dut.clk, dut.rst_n)

    source.set_pause_generator(random_stall_gen())
    sink.set_pause_generator(random_stall_gen())

    dut._log.info("--- 开始发送数据 ---")

    # 准备要发送的一批数据（字节数组）
    # 发送 3 个 32-bit (4字节) 的数据包
    send_data_1 = b'\x11\x22\x33\x44'  # 等于 0x44332211 (小端序)
    send_data_2 = b'\xAA\xBB\xCC\xDD'
    send_data_3 = b'\xFF\xEE\xDD\xCC'

    await source.send(send_data_1)
    await source.send(send_data_2)
    await source.send(send_data_3)

    dut._log.info("--- 数据发送完毕，等待接收 ---")

    recv_1 = await sink.recv()
    recv_2 = await sink.recv()
    recv_3 = await sink.recv()

    #  断言检查
    assert recv_1.tdata == send_data_1, "包 1 数据错误！"
    assert recv_2.tdata == send_data_2, "包 2 数据错误！"
    assert recv_3.tdata == send_data_3, "包 3 数据错误！"

    dut._log.info("--- AXI-Stream VIP 验证完美 PASS！ ---")
