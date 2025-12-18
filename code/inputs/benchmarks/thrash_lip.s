# LIP/BIP vs LRU Test Benchmark
# Pattern: repeatedly access working set, then scan pollution
# LRU will evict working set, LIP/BIP will keep it

.text
    lui $s0, 0x1000         # Working set base
    lui $s3, 0x1008         # Pollution stream base
    
    # Outer loop: 4 repetitions
    addiu $s4, $zero, 4
    
main_loop:
    # Phase 1: Access working set (16KB fits in 64KB cache)
    addiu $s1, $zero, 4096  # 16KB
    move $t1, $s0
    
ws_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s1, $s1, -1
    bne $s1, $zero, ws_loop
    
    # Phase 2: Pollution scan (128KB, larger than cache)
    # This is the "polluting" workload that shouldn't evict WS
    lui $s2, 0          
    ori $s2, $s2, 32768     # 128KB = 32768 words
    move $t1, $s3
    
poll_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s2, $s2, -1
    bne $s2, $zero, poll_loop
    
    # Phase 3: Re-access working set
    # Should hit with LIP, mostly miss with LRU
    addiu $s1, $zero, 4096
    move $t1, $s0
    
reaccess_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s1, $s1, -1
    bne $s1, $zero, reaccess_loop
    
    addiu $s4, $s4, -1
    bne $s4, $zero, main_loop
    
    # Exit
    addiu $v0, $zero, 10
    syscall

