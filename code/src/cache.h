#ifndef _CACHE_H_
#define _CACHE_H_

#include "shell.h"
#include <cstdint>
#include <stdint.h>

#define L1_CACHE_MISS_PENALTY 50
#define L1_CACHE_LINE_SIZE 32 /* 32 bytes */
#define I_CACHE_NUM_SETS 64
#define I_CACHE_ASSOC 4
#define D_CACHE_NUM_SETS 256
#define D_CACHE_ASSOC 8


typedef struct Cache_Line {

    uint32_t *data; /* pointer to data */
    uint32_t tag; /* tag */
    uint32_t valid; /* valid bit */
    uint32_t dirty; /* dirty bit */
    uint32 last_touch_tick; /* last touch tick */

} Cache_Line;


typedef struct Cache_Set {

    Cache_Line *lines; /* pointer to lines in the set */
    uint32_t LRU; /* least recently used line index */

} Cache_Set;


typedef struct Cache {

    Cache_Set *sets; /* pointer to sets in the cache */
    uint32_t num_sets; /* number of sets in the cache */
    uint32_t assoc; /* associativity */
    uint32_t line_size; /* line size */
    uint32_t miss_penalty; /* miss penalty */

    /* statistics */
    uint32_t read_misses;
    uint32_t write_misses;
    uint32_t read_hits;
    uint32_t write_hits;
    
} Cache;

/* global variable -- cache */
extern Cache i_cache;
extern Cache d_cache;

/* initialize the cache */
void cache_init(Cache *cache, int num_sets, int assoc, int line_size, int miss_penalty);

/* read from the cache */
uint32_t cache_read(Cache *cache, uint32_t address);

/* write to the cache */
uint32_t cache_write(Cache *cache, uint32_t address, uint32_t value);

/* helper function */
int log2_32(int n);

/* helper function */
uint32_t undo_little_endian(uint32_t data);

/* cache statistics */
extern uint32_t stat_i_cache_read_misses;
extern uint32_t stat_d_cache_read_misses;
extern uint32_t stat_i_cache_write_misses;
extern uint32_t stat_d_cache_write_misses;
extern uint32_t stat_i_cache_read_hits;
extern uint32_t stat_d_cache_read_hits;
extern uint32_t stat_i_cache_write_hits;
extern uint32_t stat_d_cache_write_hits;




#endif