// 文件名: sync_fifo.v
module sync_fifo (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       wr_en,    // 写使能
    input  wire [7:0] wr_data,  // 写数据
    input  wire       rd_en,    // 读使能
    output reg  [7:0] rd_data,  // 读数据
    output wire       full,     // 写满标志
    output wire       empty     // 读空标志
);

    parameter DEPTH = 16;
    reg [7:0] mem [0:DEPTH-1];
    reg [4:0] wr_ptr;
    reg [4:0] rd_ptr;

    // 满和空的判断逻辑 (最高位不同但其余位相同则为满，全部相同则为空)
    assign full  = (wr_ptr[4] != rd_ptr[4]) && (wr_ptr[3:0] == rd_ptr[3:0]);
    assign empty = (wr_ptr == rd_ptr);

    // 写逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr[3:0]] <= wr_data;
            wr_ptr <= wr_ptr + 1;
        end
    end

    // 读逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= 0;
            rd_data <= 0;
        end else if (rd_en && !empty) begin
            rd_data <= mem[rd_ptr[3:0]];
            rd_ptr <= rd_ptr + 1;
        end
    end

`ifdef COCOTB_SIM
    initial begin
        $fsdbDumpfile("sync_fifo.fsdb");
        $fsdbDumpvars(0, sync_fifo);
    end
`endif

endmodule
