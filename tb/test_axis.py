import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge,ReadOnly
import random
import queue


# ========================================================
# 发送端 (Source)
# ========================================================
class MyAxiStreamSource:
    def __init__(self, clk, tvalid, tready, tdata):
        self.clk = clk
        self.tvalid = tvalid
        self.tready = tready
        self.tdata = tdata
        self.tvalid.value = 0

    async def send(self, data_list):
        for data in data_list:

            # 1. 随机阶段
            delay_cycles = random.randint(0, 3)
            for _ in range(delay_cycles):
                # 先等时钟沿（脱离 ReadOnly），再驱动信号
                await RisingEdge(self.clk)
                self.tvalid.value = 0

            # 2. 准备发送阶段
            await RisingEdge(self.clk)
            self.tvalid.value = 1
            self.tdata.value = data

            # 3. 握手等待阶段
            while True:
                await ReadOnly()
                # 采样对方的 Ready
                if self.tready.value == 1:
                    break  # 握手成功！准备发下一个。（下一个循环开头的 RisingEdge 会带我们离开 ReadOnly）

                # 如果没成功，必须等下一个时钟沿再进入下一轮 ReadOnly
                await RisingEdge(self.clk)

        # 4. 全部发完后，等待一个边沿，收工
        await RisingEdge(self.clk)
        self.tvalid.value = 0


# ========================================================
# 接收端 (Sink)
# ========================================================
class MyAxiStreamSink:
    def __init__(self, clk, tvalid, tready, tdata):
        self.clk = clk
        self.tvalid = tvalid
        self.tready = tready
        self.tdata = tdata
        self.queue = queue.Queue()
        self.tready.value = 0
        cocotb.start_soon(self._monitor_loop())

    async def _monitor_loop(self):
        while True:
            # 1. ReadOnly 状态！
            await RisingEdge(self.clk)

            # 2. 此时处于 Active 阶段，可以安全地驱动引脚
            will_accept = random.choice([True, False])
            self.tready.value = 1 if will_accept else 0

            # 3. 驱动完之后，进入 ReadOnly 准备抓取数据
            await ReadOnly()

            if self.tvalid.value == 1 and self.tready.value == 1:
                received_data = int(self.tdata.value)
                self.queue.put(received_data)

    async def recv(self):
        while self.queue.empty():
            await RisingEdge(self.clk)
        return self.queue.get()

# ========================================================
# 顶层测试用例 (Testbench)
# ========================================================
@cocotb.test()
async def test_my_own_axis(dut):
    """测试我自己手写的 AXI-Stream VIP！"""

    # 1. 基础时钟和复位
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # 2. 实例化(手动把引脚绑进去)
    source = MyAxiStreamSource(
        clk=dut.clk,
        tvalid=dut.s_axis_tvalid,
        tready=dut.s_axis_tready,
        tdata=dut.s_axis_tdata
    )

    sink = MyAxiStreamSink(
        clk=dut.clk,
        tvalid=dut.m_axis_tvalid,
        tready=dut.m_axis_tready,
        tdata=dut.m_axis_tdata
    )

    dut._log.info("--- 开始使用自研 VIP 发送数据 ---")

    # 准备要发送的数据
    send_list = [0x11223344, 0xAABBCCDD, 0xFFEEDDCC]

    # 3. 发送数据！(背压和延迟会在 VIP 内部自动产生)
    await source.send(send_list)

    dut._log.info("--- 数据发送完毕，检查接收结果 ---")

    # 4. 接收并比对
    for expected_data in send_list:
        actual_data = await sink.recv()
        dut._log.info(f"收到数据: 0x{actual_data:08X}, 期望: 0x{expected_data:08X}")
        assert actual_data == expected_data, "数据因为拥堵丢包了！测试失败！"

    dut._log.info("--- 自研 AXI-Stream VIP 背压测试完美 PASS！ ---")
