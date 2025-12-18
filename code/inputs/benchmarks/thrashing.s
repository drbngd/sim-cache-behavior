# Thrashing Benchmark  
# Designed to cause cache thrashing by accessing more sets than available
# This specifically tests LRU vs LIP/BIP policies
# Access pattern: scan through working set, then access a "polluting" stream

.text
    # Setup base addresses
    lui $s0, 0x1000         # Main working set base
    lui $s3, 0x1002         # Polluting stream base (different region)
    
    # Outer loop: repeat 8 times
    addiu $s4, $zero, 8
    
main_loop:
    # Phase 1: Access main working set (fits in cache)
    # 8192 words = 32KB, fits in 64KB D-cache
    addiu $s1, $zero, 8192
    move $t1, $s0
    
working_set_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s1, $s1, -1
    bne $s1, $zero, working_set_loop
    
    # Phase 2: Polluting scan (larger than cache, single pass)
    # This should evict the working set with LRU
    # With LIP/BIP, polluting stream doesn't evict working set
    addiu $s2, $zero, 16384  # 64KB polluting scan
    move $t1, $s3
    
pollute_loop:
    lw $t2, 0($t1)
    addiu $t1, $t1, 4
    addiu $s2, $s2, -1
    bne $s2, $zero, pollute_loop
    
    # Phase 3: Re-access working set (should hit with LIP, miss with LRU)
    addiu $s1, $zero, 8192
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

