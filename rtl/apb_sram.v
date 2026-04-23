// 文件名: apb_sram.v
module apb_sram (
    input  wire        PCLK,
    input  wire        PRESETn,
    input  wire        PSEL,
    input  wire        PENABLE,
    input  wire        PWRITE,
    input  wire [31:0] PADDR,
    input  wire [31:0] PWDATA,
    output reg  [31:0] PRDATA,
    output wire        PREADY
);

    // 定义一个深度为 16 的 32-bit 内存
    reg [31:0] mem [0:15];

    // 永远 ready
    assign PREADY = 1'b1;

    // APB 协议的核心逻辑
    // 只有在 PSEL(选中) 且 PENABLE(使能) 且 PREADY(就绪) 的时钟上升沿，才发生实际的数据交互
    wire apb_access = PSEL && PENABLE && PREADY;

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            PRDATA <= 32'h00000000;
        end else begin
            if (apb_access) begin
                if (PWRITE) begin
                    // 写操作：把地址低 4 位作为索引写入
                    mem[PADDR[3:0]] <= PWDATA;
                end else begin
                    // 读操作
                    PRDATA <= mem[PADDR[3:0]];
                end
            end
        end
    end

`ifdef COCOTB_SIM
    initial begin
        $fsdbDumpfile("apb_sram.fsdb");
        $fsdbDumpvars(0, apb_sram);
    end
`endif

endmodule
