assume -name {i_SLLI_0} {i0[31:26] == 6'b000000}
assume -name {i_SLLI_1} {i0[14:12] == 3'b001}
assume -name {i_SLLI_2} {i0[11:7] != 5'd0}
assume -name {i_SLLI_3} {i0[6:0] == 7'b0010011}
