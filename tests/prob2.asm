db 1
db 2
db 4000000
db 2
db 2
loop:
    ld acc 0
    ld r7 1
    add acc r7
    sv acc 1
    sv r7 0
compare:
    ld br 2
    sub acc br
    jn test_odd
    jmp end
test_odd:
    ld r7 4
    ld acc 1
    mov br acc
    mod r7
    test dr
    jz sum
    jmp loop
sum:
    ld br 3
    ld acc 1
    add br acc
    sv br 3
    jmp loop
end:
    ld acc 3
    halt

