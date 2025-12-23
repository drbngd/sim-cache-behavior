/*
 * Computer Architecture - Professor Onur Mutlu
 *
 * MIPS pipeline timing simulator
 *
 * Chris Fallin, 2012
 */

#include "processor.h"

Processor::Processor() {
    /* Initialize 4 Cores */
    for (int i = 0; i < 4; i++) {
        cores.push_back(std::make_unique<Core>(i, this));
    }
}

void Processor::cycle() {
    /* Tick all cores */
    for (int i = 0; i < 4; i++) {
        cores[i]->cycle();
    }
}

int Processor::active_cores_count() {
    int count = 0;
    for (int i = 0; i < 4; i++) {
        if (cores[i]->is_running) count++;
    }
    return count;
}
