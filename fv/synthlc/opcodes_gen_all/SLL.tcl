assume -name {i_SLL_0} {i0[31:25] == 7'b0000000}
assume -name {i_SLL_1} {i0[14:12] == 3'b001}
assume -name {i_SLL_2} {i0[11:7] != 5'd0}
assume -name {i_SLL_3} {i0[6:0] == 7'b0110011}
