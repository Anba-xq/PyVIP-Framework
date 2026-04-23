# --- 核心修改：指定仿真器为 vcs ---
SIM ?= vcs
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/axis_buffer.v
TOPLEVEL = axis_buffer
COCOTB_TEST_MODULES = test_axis

# --- VCS 专用参数 ---
# -full64: 开启 64 位仿真模式
# -debug_access+all: 极其重要！允许 Cocotb (通过 VPI) 读取和修改所有硬件信号
# +v2k: 支持 Verilog 2001 语法
COMPILE_ARGS += -full64 -debug_access+all +v2k +define+COCOTB_SIM

# 如果你的系统环境需要指定特定的编译参数，也可以加在这里
# SIM_ARGS += ...


# 引入 cocotb 仿真核心规则（必须放在最后）
include $(shell cocotb-config --makefiles)/Makefile.sim


# ==============================================
# Verdi 手动调用规则（默认不执行）
# ==============================================
verdi:
	verdi -sv $(VERILOG_SOURCES) -ssf $(TOPLEVEL).fsdb &
