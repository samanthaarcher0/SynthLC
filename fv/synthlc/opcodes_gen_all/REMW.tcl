assume -name {i_REMW_0} {i0[31:25] == 7'b0000001}
assume -name {i_REMW_1} {i0[14:12] == 3'b110}
assume -name {i_REMW_2} {i0[11:7] != 5'd0}
assume -name {i_REMW_3} {i0[6:0] == 7'b0111011}
