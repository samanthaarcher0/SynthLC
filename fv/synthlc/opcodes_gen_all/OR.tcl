assume -name {i_OR_0} {i0[31:25] == 7'b0000000}
assume -name {i_OR_1} {i0[14:12] == 3'b110}
assume -name {i_OR_2} {i0[11:7] != 5'd0}
assume -name {i_OR_3} {i0[6:0] == 7'b0110011}
