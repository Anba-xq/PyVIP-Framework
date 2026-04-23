// 文件名: axis_buffer.v
module axis_buffer (
    input  wire        clk,
    input  wire        rst_n,

    // AXI-Stream Slave 接口 (接收数据)
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    input  wire [31:0] s_axis_tdata,

    // AXI-Stream Master 接口 (发送数据)
    output reg         m_axis_tvalid,
    input  wire        m_axis_tready,
    output reg  [31:0] m_axis_tdata
);

    // 接收端 Ready 逻辑：只要输出端是空的，或者输出端的数据马上要被读走，我就可以接收新数据
    assign s_axis_tready = !m_axis_tvalid || m_axis_tready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axis_tvalid <= 1'b0;
            m_axis_tdata  <= 32'b0;
        end else begin
            // 握手成功：接收端拿到数据，存到输出寄存器，并拉高输出 Valid
            if (s_axis_tvalid && s_axis_tready) begin
                m_axis_tvalid <= 1'b1;
                m_axis_tdata  <= s_axis_tdata;
            end
            // 握手成功：输出端数据被读走，且没有新数据进来，拉低输出 Valid
            else if (m_axis_tready && m_axis_tvalid) begin
                m_axis_tvalid <= 1'b0;
            end
        end
    end

`ifdef COCOTB_SIM
    initial begin
        $fsdbDumpfile("axis_buffer.fsdb");
        $fsdbDumpvars(0, axis_buffer);
    end
`endif

endmodule
