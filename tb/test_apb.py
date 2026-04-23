import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge,ReadOnly
import random

# ========================================================
# 验证组件 (VIP) - 把总线时序封装成一个 Python 类
# ========================================================
class ApbMaster:
    """ APB 总线 Master 驱动器"""
    def __init__(self,dut):
        self.dut = dut
        # 初始状态： 把总线信号全部清零
        self.dut.PSEL.value = 0
        self.dut.PENABLE.value = 0
        self.dut.PWRITE.value = 0
        self.dut.PADDR.value = 0
        self.dut.PWDATA.value = 0

    async def write(self,addr,data):
        """发起一次 APB 写传输"""
        await RisingEdge(self.dut.PCLK)

        # --- T1: Setup Phase (建立阶段) ---
        self.dut.PSEL.value = 1
        self.dut.PWRITE.value = 1
        self.dut.PADDR.value = addr
        self.dut.PWDATA.value = data
        await RisingEdge(self.dut.PCLK)

        # --- T2: Access Phase (访问阶段) ---
        self.dut.PENABLE.value = 1

        # 等待 Slave 准备好 (处理PREADY逻辑)
        while True:
            await RisingEdge(self.dut.PCLK)
            if self.dut.PREADY.value == 1:
                break

        # 传输完成，总线归零
        self.dut.PSEL.value = 0
        self.dut.PENABLE.value = 0
        self.dut._log.info(f"[APB WRITE] ADDR: 0x{addr:08X}, DATA: 0x{data:08X}")
    async def read(self,addr):
        """发起一次 APB 读传输，并返回读到的数据"""
        await RisingEdge(self.dut.PCLK)

        # --- T1: Setup Phase ---
        self.dut.PSEL.value = 1
        self.dut.PWRITE.value = 0
        self.dut.PADDR.value = addr
        await RisingEdge(self.dut.PCLK)

        # --- T2: Access Phase ---
        self.dut.PENABLE.value = 1
        while True:
            await RisingEdge(self.dut.PCLK)
            if self.dut.PREADY.value == 1:
                self.dut.PENABLE.value = 0
                break
        # 获取读出的数据
        self.dut.PSEL.value = 0
        self.dut.PENABLE.value = 0

        await ReadOnly()
        rdata = int(self.dut.PRDATA.value)

        self.dut._log.info(f"[APB READ]  Addr: 0x{addr:08X}, Data: 0x{rdata:08X}")
        return rdata
# ========================================================
# 顶层测试用例
# ========================================================
@cocotb.test()
async def test_apb(dut):
    """ 测试 APB RAM 的 读写一致型"""

    # 1. 启动时钟
    cocotb.start_soon(Clock(dut.PCLK,10,unit="ns").start())

    # 2. 实例化我们写的类，创造一个 APB Master 对象
    apb_mst = ApbMaster(dut)

    # 3. 复位系统
    dut.PRESETn.value = 0
    await RisingEdge(dut.PCLK)
    dut.PRESETn.value = 1
    await RisingEdge(dut.PCLK)
    dut._log.info("--- 开始 APB 读写测试")

    # 建立一个Python 字典作为Scoreboard(计分版模型)
    scoreboard = {}
    for _ in range(5):
        rand_addr = random.randint(0,15)
        rand_data = random.randint(0,0xFFFFFFFF)
        await apb_mst.write(rand_addr,rand_data)
        scoreboard[rand_addr] = rand_data
    dut._log.info("--- 写入完毕 开始校验读出数据")

    # 遍历刚才写的地址，读出来并比对
    for addr,expected_data in scoreboard.items():
        actual_data = await apb_mst.read(addr)
        assert expected_data == actual_data, f"数据比对失败！ Addr：{addr:08X},期望：{expected_data:08X},实际：{actual_data:08X}"

    dut._log.info("--- APB 测试全部PASS! ---")



