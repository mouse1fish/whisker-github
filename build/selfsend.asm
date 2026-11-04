Microsoft (R) COFF/PE Dumper Version 14.44.35222.0
Copyright (C) Microsoft Corporation.  All rights reserved.


Dump of file H:\trea-xiancheng-bianyiqi\build\selfsend.exe

File Type: EXECUTABLE IMAGE

  0000000140001000: 55                 push        rbp
  0000000140001001: 48 89 E5           mov         rbp,rsp
  0000000140001004: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  000000014000100B: 48 C7 C1 F5 FF FF  mov         rcx,0FFFFFFFFFFFFFFF5h
                    FF
  0000000140001012: FF 15 68 60 00 00  call        qword ptr [0000000140007080h]
  0000000140001018: 48 89 05 E1 1F 00  mov         qword ptr [0000000140003000h],rax
                    00
  000000014000101F: 48 8D 0D 0A 20 00  lea         rcx,[0000000140003030h]
                    00
  0000000140001026: FF 15 74 60 00 00  call        qword ptr [00000001400070A0h]
  000000014000102C: 48 8D 0D 05 20 00  lea         rcx,[0000000140003038h]
                    00
  0000000140001033: FF 15 5F 60 00 00  call        qword ptr [0000000140007098h]
  0000000140001039: 48 C7 C1 00 00 00  mov         rcx,0
                    00
  0000000140001040: 48 C7 C2 00 00 10  mov         rdx,100000h
                    00
  0000000140001047: 49 C7 C0 00 30 00  mov         r8,3000h
                    00
  000000014000104E: 49 C7 C1 04 00 00  mov         r9,4
                    00
  0000000140001055: FF 15 35 60 00 00  call        qword ptr [0000000140007090h]
  000000014000105B: 48 89 05 AE 1F 00  mov         qword ptr [0000000140003010h],rax
                    00
  0000000140001062: 48 89 C2           mov         rdx,rax
  0000000140001065: 48 81 C2 00 00 10  add         rdx,100000h
                    00
  000000014000106C: 48 89 15 A5 1F 00  mov         qword ptr [0000000140003018h],rdx
                    00
  0000000140001073: 48 89 EC           mov         rsp,rbp
  0000000140001076: 5D                 pop         rbp
  0000000140001077: C3                 ret
  0000000140001078: 55                 push        rbp
  0000000140001079: 48 89 E5           mov         rbp,rsp
  000000014000107C: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  0000000140001083: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  0000000140001088: 48 8B 05 81 1F 00  mov         rax,qword ptr [0000000140003010h]
                    00
  000000014000108F: 48 89 C2           mov         rdx,rax
  0000000140001092: 48 01 CA           add         rdx,rcx
  0000000140001095: 4C 8B 05 7C 1F 00  mov         r8,qword ptr [0000000140003018h]
                    00
  000000014000109C: 4C 39 C2           cmp         rdx,r8
  000000014000109F: 0F 86 4A 00 00 00  jbe         00000001400010EF
  00000001400010A5: 48 C7 C1 00 00 00  mov         rcx,0
                    00
  00000001400010AC: 48 C7 C2 00 00 10  mov         rdx,100000h
                    00
  00000001400010B3: 49 C7 C0 00 30 00  mov         r8,3000h
                    00
  00000001400010BA: 49 C7 C1 04 00 00  mov         r9,4
                    00
  00000001400010C1: FF 15 C9 5F 00 00  call        qword ptr [0000000140007090h]
  00000001400010C7: 48 89 C2           mov         rdx,rax
  00000001400010CA: 48 81 C2 00 00 10  add         rdx,100000h
                    00
  00000001400010D1: 48 89 15 40 1F 00  mov         qword ptr [0000000140003018h],rdx
                    00
  00000001400010D8: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  00000001400010DD: 48 89 C2           mov         rdx,rax
  00000001400010E0: 48 01 CA           add         rdx,rcx
  00000001400010E3: 48 89 15 26 1F 00  mov         qword ptr [0000000140003010h],rdx
                    00
  00000001400010EA: 48 89 EC           mov         rsp,rbp
  00000001400010ED: 5D                 pop         rbp
  00000001400010EE: C3                 ret
  00000001400010EF: 48 01 C8           add         rax,rcx
  00000001400010F2: 48 89 05 17 1F 00  mov         qword ptr [0000000140003010h],rax
                    00
  00000001400010F9: 48 89 D0           mov         rax,rdx
  00000001400010FC: 48 29 C8           sub         rax,rcx
  00000001400010FF: 48 89 EC           mov         rsp,rbp
  0000000140001102: 5D                 pop         rbp
  0000000140001103: C3                 ret
  0000000140001104: 55                 push        rbp
  0000000140001105: 48 89 E5           mov         rbp,rsp
  0000000140001108: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  000000014000110F: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  0000000140001114: 48 89 D1           mov         rcx,rdx
  0000000140001117: E8 5C FF FF FF     call        0000000140001078
  000000014000111C: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  0000000140001121: 48 89 48 00        mov         qword ptr [rax],rcx
  0000000140001125: 48 89 EC           mov         rsp,rbp
  0000000140001128: 5D                 pop         rbp
  0000000140001129: C3                 ret
  000000014000112A: 55                 push        rbp
  000000014000112B: 48 89 E5           mov         rbp,rsp
  000000014000112E: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  0000000140001135: 48 C7 42 08 00 00  mov         qword ptr [rdx+8],0
                    00 00
  000000014000113D: 48 8B 41 18        mov         rax,qword ptr [rcx+18h]
  0000000140001141: 48 85 C0           test        rax,rax
  0000000140001144: 0F 84 09 00 00 00  je          0000000140001153
  000000014000114A: 48 89 50 08        mov         qword ptr [rax+8],rdx
  000000014000114E: E9 04 00 00 00     jmp         0000000140001157
  0000000140001153: 48 89 51 10        mov         qword ptr [rcx+10h],rdx
  0000000140001157: 48 89 51 18        mov         qword ptr [rcx+18h],rdx
  000000014000115B: 48 8B 41 08        mov         rax,qword ptr [rcx+8]
  000000014000115F: 48 85 C0           test        rax,rax
  0000000140001162: 0F 85 37 00 00 00  jne         000000014000119F
  0000000140001168: 48 C7 41 08 01 00  mov         qword ptr [rcx+8],1
                    00 00
  0000000140001170: 48 8B 05 B1 1E 00  mov         rax,qword ptr [0000000140003028h]
                    00
  0000000140001177: 48 85 C0           test        rax,rax
  000000014000117A: 0F 84 09 00 00 00  je          0000000140001189
  0000000140001180: 48 89 48 20        mov         qword ptr [rax+20h],rcx
  0000000140001184: E9 07 00 00 00     jmp         0000000140001190
  0000000140001189: 48 89 0D 90 1E 00  mov         qword ptr [0000000140003020h],rcx
                    00
  0000000140001190: 48 89 0D 91 1E 00  mov         qword ptr [0000000140003028h],rcx
                    00
  0000000140001197: 48 C7 41 20 00 00  mov         qword ptr [rcx+20h],0
                    00 00
  000000014000119F: 48 89 EC           mov         rsp,rbp
  00000001400011A2: 5D                 pop         rbp
  00000001400011A3: C3                 ret
  00000001400011A4: 55                 push        rbp
  00000001400011A5: 48 89 E5           mov         rbp,rsp
  00000001400011A8: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  00000001400011AF: 48 8B 05 6A 1E 00  mov         rax,qword ptr [0000000140003020h]
                    00
  00000001400011B6: 48 85 C0           test        rax,rax
  00000001400011B9: 0F 84 BC 00 00 00  je          000000014000127B
  00000001400011BF: 48 8B 48 20        mov         rcx,qword ptr [rax+20h]
  00000001400011C3: 48 89 0D 56 1E 00  mov         qword ptr [0000000140003020h],rcx
                    00
  00000001400011CA: 48 85 C9           test        rcx,rcx
  00000001400011CD: 0F 85 0A 00 00 00  jne         00000001400011DD
  00000001400011D3: 48 31 D2           xor         rdx,rdx
  00000001400011D6: 48 89 15 4B 1E 00  mov         qword ptr [0000000140003028h],rdx
                    00
  00000001400011DD: 48 89 44 24 20     mov         qword ptr [rsp+20h],rax
  00000001400011E2: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  00000001400011E7: 48 8B 48 10        mov         rcx,qword ptr [rax+10h]
  00000001400011EB: 48 85 C9           test        rcx,rcx
  00000001400011EE: 0F 84 31 00 00 00  je          0000000140001225
  00000001400011F4: 48 8B 51 08        mov         rdx,qword ptr [rcx+8]
  00000001400011F8: 48 89 50 10        mov         qword ptr [rax+10h],rdx
  00000001400011FC: 48 85 D2           test        rdx,rdx
  00000001400011FF: 0F 85 08 00 00 00  jne         000000014000120D
  0000000140001205: 48 C7 40 18 00 00  mov         qword ptr [rax+18h],0
                    00 00
  000000014000120D: 48 89 4C 24 28     mov         qword ptr [rsp+28h],rcx
  0000000140001212: 48 89 CA           mov         rdx,rcx
  0000000140001215: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  000000014000121A: 48 8B 41 00        mov         rax,qword ptr [rcx]
  000000014000121E: FF D0              call        rax
  0000000140001220: E9 BD FF FF FF     jmp         00000001400011E2
  0000000140001225: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  000000014000122A: 48 C7 40 08 00 00  mov         qword ptr [rax+8],0
                    00 00
  0000000140001232: 48 8B 48 10        mov         rcx,qword ptr [rax+10h]
  0000000140001236: 48 85 C9           test        rcx,rcx
  0000000140001239: 0F 84 70 FF FF FF  je          00000001400011AF
  000000014000123F: 48 C7 40 08 01 00  mov         qword ptr [rax+8],1
                    00 00
  0000000140001247: 48 8B 15 DA 1D 00  mov         rdx,qword ptr [0000000140003028h]
                    00
  000000014000124E: 48 85 D2           test        rdx,rdx
  0000000140001251: 0F 84 09 00 00 00  je          0000000140001260
  0000000140001257: 48 89 42 20        mov         qword ptr [rdx+20h],rax
  000000014000125B: E9 07 00 00 00     jmp         0000000140001267
  0000000140001260: 48 89 05 B9 1D 00  mov         qword ptr [0000000140003020h],rax
                    00
  0000000140001267: 48 89 05 BA 1D 00  mov         qword ptr [0000000140003028h],rax
                    00
  000000014000126E: 48 C7 40 20 00 00  mov         qword ptr [rax+20h],0
                    00 00
  0000000140001276: E9 34 FF FF FF     jmp         00000001400011AF
  000000014000127B: 48 89 EC           mov         rsp,rbp
  000000014000127E: 5D                 pop         rbp
  000000014000127F: C3                 ret
  0000000140001280: 55                 push        rbp
  0000000140001281: 48 89 E5           mov         rbp,rsp
  0000000140001284: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  000000014000128B: 48 31 C0           xor         rax,rax
  000000014000128E: 48 89 05 73 1D 00  mov         qword ptr [0000000140003008h],rax
                    00
  0000000140001295: 48 89 EC           mov         rsp,rbp
  0000000140001298: 5D                 pop         rbp
  0000000140001299: C3                 ret
  000000014000129A: 55                 push        rbp
  000000014000129B: 48 89 E5           mov         rbp,rsp
  000000014000129E: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  00000001400012A5: 48 8B 3D 5C 1D 00  mov         rdi,qword ptr [0000000140003008h]
                    00
  00000001400012AC: 4C 8D 05 CD 1D 00  lea         r8,[0000000140003080h]
                    00
  00000001400012B3: 4C 01 C7           add         rdi,r8
  00000001400012B6: 48 89 CE           mov         rsi,rcx
  00000001400012B9: 48 89 D1           mov         rcx,rdx
  00000001400012BC: F3 A4              rep movs    byte ptr [rdi],byte ptr [rsi]
  00000001400012BE: 48 8B 05 43 1D 00  mov         rax,qword ptr [0000000140003008h]
                    00
  00000001400012C5: 48 01 D0           add         rax,rdx
  00000001400012C8: 48 89 05 39 1D 00  mov         qword ptr [0000000140003008h],rax
                    00
  00000001400012CF: 48 89 EC           mov         rsp,rbp
  00000001400012D2: 5D                 pop         rbp
  00000001400012D3: C3                 ret
  00000001400012D4: 55                 push        rbp
  00000001400012D5: 48 89 E5           mov         rbp,rsp
  00000001400012D8: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  00000001400012DF: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  00000001400012E4: 48 C7 C2 00 00 00  mov         rdx,0
                    00
  00000001400012EB: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  00000001400012F0: 48 01 D1           add         rcx,rdx
  00000001400012F3: 4C 0F B6 41 00     movzx       r8,byte ptr [rcx]
  00000001400012F8: 4D 85 C0           test        r8,r8
  00000001400012FB: 0F 84 09 00 00 00  je          000000014000130A
  0000000140001301: 48 83 C2 01        add         rdx,1
  0000000140001305: E9 E1 FF FF FF     jmp         00000001400012EB
  000000014000130A: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  000000014000130F: E8 86 FF FF FF     call        000000014000129A
  0000000140001314: 48 89 EC           mov         rsp,rbp
  0000000140001317: 5D                 pop         rbp
  0000000140001318: C3                 ret
  0000000140001319: 55                 push        rbp
  000000014000131A: 48 89 E5           mov         rbp,rsp
  000000014000131D: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  0000000140001324: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  0000000140001329: 48 85 C9           test        rcx,rcx
  000000014000132C: 0F 89 20 00 00 00  jns         0000000140001352
  0000000140001332: 48 8D 0D C8 0C 00  lea         rcx,[0000000140002001h]
                    00
  0000000140001339: 48 C7 C2 01 00 00  mov         rdx,1
                    00
  0000000140001340: E8 55 FF FF FF     call        000000014000129A
  0000000140001345: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  000000014000134A: 48 F7 D8           neg         rax
  000000014000134D: 48 89 44 24 20     mov         qword ptr [rsp+20h],rax
  0000000140001352: 4C 8D 05 FF 1C 00  lea         r8,[0000000140003058h]
                    00
  0000000140001359: 49 83 C0 20        add         r8,20h
  000000014000135D: 49 C7 C1 00 00 00  mov         r9,0
                    00
  0000000140001364: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  0000000140001369: 48 85 C0           test        rax,rax
  000000014000136C: 0F 85 1B 00 00 00  jne         000000014000138D
  0000000140001372: 49 83 E8 01        sub         r8,1
  0000000140001376: 48 C7 C2 30 00 00  mov         rdx,30h
                    00
  000000014000137D: 41 88 50 00        mov         byte ptr [r8],dl
  0000000140001381: 49 C7 C1 01 00 00  mov         r9,1
                    00
  0000000140001388: E9 26 00 00 00     jmp         00000001400013B3
  000000014000138D: 48 31 D2           xor         rdx,rdx
  0000000140001390: 49 C7 C2 0A 00 00  mov         r10,0Ah
                    00
  0000000140001397: 49 F7 F2           div         rax,r10
  000000014000139A: 48 83 C2 30        add         rdx,30h
  000000014000139E: 49 83 E8 01        sub         r8,1
  00000001400013A2: 41 88 50 00        mov         byte ptr [r8],dl
  00000001400013A6: 49 83 C1 01        add         r9,1
  00000001400013AA: 48 85 C0           test        rax,rax
  00000001400013AD: 0F 85 DA FF FF FF  jne         000000014000138D
  00000001400013B3: 4C 89 C1           mov         rcx,r8
  00000001400013B6: 4C 89 CA           mov         rdx,r9
  00000001400013B9: E8 DC FE FF FF     call        000000014000129A
  00000001400013BE: 48 89 EC           mov         rsp,rbp
  00000001400013C1: 5D                 pop         rbp
  00000001400013C2: C3                 ret
  00000001400013C3: 55                 push        rbp
  00000001400013C4: 48 89 E5           mov         rbp,rsp
  00000001400013C7: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  00000001400013CE: 48 85 C9           test        rcx,rcx
  00000001400013D1: 0F 84 18 00 00 00  je          00000001400013EF
  00000001400013D7: 48 8D 0D 24 0C 00  lea         rcx,[0000000140002002h]
                    00
  00000001400013DE: 48 C7 C2 04 00 00  mov         rdx,4
                    00
  00000001400013E5: E8 B0 FE FF FF     call        000000014000129A
  00000001400013EA: 48 89 EC           mov         rsp,rbp
  00000001400013ED: 5D                 pop         rbp
  00000001400013EE: C3                 ret
  00000001400013EF: 48 8D 0D 10 0C 00  lea         rcx,[0000000140002006h]
                    00
  00000001400013F6: 48 C7 C2 05 00 00  mov         rdx,5
                    00
  00000001400013FD: E8 98 FE FF FF     call        000000014000129A
  0000000140001402: 48 89 EC           mov         rsp,rbp
  0000000140001405: 5D                 pop         rbp
  0000000140001406: C3                 ret
  0000000140001407: 55                 push        rbp
  0000000140001408: 48 89 E5           mov         rbp,rsp
  000000014000140B: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  0000000140001412: 48 8D 0D E7 0B 00  lea         rcx,[0000000140002000h]
                    00
  0000000140001419: 48 C7 C2 01 00 00  mov         rdx,1
                    00
  0000000140001420: E8 75 FE FF FF     call        000000014000129A
  0000000140001425: 48 8B 0D D4 1B 00  mov         rcx,qword ptr [0000000140003000h]
                    00
  000000014000142C: 48 8D 15 4D 1C 00  lea         rdx,[0000000140003080h]
                    00
  0000000140001433: 4C 8B 05 CE 1B 00  mov         r8,qword ptr [0000000140003008h]
                    00
  000000014000143A: 4C 8D 0D 07 1C 00  lea         r9,[0000000140003048h]
                    00
  0000000140001441: 48 C7 44 24 20 00  mov         qword ptr [rsp+20h],0
                    00 00 00
  000000014000144A: FF 15 38 5C 00 00  call        qword ptr [0000000140007088h]
  0000000140001450: 48 89 EC           mov         rsp,rbp
  0000000140001453: 5D                 pop         rbp
  0000000140001454: C3                 ret
  0000000140001455: 55                 push        rbp
  0000000140001456: 48 89 E5           mov         rbp,rsp
  0000000140001459: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  0000000140001460: 48 8D 0D D9 1B 00  lea         rcx,[0000000140003040h]
                    00
  0000000140001467: FF 15 2B 5C 00 00  call        qword ptr [0000000140007098h]
  000000014000146D: 48 8B 05 CC 1B 00  mov         rax,qword ptr [0000000140003040h]
                    00
  0000000140001474: 48 8B 0D BD 1B 00  mov         rcx,qword ptr [0000000140003038h]
                    00
  000000014000147B: 48 29 C8           sub         rax,rcx
  000000014000147E: 48 C7 C1 E8 03 00  mov         rcx,3E8h
                    00
  0000000140001485: 48 F7 E1           mul         rax,rcx
  0000000140001488: 48 8B 0D A1 1B 00  mov         rcx,qword ptr [0000000140003030h]
                    00
  000000014000148F: 48 F7 F1           div         rax,rcx
  0000000140001492: 48 89 EC           mov         rsp,rbp
  0000000140001495: 5D                 pop         rbp
  0000000140001496: C3                 ret
  0000000140001497: 55                 push        rbp
  0000000140001498: 48 89 E5           mov         rbp,rsp
  000000014000149B: 48 81 EC 20 00 00  sub         rsp,20h
                    00
  00000001400014A2: 48 0F B6 41 00     movzx       rax,byte ptr [rcx]
  00000001400014A7: 4C 0F B6 42 00     movzx       r8,byte ptr [rdx]
  00000001400014AC: 4C 39 C0           cmp         rax,r8
  00000001400014AF: 0F 85 16 00 00 00  jne         00000001400014CB
  00000001400014B5: 48 85 C0           test        rax,rax
  00000001400014B8: 0F 84 15 00 00 00  je          00000001400014D3
  00000001400014BE: 48 83 C1 01        add         rcx,1
  00000001400014C2: 48 83 C2 01        add         rdx,1
  00000001400014C6: E9 D7 FF FF FF     jmp         00000001400014A2
  00000001400014CB: 48 31 C0           xor         rax,rax
  00000001400014CE: 48 89 EC           mov         rsp,rbp
  00000001400014D1: 5D                 pop         rbp
  00000001400014D2: C3                 ret
  00000001400014D3: 48 C7 C0 01 00 00  mov         rax,1
                    00
  00000001400014DA: 48 89 EC           mov         rsp,rbp
  00000001400014DD: 5D                 pop         rbp
  00000001400014DE: C3                 ret
  00000001400014DF: 55                 push        rbp
  00000001400014E0: 48 89 E5           mov         rbp,rsp
  00000001400014E3: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  00000001400014EA: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  00000001400014EF: 48 C7 C1 20 00 00  mov         rcx,20h
                    00
  00000001400014F6: E8 7D FB FF FF     call        0000000140001078
  00000001400014FB: 48 89 44 24 28     mov         qword ptr [rsp+28h],rax
  0000000140001500: 48 C7 40 00 02 00  mov         qword ptr [rax],2
                    00 00
  0000000140001508: 48 C7 40 08 00 00  mov         qword ptr [rax+8],0
                    00 00
  0000000140001510: 48 C7 C0 01 00 00  mov         rax,1
                    00
  0000000140001517: 48 8B 54 24 28     mov         rdx,qword ptr [rsp+28h]
  000000014000151C: 48 89 42 10        mov         qword ptr [rdx+10h],rax
  0000000140001520: 48 C7 C0 64 00 00  mov         rax,64h
                    00
  0000000140001527: 48 8B 54 24 28     mov         rdx,qword ptr [rsp+28h]
  000000014000152C: 48 89 42 18        mov         qword ptr [rdx+18h],rax
  0000000140001530: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  0000000140001535: 48 8B 54 24 28     mov         rdx,qword ptr [rsp+28h]
  000000014000153A: 48 89 C1           mov         rcx,rax
  000000014000153D: E8 E8 FB FF FF     call        000000014000112A
  0000000140001542: 48 89 EC           mov         rsp,rbp
  0000000140001545: 5D                 pop         rbp
  0000000140001546: C3                 ret
  0000000140001547: 55                 push        rbp
  0000000140001548: 48 89 E5           mov         rbp,rsp
  000000014000154B: 48 81 EC 60 00 00  sub         rsp,60h
                    00
  0000000140001552: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  0000000140001557: 48 89 54 24 28     mov         qword ptr [rsp+28h],rdx
  000000014000155C: 4C 89 44 24 30     mov         qword ptr [rsp+30h],r8
  0000000140001561: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  0000000140001566: 48 8B 40 30        mov         rax,qword ptr [rax+30h]
  000000014000156A: 48 89 44 24 38     mov         qword ptr [rsp+38h],rax
  000000014000156F: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  0000000140001574: 48 89 C2           mov         rdx,rax
  0000000140001577: 48 8B 44 24 38     mov         rax,qword ptr [rsp+38h]
  000000014000157C: 48 01 D0           add         rax,rdx
  000000014000157F: 48 8B 54 24 20     mov         rdx,qword ptr [rsp+20h]
  0000000140001584: 48 89 42 30        mov         qword ptr [rdx+30h],rax
  0000000140001588: 48 8B 44 24 30     mov         rax,qword ptr [rsp+30h]
  000000014000158D: 48 89 44 24 40     mov         qword ptr [rsp+40h],rax
  0000000140001592: 48 C7 C0 00 00 00  mov         rax,0
                    00
  0000000140001599: 48 89 C2           mov         rdx,rax
  000000014000159C: 48 8B 44 24 40     mov         rax,qword ptr [rsp+40h]
  00000001400015A1: 48 39 D0           cmp         rax,rdx
  00000001400015A4: 0F 9F C0           setg        al
  00000001400015A7: 0F B6 C0           movzx       eax,al
  00000001400015AA: 48 85 C0           test        rax,rax
  00000001400015AD: 0F 84 82 00 00 00  je          0000000140001635
  00000001400015B3: 48 C7 C1 20 00 00  mov         rcx,20h
                    00
  00000001400015BA: E8 B9 FA FF FF     call        0000000140001078
  00000001400015BF: 48 89 44 24 48     mov         qword ptr [rsp+48h],rax
  00000001400015C4: 48 C7 40 00 02 00  mov         qword ptr [rax],2
                    00 00
  00000001400015CC: 48 C7 40 08 00 00  mov         qword ptr [rax+8],0
                    00 00
  00000001400015D4: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  00000001400015D9: 48 89 44 24 50     mov         qword ptr [rsp+50h],rax
  00000001400015DE: 48 C7 C0 01 00 00  mov         rax,1
                    00
  00000001400015E5: 48 89 C2           mov         rdx,rax
  00000001400015E8: 48 8B 44 24 50     mov         rax,qword ptr [rsp+50h]
  00000001400015ED: 48 01 D0           add         rax,rdx
  00000001400015F0: 48 8B 54 24 48     mov         rdx,qword ptr [rsp+48h]
  00000001400015F5: 48 89 42 10        mov         qword ptr [rdx+10h],rax
  00000001400015F9: 48 8B 44 24 30     mov         rax,qword ptr [rsp+30h]
  00000001400015FE: 48 89 44 24 58     mov         qword ptr [rsp+58h],rax
  0000000140001603: 48 C7 C0 01 00 00  mov         rax,1
                    00
  000000014000160A: 48 89 C2           mov         rdx,rax
  000000014000160D: 48 8B 44 24 58     mov         rax,qword ptr [rsp+58h]
  0000000140001612: 48 29 D0           sub         rax,rdx
  0000000140001615: 48 8B 54 24 48     mov         rdx,qword ptr [rsp+48h]
  000000014000161A: 48 89 42 18        mov         qword ptr [rdx+18h],rax
  000000014000161E: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  0000000140001623: 48 8B 54 24 48     mov         rdx,qword ptr [rsp+48h]
  0000000140001628: 48 89 C1           mov         rcx,rax
  000000014000162B: E8 FA FA FF FF     call        000000014000112A
  0000000140001630: E9 2A 00 00 00     jmp         000000014000165F
  0000000140001635: E8 46 FC FF FF     call        0000000140001280
  000000014000163A: 48 8D 05 CA 09 00  lea         rax,[000000014000200Bh]
                    00
  0000000140001641: 48 89 C1           mov         rcx,rax
  0000000140001644: E8 8B FC FF FF     call        00000001400012D4
  0000000140001649: 48 8B 44 24 20     mov         rax,qword ptr [rsp+20h]
  000000014000164E: 48 8B 40 30        mov         rax,qword ptr [rax+30h]
  0000000140001652: 48 89 C1           mov         rcx,rax
  0000000140001655: E8 BF FC FF FF     call        0000000140001319
  000000014000165A: E8 A8 FD FF FF     call        0000000140001407
  000000014000165F: 48 89 EC           mov         rsp,rbp
  0000000140001662: 5D                 pop         rbp
  0000000140001663: C3                 ret
  0000000140001664: 55                 push        rbp
  0000000140001665: 48 89 E5           mov         rbp,rsp
  0000000140001668: 48 81 EC 30 00 00  sub         rsp,30h
                    00
  000000014000166F: 48 89 4C 24 20     mov         qword ptr [rsp+20h],rcx
  0000000140001674: 48 89 54 24 28     mov         qword ptr [rsp+28h],rdx
  0000000140001679: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  000000014000167E: 48 8B 40 00        mov         rax,qword ptr [rax]
  0000000140001682: 48 83 F8 01        cmp         rax,1
  0000000140001686: 0F 84 18 00 00 00  je          00000001400016A4
  000000014000168C: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  0000000140001691: 48 8B 40 00        mov         rax,qword ptr [rax]
  0000000140001695: 48 83 F8 02        cmp         rax,2
  0000000140001699: 0F 84 14 00 00 00  je          00000001400016B3
  000000014000169F: E9 30 00 00 00     jmp         00000001400016D4
  00000001400016A4: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  00000001400016A9: E8 3C FE FF FF     call        00000001400014EA
  00000001400016AE: E9 21 00 00 00     jmp         00000001400016D4
  00000001400016B3: 48 8B 4C 24 20     mov         rcx,qword ptr [rsp+20h]
  00000001400016B8: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  00000001400016BD: 48 8B 50 10        mov         rdx,qword ptr [rax+10h]
  00000001400016C1: 48 8B 44 24 28     mov         rax,qword ptr [rsp+28h]
  00000001400016C6: 4C 8B 40 18        mov         r8,qword ptr [rax+18h]
  00000001400016CA: E8 83 FE FF FF     call        0000000140001552
  00000001400016CF: E9 00 00 00 00     jmp         00000001400016D4
  00000001400016D4: 48 89 EC           mov         rsp,rbp
  00000001400016D7: 5D                 pop         rbp
  00000001400016D8: C3                 ret
  00000001400016D9: E8 22 F9 FF FF     call        0000000140001000
  00000001400016DE: 48 8D 0D 7F FF FF  lea         rcx,[0000000140001664h]
                    FF
  00000001400016E5: 48 C7 C2 40 00 00  mov         rdx,40h
                    00
  00000001400016EC: E8 13 FA FF FF     call        0000000140001104
  00000001400016F1: 48 89 05 58 19 00  mov         qword ptr [0000000140003050h],rax
                    00
  00000001400016F8: 48 C7 40 30 00 00  mov         qword ptr [rax+30h],0
                    00 00
  0000000140001700: 48 C7 C1 10 00 00  mov         rcx,10h
                    00
  0000000140001707: E8 6C F9 FF FF     call        0000000140001078
  000000014000170C: 48 C7 40 00 01 00  mov         qword ptr [rax],1
                    00 00
  0000000140001714: 48 C7 40 08 00 00  mov         qword ptr [rax+8],0
                    00 00
  000000014000171C: 48 89 C2           mov         rdx,rax
  000000014000171F: 48 8B 0D 2A 19 00  mov         rcx,qword ptr [0000000140003050h]
                    00
  0000000140001726: E8 FF F9 FF FF     call        000000014000112A
  000000014000172B: E8 74 FA FF FF     call        00000001400011A4
  0000000140001730: C3                 ret
  0000000140001731: 00 00              add         byte ptr [rax],al
  0000000140001733: 00 00              add         byte ptr [rax],al
  0000000140001735: 00 00              add         byte ptr [rax],al
  0000000140001737: 00 00              add         byte ptr [rax],al
  0000000140001739: 00 00              add         byte ptr [rax],al
  000000014000173B: 00 00              add         byte ptr [rax],al
  000000014000173D: 00 00              add         byte ptr [rax],al
  000000014000173F: 00 00              add         byte ptr [rax],al
  0000000140001741: 00 00              add         byte ptr [rax],al
  0000000140001743: 00 00              add         byte ptr [rax],al
  0000000140001745: 00 00              add         byte ptr [rax],al
  0000000140001747: 00 00              add         byte ptr [rax],al
  0000000140001749: 00 00              add         byte ptr [rax],al
  000000014000174B: 00 00              add         byte ptr [rax],al
  000000014000174D: 00 00              add         byte ptr [rax],al
  000000014000174F: 00 00              add         byte ptr [rax],al
  0000000140001751: 00 00              add         byte ptr [rax],al
  0000000140001753: 00 00              add         byte ptr [rax],al
  0000000140001755: 00 00              add         byte ptr [rax],al
  0000000140001757: 00 00              add         byte ptr [rax],al
  0000000140001759: 00 00              add         byte ptr [rax],al
  000000014000175B: 00 00              add         byte ptr [rax],al
  000000014000175D: 00 00              add         byte ptr [rax],al
  000000014000175F: 00 00              add         byte ptr [rax],al
  0000000140001761: 00 00              add         byte ptr [rax],al
  0000000140001763: 00 00              add         byte ptr [rax],al
  0000000140001765: 00 00              add         byte ptr [rax],al
  0000000140001767: 00 00              add         byte ptr [rax],al
  0000000140001769: 00 00              add         byte ptr [rax],al
  000000014000176B: 00 00              add         byte ptr [rax],al
  000000014000176D: 00 00              add         byte ptr [rax],al
  000000014000176F: 00 00              add         byte ptr [rax],al
  0000000140001771: 00 00              add         byte ptr [rax],al
  0000000140001773: 00 00              add         byte ptr [rax],al
  0000000140001775: 00 00              add         byte ptr [rax],al
  0000000140001777: 00 00              add         byte ptr [rax],al
  0000000140001779: 00 00              add         byte ptr [rax],al
  000000014000177B: 00 00              add         byte ptr [rax],al
  000000014000177D: 00 00              add         byte ptr [rax],al
  000000014000177F: 00 00              add         byte ptr [rax],al
  0000000140001781: 00 00              add         byte ptr [rax],al
  0000000140001783: 00 00              add         byte ptr [rax],al
  0000000140001785: 00 00              add         byte ptr [rax],al
  0000000140001787: 00 00              add         byte ptr [rax],al
  0000000140001789: 00 00              add         byte ptr [rax],al
  000000014000178B: 00 00              add         byte ptr [rax],al
  000000014000178D: 00 00              add         byte ptr [rax],al
  000000014000178F: 00 00              add         byte ptr [rax],al
  0000000140001791: 00 00              add         byte ptr [rax],al
  0000000140001793: 00 00              add         byte ptr [rax],al
  0000000140001795: 00 00              add         byte ptr [rax],al
  0000000140001797: 00 00              add         byte ptr [rax],al
  0000000140001799: 00 00              add         byte ptr [rax],al
  000000014000179B: 00 00              add         byte ptr [rax],al
  000000014000179D: 00 00              add         byte ptr [rax],al
  000000014000179F: 00 00              add         byte ptr [rax],al
  00000001400017A1: 00 00              add         byte ptr [rax],al
  00000001400017A3: 00 00              add         byte ptr [rax],al
  00000001400017A5: 00 00              add         byte ptr [rax],al
  00000001400017A7: 00 00              add         byte ptr [rax],al
  00000001400017A9: 00 00              add         byte ptr [rax],al
  00000001400017AB: 00 00              add         byte ptr [rax],al
  00000001400017AD: 00 00              add         byte ptr [rax],al
  00000001400017AF: 00 00              add         byte ptr [rax],al
  00000001400017B1: 00 00              add         byte ptr [rax],al
  00000001400017B3: 00 00              add         byte ptr [rax],al
  00000001400017B5: 00 00              add         byte ptr [rax],al
  00000001400017B7: 00 00              add         byte ptr [rax],al
  00000001400017B9: 00 00              add         byte ptr [rax],al
  00000001400017BB: 00 00              add         byte ptr [rax],al
  00000001400017BD: 00 00              add         byte ptr [rax],al
  00000001400017BF: 00 00              add         byte ptr [rax],al
  00000001400017C1: 00 00              add         byte ptr [rax],al
  00000001400017C3: 00 00              add         byte ptr [rax],al
  00000001400017C5: 00 00              add         byte ptr [rax],al
  00000001400017C7: 00 00              add         byte ptr [rax],al
  00000001400017C9: 00 00              add         byte ptr [rax],al
  00000001400017CB: 00 00              add         byte ptr [rax],al
  00000001400017CD: 00 00              add         byte ptr [rax],al
  00000001400017CF: 00 00              add         byte ptr [rax],al
  00000001400017D1: 00 00              add         byte ptr [rax],al
  00000001400017D3: 00 00              add         byte ptr [rax],al
  00000001400017D5: 00 00              add         byte ptr [rax],al
  00000001400017D7: 00 00              add         byte ptr [rax],al
  00000001400017D9: 00 00              add         byte ptr [rax],al
  00000001400017DB: 00 00              add         byte ptr [rax],al
  00000001400017DD: 00 00              add         byte ptr [rax],al
  00000001400017DF: 00 00              add         byte ptr [rax],al
  00000001400017E1: 00 00              add         byte ptr [rax],al
  00000001400017E3: 00 00              add         byte ptr [rax],al
  00000001400017E5: 00 00              add         byte ptr [rax],al
  00000001400017E7: 00 00              add         byte ptr [rax],al
  00000001400017E9: 00 00              add         byte ptr [rax],al
  00000001400017EB: 00 00              add         byte ptr [rax],al
  00000001400017ED: 00 00              add         byte ptr [rax],al
  00000001400017EF: 00 00              add         byte ptr [rax],al
  00000001400017F1: 00 00              add         byte ptr [rax],al
  00000001400017F3: 00 00              add         byte ptr [rax],al
  00000001400017F5: 00 00              add         byte ptr [rax],al
  00000001400017F7: 00 00              add         byte ptr [rax],al
  00000001400017F9: 00 00              add         byte ptr [rax],al
  00000001400017FB: 00 00              add         byte ptr [rax],al
  00000001400017FD: 00 00              add         byte ptr [rax],al
  00000001400017FF: 00

  Summary

        5000 .data
        1000 .rdata
        1000 .text
