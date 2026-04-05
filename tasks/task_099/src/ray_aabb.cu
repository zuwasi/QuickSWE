#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>

#define BLOCK_SIZE 128
#define MAX_BOXES 256
#define STACK_SIZE 64

/* ------------------------------------------------------------------ */
/* Data types                                                          */
/* ------------------------------------------------------------------ */
typedef struct { float x, y, z; } Vec3;
typedef struct { Vec3 origin, dir; } Ray;
typedef struct { Vec3 bmin, bmax; int left, right; int is_leaf; int prim_id; } BVHNode;

/* ------------------------------------------------------------------ */
/* CPU reference ray-AABB test (DO NOT MODIFY)                        */
/* ------------------------------------------------------------------ */
int cpu_ray_aabb(const Ray *ray, const BVHNode *node, float *t_hit) {
    float tmin = 0.0f, tmax = FLT_MAX;

    float invx = 1.0f / ray->dir.x;
    float t1 = (node->bmin.x - ray->origin.x) * invx;
    float t2 = (node->bmax.x - ray->origin.x) * invx;
    if (t1 > t2) { float tmp = t1; t1 = t2; t2 = tmp; }
    tmin = fmaxf(tmin, t1);
    tmax = fminf(tmax, t2);

    float invy = 1.0f / ray->dir.y;
    t1 = (node->bmin.y - ray->origin.y) * invy;
    t2 = (node->bmax.y - ray->origin.y) * invy;
    if (t1 > t2) { float tmp = t1; t1 = t2; t2 = tmp; }
    tmin = fmaxf(tmin, t1);
    tmax = fminf(tmax, t2);

    float invz = 1.0f / ray->dir.z;
    t1 = (node->bmin.z - ray->origin.z) * invz;
    t2 = (node->bmax.z - ray->origin.z) * invz;
    if (t1 > t2) { float tmp = t1; t1 = t2; t2 = tmp; }
    tmin = fmaxf(tmin, t1);
    tmax = fminf(tmax, t2);

    if (tmin <= tmax && tmax >= 0.0f) {
        *t_hit = tmin >= 0.0f ? tmin : tmax;
        return 1;
    }
    return 0;
}

int cpu_traverse(const Ray *ray, const BVHNode *nodes, int num_nodes,
                  int *hit_id, float *hit_t) {
    *hit_t = FLT_MAX;
    *hit_id = -1;

    int stack[STACK_SIZE];
    int sp = 0;
    stack[sp++] = 0;

    while (sp > 0) {
        int idx = stack[--sp];
        if (idx < 0 || idx >= num_nodes) continue;

        float t;
        if (!cpu_ray_aabb(ray, &nodes[idx], &t)) continue;
        if (t >= *hit_t) continue;

        if (nodes[idx].is_leaf) {
            *hit_t = t;
            *hit_id = nodes[idx].prim_id;
        } else {
            if (nodes[idx].left >= 0) stack[sp++] = nodes[idx].left;
            if (nodes[idx].right >= 0) stack[sp++] = nodes[idx].right;
        }
    }
    return *hit_id >= 0 ? 1 : 0;
}

/* ------------------------------------------------------------------ */
/* GPU ray-AABB kernel                                                 */
/* ------------------------------------------------------------------ */
__device__ int gpu_ray_aabb(const Ray *ray, const BVHNode *node, float *t_hit) {
    float tmin = 0.0f, tmax = 0.0f;

    float invx = 1.0f / ray->dir.x;
    float t1 = (node->bmin.x - ray->origin.x) * invx;
    float t2 = (node->bmax.x - ray->origin.x) * invx;
    tmin = fmaxf(tmin, fminf(t1, t2));
    tmax = fminf(tmax, fmaxf(t1, t2));

    float invy = 1.0f / ray->dir.y;
    t1 = (node->bmin.y - ray->origin.y) * invy;
    t2 = (node->bmax.y - ray->origin.y) * invy;
    tmin = fmaxf(tmin, fminf(t1, t2));
    tmax = fminf(tmax, fmaxf(t1, t2));

    float invz = 1.0f / ray->dir.z;
    t1 = (node->bmin.z - ray->origin.z) * invz;
    t2 = (node->bmax.z - ray->origin.z) * invz;
    tmin = fmaxf(tmin, fminf(t1, t2));
    tmax = fminf(tmax, fmaxf(t1, t2));

    if (tmin <= tmax && tmax >= 0.0f) {
        *t_hit = tmin >= 0.0f ? tmin : tmax;
        return 1;
    }
    return 0;
}

__global__ void traverse_kernel(const Ray *rays, const BVHNode *nodes,
                                  int num_rays, int num_nodes,
                                  int *hit_ids, float *hit_ts) {
    int rid = blockIdx.x * blockDim.x + threadIdx.x;
    if (rid >= num_rays) return;

    Ray ray = rays[rid];
    float best_t = 0.0f;
    int best_id = -1;

    int stack[STACK_SIZE];
    int sp = 0;
    stack[sp++] = 0;

    while (sp > 0) {
        int idx = stack[sp--];
        if (idx < 0 || idx >= num_nodes) continue;

        float t;
        if (!gpu_ray_aabb(&ray, &nodes[idx], &t)) continue;
        if (t >= best_t && best_id >= 0) continue;

        if (nodes[idx].is_leaf >= 1) {
            best_t = t;
            best_id = nodes[idx].prim_id;
        } else {
            if (nodes[idx].left >= 0) stack[sp++] = nodes[idx].left;
            if (nodes[idx].right >= 0) stack[sp++] = nodes[idx].right;
        }
    }

    hit_ids[rid] = best_id;
    hit_ts[rid] = best_t;
}

/* ------------------------------------------------------------------ */
void gpu_traverse(const Ray *h_rays, const BVHNode *h_nodes,
                   int num_rays, int num_nodes,
                   int *h_hit_ids, float *h_hit_ts) {
    Ray *d_rays;
    BVHNode *d_nodes;
    int *d_hit_ids;
    float *d_hit_ts;

    cudaMalloc(&d_rays, num_rays * sizeof(Ray));
    cudaMalloc(&d_nodes, num_nodes * sizeof(BVHNode));
    cudaMalloc(&d_hit_ids, num_rays * sizeof(int));
    cudaMalloc(&d_hit_ts, num_rays * sizeof(float));

    cudaMemcpy(d_rays, h_rays, num_rays * sizeof(Ray), cudaMemcpyHostToDevice);
    cudaMemcpy(d_nodes, h_nodes, num_nodes * sizeof(BVHNode), cudaMemcpyHostToDevice);

    int grid = (num_rays + BLOCK_SIZE - 1) / BLOCK_SIZE;
    traverse_kernel<<<grid, BLOCK_SIZE>>>(d_rays, d_nodes, num_rays, num_nodes,
                                            d_hit_ids, d_hit_ts);
    cudaDeviceSynchronize();

    cudaMemcpy(h_hit_ids, d_hit_ids, num_rays * sizeof(int), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_hit_ts, d_hit_ts, num_rays * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_rays); cudaFree(d_nodes); cudaFree(d_hit_ids); cudaFree(d_hit_ts);
}

/* ------------------------------------------------------------------ */
void build_flat_bvh(BVHNode *nodes, int *num_nodes, int num_prims,
                     unsigned int seed) {
    int n = 0;
    /* Create leaf nodes for each primitive */
    int leaf_start = 1;
    for (int i = 0; i < num_prims; i++) {
        int idx = leaf_start + i;
        seed = seed * 1103515245u + 12345u;
        float cx = (float)(seed % 200) / 10.0f - 10.0f;
        seed = seed * 1103515245u + 12345u;
        float cy = (float)(seed % 200) / 10.0f - 10.0f;
        seed = seed * 1103515245u + 12345u;
        float cz = (float)(seed % 200) / 10.0f - 10.0f;
        float sz = 0.5f + (float)(seed % 100) / 100.0f;

        nodes[idx].bmin = {cx - sz, cy - sz, cz - sz};
        nodes[idx].bmax = {cx + sz, cy + sz, cz + sz};
        nodes[idx].is_leaf = 1;
        nodes[idx].prim_id = i;
        nodes[idx].left = nodes[idx].right = -1;
    }

    /* Root node encompasses all leaves */
    nodes[0].bmin = {-20.0f, -20.0f, -20.0f};
    nodes[0].bmax = { 20.0f,  20.0f,  20.0f};
    nodes[0].is_leaf = 0;
    nodes[0].prim_id = -1;
    nodes[0].left = 1;
    nodes[0].right = num_prims > 1 ? (1 + num_prims / 2) : -1;

    /* Simple split: first half under left, second half under right */
    if (num_prims > 2) {
        /* Insert intermediate nodes */
        /* For simplicity, make root point to first and mid leaf directly */
        nodes[0].left = 1;
        nodes[0].right = 1 + num_prims / 2;
    }

    *num_nodes = 1 + num_prims;
}

void generate_rays(Ray *rays, int num_rays, unsigned int seed) {
    for (int i = 0; i < num_rays; i++) {
        seed = seed * 1103515245u + 12345u;
        rays[i].origin.x = (float)(seed % 100) / 5.0f - 10.0f;
        seed = seed * 1103515245u + 12345u;
        rays[i].origin.y = (float)(seed % 100) / 5.0f - 10.0f;
        seed = seed * 1103515245u + 12345u;
        rays[i].origin.z = -15.0f;

        seed = seed * 1103515245u + 12345u;
        float dx = (float)(seed % 100) / 50.0f - 1.0f;
        seed = seed * 1103515245u + 12345u;
        float dy = (float)(seed % 100) / 50.0f - 1.0f;
        float dz = 1.0f;
        float len = sqrtf(dx*dx + dy*dy + dz*dz);
        rays[i].dir.x = dx / len;
        rays[i].dir.y = dy / len;
        rays[i].dir.z = dz / len;
    }
}

int main(int argc, char **argv) {
    int num_prims = 16;
    int num_rays = 256;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--prims") == 0 && k+1 < argc) num_prims = atoi(argv[++k]);
        else if (strcmp(argv[k], "--rays") == 0 && k+1 < argc) num_rays = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    BVHNode *nodes = (BVHNode *)calloc(MAX_BOXES, sizeof(BVHNode));
    int num_nodes;
    build_flat_bvh(nodes, &num_nodes, num_prims, seed);

    Ray *rays = (Ray *)malloc(num_rays * sizeof(Ray));
    generate_rays(rays, num_rays, seed + 999);

    int *cpu_ids = (int *)malloc(num_rays * sizeof(int));
    float *cpu_ts = (float *)malloc(num_rays * sizeof(float));
    int *gpu_ids = (int *)malloc(num_rays * sizeof(int));
    float *gpu_ts = (float *)malloc(num_rays * sizeof(float));

    for (int i = 0; i < num_rays; i++) {
        cpu_traverse(&rays[i], nodes, num_nodes, &cpu_ids[i], &cpu_ts[i]);
    }
    gpu_traverse(rays, nodes, num_rays, num_nodes, gpu_ids, gpu_ts);

    int mismatches = 0;
    int missed_hits = 0;
    int false_hits = 0;
    for (int i = 0; i < num_rays; i++) {
        if (cpu_ids[i] != gpu_ids[i]) {
            mismatches++;
            if (cpu_ids[i] >= 0 && gpu_ids[i] < 0) missed_hits++;
            if (cpu_ids[i] < 0 && gpu_ids[i] >= 0) false_hits++;
        }
    }

    int cpu_hits = 0, gpu_hits = 0;
    for (int i = 0; i < num_rays; i++) {
        if (cpu_ids[i] >= 0) cpu_hits++;
        if (gpu_ids[i] >= 0) gpu_hits++;
    }

    printf("PRIMS=%d\n", num_prims);
    printf("RAYS=%d\n", num_rays);
    printf("NODES=%d\n", num_nodes);
    printf("CPU_HITS=%d\n", cpu_hits);
    printf("GPU_HITS=%d\n", gpu_hits);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MISSED_HITS=%d\n", missed_hits);
    printf("FALSE_HITS=%d\n", false_hits);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(nodes); free(rays); free(cpu_ids); free(cpu_ts);
    free(gpu_ids); free(gpu_ts);
    return mismatches == 0 ? 0 : 1;
}
