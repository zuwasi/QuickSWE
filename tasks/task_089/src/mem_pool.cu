#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define POOL_SIZE (1 << 20)  /* 1MB pool */
#define ALIGNMENT 256
#define HEADER_SIZE 16

/* ------------------------------------------------------------------ */
/* Block header in the pool                                            */
/* ------------------------------------------------------------------ */
typedef struct BlockHeader {
    int size;        /* payload size (excluding header) */
    int is_free;
    int next_offset; /* offset of next block from pool start, -1 if last */
    int pad;
} BlockHeader;

/* ------------------------------------------------------------------ */
/* CPU reference allocator (DO NOT MODIFY)                            */
/* ------------------------------------------------------------------ */
typedef struct {
    char *pool;
    int pool_size;
} CPUPool;

void cpu_pool_init(CPUPool *p) {
    p->pool = (char *)calloc(POOL_SIZE, 1);
    p->pool_size = POOL_SIZE;
    BlockHeader *h = (BlockHeader *)p->pool;
    h->size = POOL_SIZE - HEADER_SIZE;
    h->is_free = 1;
    h->next_offset = -1;
}

int cpu_pool_alloc(CPUPool *p, int size) {
    size = ((size + ALIGNMENT - 1) / ALIGNMENT) * ALIGNMENT;
    int offset = 0;
    while (offset >= 0 && offset < p->pool_size) {
        BlockHeader *h = (BlockHeader *)(p->pool + offset);
        if (h->is_free && h->size >= size) {
            if (h->size >= size + HEADER_SIZE + ALIGNMENT) {
                int new_offset = offset + HEADER_SIZE + size;
                BlockHeader *nh = (BlockHeader *)(p->pool + new_offset);
                nh->size = h->size - size - HEADER_SIZE;
                nh->is_free = 1;
                nh->next_offset = h->next_offset;
                h->next_offset = new_offset;
                h->size = size;
            }
            h->is_free = 0;
            return offset + HEADER_SIZE;
        }
        offset = h->next_offset;
    }
    return -1;
}

void cpu_pool_free(CPUPool *p, int data_offset) {
    int offset = data_offset - HEADER_SIZE;
    BlockHeader *h = (BlockHeader *)(p->pool + offset);
    h->is_free = 1;

    /* Coalesce with next block */
    if (h->next_offset >= 0) {
        BlockHeader *next = (BlockHeader *)(p->pool + h->next_offset);
        if (next->is_free) {
            h->size += HEADER_SIZE + next->size;
            h->next_offset = next->next_offset;
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU pool allocator                                                  */
/* ------------------------------------------------------------------ */
typedef struct {
    char *pool;
    int pool_size;
} GPUPool;

void gpu_pool_init(GPUPool *p) {
    p->pool = (char *)calloc(POOL_SIZE, 1);
    p->pool_size = POOL_SIZE;
    BlockHeader *h = (BlockHeader *)p->pool;
    h->size = POOL_SIZE - HEADER_SIZE;
    h->is_free = 1;
    h->next_offset = -1;
}

int gpu_pool_alloc(GPUPool *p, int size) {
    size = ((size + ALIGNMENT - 1) / ALIGNMENT) * ALIGNMENT;
    int offset = 0;
    while (offset >= 0 && offset < p->pool_size) {
        BlockHeader *h = (BlockHeader *)(p->pool + offset);
        if (h->is_free && h->size >= size) {
            if (h->size >= size + HEADER_SIZE + ALIGNMENT) {
                int new_offset = offset + HEADER_SIZE + size;
                BlockHeader *nh = (BlockHeader *)(p->pool + new_offset);
                nh->size = h->size - size - HEADER_SIZE;
                nh->is_free = 1;
                nh->next_offset = h->next_offset;
                h->next_offset = new_offset;
                h->size = size;
            }
            h->is_free = 0;
            return offset + HEADER_SIZE;
        }
        offset = h->next_offset;
    }
    return -1;
}

void gpu_pool_free(GPUPool *p, int data_offset) {
    int offset = data_offset - HEADER_SIZE;
    BlockHeader *h = (BlockHeader *)(p->pool + offset);
    h->is_free = 1;

    /* Coalesce with next block — size calculation is wrong */
    if (h->next_offset >= 0) {
        BlockHeader *next = (BlockHeader *)(p->pool + h->next_offset);
        if (next->is_free) {
            h->size += next->size;  /* Missing HEADER_SIZE addition */
            h->next_offset = next->next_offset;
        }
    }
}

/* ------------------------------------------------------------------ */
/* Test harness — perform same operations on both allocators            */
/* ------------------------------------------------------------------ */
int main(int argc, char **argv) {
    int num_ops = 20;
    unsigned int seed = 42;
    int alloc_size = 512;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--ops") == 0 && k+1 < argc) num_ops = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--alloc") == 0 && k+1 < argc) alloc_size = atoi(argv[++k]);
    }

    CPUPool cpu_pool;
    GPUPool gpu_pool;
    cpu_pool_init(&cpu_pool);
    gpu_pool_init(&gpu_pool);

    int *cpu_offsets = (int *)malloc(num_ops * sizeof(int));
    int *gpu_offsets = (int *)malloc(num_ops * sizeof(int));
    int alloc_count = 0;

    int mismatches = 0;
    int alloc_failures = 0;
    unsigned int s = seed;

    /* Phase 1: Allocate and write patterns */
    for (int i = 0; i < num_ops; i++) {
        s = s * 1103515245u + 12345u;
        int sz = alloc_size + (s % 512);

        int co = cpu_pool_alloc(&cpu_pool, sz);
        int go = gpu_pool_alloc(&gpu_pool, sz);

        cpu_offsets[i] = co;
        gpu_offsets[i] = go;

        if (co >= 0 && go >= 0) {
            /* Write pattern */
            memset(cpu_pool.pool + co, (i + 1) & 0xFF, sz);
            memset(gpu_pool.pool + go, (i + 1) & 0xFF, sz);
            alloc_count++;
        }
    }

    /* Phase 2: Free every other block */
    for (int i = 0; i < num_ops; i += 2) {
        if (cpu_offsets[i] >= 0) cpu_pool_free(&cpu_pool, cpu_offsets[i]);
        if (gpu_offsets[i] >= 0) gpu_pool_free(&gpu_pool, gpu_offsets[i]);
    }

    /* Phase 3: Re-allocate into freed space */
    for (int i = 0; i < num_ops; i += 2) {
        s = s * 1103515245u + 12345u;
        int sz = alloc_size + (s % 256);

        int co = cpu_pool_alloc(&cpu_pool, sz);
        int go = gpu_pool_alloc(&gpu_pool, sz);

        if (co >= 0 && go >= 0) {
            memset(cpu_pool.pool + co, 0xAA, sz);
            memset(gpu_pool.pool + go, 0xAA, sz);
        } else if ((co >= 0) != (go >= 0)) {
            alloc_failures++;
        }
    }

    /* Check: verify odd-indexed allocations still have their data */
    for (int i = 1; i < num_ops; i += 2) {
        if (cpu_offsets[i] < 0 || gpu_offsets[i] < 0) continue;
        s = seed;
        for (int j = 0; j <= i; j++) s = s * 1103515245u + 12345u;
        int sz = alloc_size + (s % 512);
        /* Align size */
        sz = ((sz + ALIGNMENT - 1) / ALIGNMENT) * ALIGNMENT;

        unsigned char expected = (i + 1) & 0xFF;
        for (int b = 0; b < sz && b < 64; b++) {
            unsigned char cpu_val = (unsigned char)cpu_pool.pool[cpu_offsets[i] + b];
            unsigned char gpu_val = (unsigned char)gpu_pool.pool[gpu_offsets[i] + b];
            if (cpu_val != gpu_val) {
                mismatches++;
                break;
            }
        }
    }

    printf("OPS=%d\n", num_ops);
    printf("ALLOC_SIZE=%d\n", alloc_size);
    printf("ALLOC_COUNT=%d\n", alloc_count);
    printf("ALLOC_FAILURES=%d\n", alloc_failures);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MATCH=%d\n", (mismatches == 0 && alloc_failures == 0) ? 1 : 0);

    free(cpu_pool.pool); free(gpu_pool.pool);
    free(cpu_offsets); free(gpu_offsets);
    return (mismatches == 0 && alloc_failures == 0) ? 0 : 1;
}
