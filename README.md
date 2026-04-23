# PyVIP-Framework
Python Verification IP Framework
基于 Cocotb 的全栈敏捷 IC 验证环境

简介： 本项目摒弃了传统 SystemVerilog 的繁琐语法，采用纯 Python (Cocotb) 结合 asyncio 异步协程构建。实现了从底层引脚驱动到高层面向对象 (OOP) 的总线 VIP 封装。

特性列表 (Features)：

🚀 敏捷驱动： 完全基于 Python，天然支持海量数据处理与生态扩展。

🧩 模块化 VIP： 独立封装了 AMBA APB 与 AXI-Stream 总线的 Master/Slave 组件。

💥 极限边界测试： 自带带内背压机制 (In-band Backpressure) 的发生器，专门针对网络拥堵场景进行鲁棒性测试。

🛠️ 工具链全兼容： 通过定制 Makefile，无缝对接 Synopsys VCS 与 Verdi 工业级仿真流程。
