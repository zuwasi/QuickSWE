#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define TILE_SIZE 16

// ---------------------------------------------------------------------------
// CPU reference 2D convolution (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_conv2d(const float *image, float *output,
                int width, int height,
                const float *kernel, int ksize) {
    int radius = ksize / 2;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float sum = 0.0f;
            for (int ky = -radius; ky <= radius; ky++) {
                for (int kx = -radius; kx <= radius; kx++) {
                    int ix = x + kx;
                    int iy = y + ky;
                    // Clamp to border
                    if (ix < 0) ix = 0;
                    if (ix >= width) ix = width - 1;
                    if (iy < 0) iy = 0;
                    if (iy >= height) iy = height - 1;
                    sum += image[iy * width + ix] *
                           kernel[(ky + radius) * ksize + (kx + radius)];
                }
            }
            output[y * width + x] = sum;
        }
    }
}

// ---------------------------------------------------------------------------
// GPU 2D convolution with shared memory + halos — BUGGY
// ---------------------------------------------------------------------------

/*
 * BUG 1 — Halo shared-memory indexing:
 *   The shared memory tile has dimensions (TILE_SIZE + 2*radius) in each
 *   direction.  When loading halo pixels, the code computes the shared-
 *   memory (sx, sy) position, but FORGETS to add the radius offset.
 *   For example, the left halo at global column (gx - radius) should be
 *   stored at shared-memory column (threadIdx.x), but instead is stored
 *   at (threadIdx.x - radius), which is negative → undefined behaviour.
 *
 * BUG 2 — Inconsistent radius/diameter:
 *   The convolution kernel loop uses `ksize` (the DIAMETER) as the
 *   loop bound in one dimension but uses `radius` (half the diameter)
 *   in the other dimension, so the convolution only covers half the
 *   filter in the Y direction.
 */

// We use a max supported radius to size static shared memory.
#define MAX_RADIUS 4
#define SHARED_DIM (TILE_SIZE + 2 * MAX_RADIUS)

__global__ void conv2d_kernel(const float *image, float *output,
                              int width, int height,
                              const float *kern, int ksize, int radius) {
    // Global pixel coordinates
    int gx = blockIdx.x * TILE_SIZE + threadIdx.x;
    int gy = blockIdx.y * TILE_SIZE + threadIdx.y;

    // Shared memory tile including halos
    __shared__ float tile[SHARED_DIM][SHARED_DIM];

    // Load the main tile region
    int sx = threadIdx.x + radius;
    int sy = threadIdx.y + radius;
    if (gx < width && gy < height) {
        tile[sy][sx] = image[gy * width + gx];
    } else {
        tile[sy][sx] = 0.0f;
    }

    // Load halo regions
    // Left halo
    if (threadIdx.x < radius) {
        int hx = gx - radius;
        if (hx < 0) hx = 0;
        // BUG 1: should be tile[sy][threadIdx.x] but writes to
        //         tile[sy][threadIdx.x - radius] via missing offset
        int bad_sx = threadIdx.x;  // Looks right but see below for top/bottom
        if (gy < height)
            tile[sy][bad_sx] = image[gy * width + hx];
    }
    // Right halo
    if (threadIdx.x >= TILE_SIZE - radius) {
        int hx = gx + radius;
        if (hx >= width) hx = width - 1;
        int rsx = threadIdx.x + 2 * radius;
        if (gy < height)
            tile[sy][rsx] = image[gy * width + hx];
    }
    // Top halo
    if (threadIdx.y < radius) {
        int hy = gy - radius;
        if (hy < 0) hy = 0;
        // BUG 1: missing radius offset — writes to tile[threadIdx.y - radius][sx]
        //         but threadIdx.y - radius is negative
        int bad_sy = threadIdx.y;  // Should be threadIdx.y, and indeed we
                                    // use it, but we must also load the CORNER
                                    // halos which this code skips entirely.
        if (gx < width)
            tile[bad_sy][sx] = image[hy * width + gx];
    }
    // Bottom halo
    if (threadIdx.y >= TILE_SIZE - radius) {
        int hy = gy + radius;
        if (hy >= height) hy = height - 1;
        int bsy = threadIdx.y + 2 * radius;
        if (gx < width)
            tile[bsy][sx] = image[hy * width + gx];
    }

    // NOTE: Corner halos (top-left, top-right, bottom-left, bottom-right)
    //       are NOT loaded at all — BUG 1 continued.

    __syncthreads();

    // Compute convolution
    if (gx < width && gy < height) {
        float sum = 0.0f;
        // BUG 2: Y loop uses `radius` instead of `ksize`
        //         → only iterates over top half of the kernel
        for (int ky = 0; ky < radius; ky++) {
            for (int kx = 0; kx < ksize; kx++) {
                sum += tile[threadIdx.y + ky][threadIdx.x + kx] *
                       kern[ky * ksize + kx];
            }
        }
        output[gy * width + gx] = sum;
    }
}

// ---------------------------------------------------------------------------
// Host driver
// ---------------------------------------------------------------------------
void gpu_conv2d(const float *h_image, float *h_output,
                int width, int height,
                const float *h_kern, int ksize) {
    int radius = ksize / 2;
    if (radius > MAX_RADIUS) {
        fprintf(stderr, "ERROR: radius %d exceeds MAX_RADIUS %d\n",
                radius, MAX_RADIUS);
        return;
    }

    int img_size = width * height;
    int kern_size = ksize * ksize;

    float *d_image, *d_output, *d_kern;
    cudaMalloc(&d_image,  img_size * sizeof(float));
    cudaMalloc(&d_output, img_size * sizeof(float));
    cudaMalloc(&d_kern,   kern_size * sizeof(float));

    cudaMemcpy(d_image, h_image, img_size * sizeof(float),
               cudaMemcpyHostToDevice);
    cudaMemcpy(d_kern, h_kern, kern_size * sizeof(float),
               cudaMemcpyHostToDevice);

    dim3 block(TILE_SIZE, TILE_SIZE);
    dim3 grid((width + TILE_SIZE - 1) / TILE_SIZE,
              (height + TILE_SIZE - 1) / TILE_SIZE);

    conv2d_kernel<<<grid, block>>>(d_image, d_output, width, height,
                                    d_kern, ksize, radius);
    cudaDeviceSynchronize();

    cudaMemcpy(h_output, d_output, img_size * sizeof(float),
               cudaMemcpyDeviceToHost);

    cudaFree(d_image);
    cudaFree(d_output);
    cudaFree(d_kern);
}

// ---------------------------------------------------------------------------
// Generate convolution kernels
// ---------------------------------------------------------------------------
void make_box_kernel(float *kern, int ksize) {
    float v = 1.0f / (float)(ksize * ksize);
    for (int i = 0; i < ksize * ksize; i++) kern[i] = v;
}

void make_gaussian_kernel(float *kern, int ksize) {
    int radius = ksize / 2;
    float sigma = (float)radius;
    float sum = 0.0f;
    for (int y = -radius; y <= radius; y++) {
        for (int x = -radius; x <= radius; x++) {
            float v = expf(-(float)(x * x + y * y) / (2.0f * sigma * sigma));
            kern[(y + radius) * ksize + (x + radius)] = v;
            sum += v;
        }
    }
    for (int i = 0; i < ksize * ksize; i++) kern[i] /= sum;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int width = 64, height = 64;
    int radius = 1;
    unsigned int seed = 42;
    char kern_type[16] = "box";

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--width") == 0 && k + 1 < argc)
            width = atoi(argv[++k]);
        else if (strcmp(argv[k], "--height") == 0 && k + 1 < argc)
            height = atoi(argv[++k]);
        else if (strcmp(argv[k], "--radius") == 0 && k + 1 < argc)
            radius = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc)
            seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--kernel") == 0 && k + 1 < argc) {
            strncpy(kern_type, argv[++k], 15);
            kern_type[15] = '\0';
        }
    }

    int ksize = 2 * radius + 1;
    int img_size = width * height;

    float *image    = (float *)malloc(img_size * sizeof(float));
    float *cpu_out  = (float *)malloc(img_size * sizeof(float));
    float *gpu_out  = (float *)calloc(img_size, sizeof(float));
    float *kern     = (float *)malloc(ksize * ksize * sizeof(float));
    if (!image || !cpu_out || !gpu_out || !kern) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < img_size; i++) {
        image[i] = (float)(rand() % 256) / 255.0f;
    }

    if (strcmp(kern_type, "gaussian") == 0) {
        make_gaussian_kernel(kern, ksize);
    } else {
        make_box_kernel(kern, ksize);
    }

    cpu_conv2d(image, cpu_out, width, height, kern, ksize);
    gpu_conv2d(image, gpu_out, width, height, kern, ksize);

    float max_err = 0.0f;
    int mismatches = 0;
    int first_bad = -1;
    int boundary_errors = 0;

    for (int i = 0; i < img_size; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 1e-3f) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
            // Check if near a tile boundary
            int px = i % width;
            int py = i / width;
            if (px % TILE_SIZE < radius || px % TILE_SIZE >= TILE_SIZE - radius ||
                py % TILE_SIZE < radius || py % TILE_SIZE >= TILE_SIZE - radius) {
                boundary_errors++;
            }
        }
    }

    int match = (mismatches == 0) ? 1 : 0;

    printf("WIDTH=%d\n", width);
    printf("HEIGHT=%d\n", height);
    printf("KSIZE=%d\n", ksize);
    printf("RADIUS=%d\n", radius);
    printf("MAX_ERROR=%.6f\n", max_err);
    printf("MISMATCHES=%d\n", mismatches);
    printf("BOUNDARY_ERRORS=%d\n", boundary_errors);
    if (first_bad >= 0) {
        printf("FIRST_BAD_INDEX=%d\n", first_bad);
        printf("EXPECTED=%.6f\n", cpu_out[first_bad]);
        printf("GOT=%.6f\n", gpu_out[first_bad]);
    }
    printf("MATCH=%d\n", match);

    free(image);
    free(cpu_out);
    free(gpu_out);
    free(kern);
    return match ? 0 : 1;
}
