#ifndef _MSHR_H_
#define _MSHR_H_

#include "config.h"
#include <cstdint>

struct MSHR {
    bool valid;
    bool done;
    uint32_t address;
    bool is_write;
    
    // Requester ID for callback
    int core_id;

    uint64_t ready_cycle;
};

#endif
