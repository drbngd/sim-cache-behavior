#include "cache.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Cache Statistics */
uint32_t stat_i_cache_read_misses = 0;
uint32_t stat_d_cache_read_misses = 0;
uint32_t stat_i_cache_write_misses = 0;
uint32_t stat_d_cache_write_misses = 0;
uint32_t stat_i_cache_read_hits = 0;
uint32_t stat_d_cache_read_hits = 0;
uint32_t stat_i_cache_write_hits = 0;
uint32_t stat_d_cache_write_hits = 0;




/* global variable -- cache */
Cache i_cache;
Cache d_cache;



int log2_32(int n) {

    if ( n == 0 ) return -1;

    return 31 - __builtin_clz(n);
    
}


uint32_t undo_little_endian(uint32_t data) {
    return ((data & 0xFF000000) >> 24) |
            ((data & 0x00FF0000) >> 8) |
            ((data & 0x0000FF00) << 8) |
            ((data & 0x000000FF) << 24);
}



void cache_init(Cache *cache, int num_sets, int assoc, int line_size, int miss_penalty) {

    memset(cache, 0, sizeof(Cache));

    cache->sets = (Cache_Set*)calloc(num_sets, sizeof(Cache_Set));

    for (int i = 0; i < num_sets; i++) {
        cache->sets[i].lines = (Cache_Line*)calloc(assoc, sizeof(Cache_Line));
        for (int j = 0; j < assoc; j++) {
            cache->sets[i].lines[j].data = (uint32_t*)calloc((int)(line_size / 4), sizeof(uint32_t));
            cache->sets[i].lines[j].tag = 0;
            cache->sets[i].lines[j].valid = 0;
            cache->sets[i].lines[j].dirty = 0;
        }
    }

    cache->num_sets = num_sets;
    cache->assoc =  assoc;
    cache->line_size = line_size;
    cache->miss_penalty = miss_penalty;

}

uint32_t cache_read(Cache *cache, uint32_t address) {

    uint32_t offset = address & (cache->line_size - 1);
    uint32_t set_index = (address >> (int)log2_32(cache->line_size)) & (cache->num_sets - 1);
    uint32_t tag = address >> (log2_32(cache->line_size) + log2_32(cache->num_sets));

    for (int i = 0; i < cache->assoc; i++) {
        if (cache->sets[set_index].lines[i].valid && cache->sets[set_index].lines[i].tag == tag) {
            cache->read_hits++;

            // TODO: LRU Logic

            return undo_little_endian(cache->sets[set_index].lines[i].data[offset]);
        } else {
            cache->read_misses++;
            uint32_t data = mem_read_32(address);
        }
    }

    
}

void cache_write(Cache *cache, uint32_t address, uint32_t value) {
    uint32_t offset = address & (cache->line_size - 1);
    uint32_t set_index = (address >> (int)log2_32(cache->line_size)) & (cache->num_sets - 1);
    uint32_t tag = address >> (log2_32(cache->line_size) + log2_32(cache->num_sets));

    for (int i = 0; i < cache->assoc; i++) {
        if (cache->sets[set_index].lines[i].valid && cache->sets[set_index].lines[i].tag == tag) {
            cache->write_hits++;
        } else {
            cache->write_misses++;
        }
    }
}