assume -name {i_ECALL_0} {i0[31:20] == 12'b000000000000}
assume -name {i_ECALL_1} {i0[19:15] == 5'b00000}
assume -name {i_ECALL_2} {i0[14:12] == 3'b000}
assume -name {i_ECALL_3} {i0[11:7] == 5'b00000}
assume -name {i_ECALL_4} {i0[6:0] == 7'b1110011}
