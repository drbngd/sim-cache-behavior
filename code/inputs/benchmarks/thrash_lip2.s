# LIP/BIP vs LRU Test Benchmark (Fixed)
# Pattern: access working set MULTIPLE times to promote to MRU,
# then scan pollution, then re-access working set
# With LRU: pollution evicts working set
# With LIP: pollution stays at LRU, working set protected at MRU

.text
    lui $s0, 0x1000         # Working set base
    lui $s3, 0x1008         # Pollution stream base
    
    # First: warm up working set (2KB = 512 words)
    # Access multiple times to promote to MRU
    addiu $s5, $zero, 4     # 4 passes over working set
    
warmup_outer:
    addiu $s1, $zero, 512   # 2KB working set = 512 words
    move $t1, $s0
    
warmup_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s1, $s1, -1
    bne $s1, $zero, warmup_loop
    
    addiu $s5, $s5, -1
    bne $s5, $zero, warmup_outer
    
    # Now the working set should be promoted to MRU
    
    # Pollution scan (64KB, exactly cache size)
    # With LRU: this will evict the 2KB working set
    # With LIP: pollution enters at LRU, doesn't affect MRU working set
    addiu $s2, $zero, 16384  # 64KB = 16384 words
    move $t1, $s3
    
poll_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s2, $s2, -1
    bne $s2, $zero, poll_loop
    
    # Re-access working set
    # Should hit with LIP (working set at MRU), miss with LRU (evicted)
    addiu $s1, $zero, 512
    move $t1, $s0
    
reaccess_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s1, $s1, -1
    bne $s1, $zero, reaccess_loop
    
    # Exit
    addiu $v0, $zero, 10
    syscall

