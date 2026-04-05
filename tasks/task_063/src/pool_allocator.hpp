#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <stdexcept>

class PoolAllocator {
    struct Block {
        std::size_t offset;
        std::size_t size;
        bool free;
    };

public:
    explicit PoolAllocator(std::size_t pool_size)
        : pool_(pool_size, 0), blocks_{{0, pool_size, true}} {}

    std::size_t allocate(std::size_t size) {
        if (size == 0) throw std::invalid_argument("zero allocation");
        for (std::size_t i = 0; i < blocks_.size(); ++i) {
            if (blocks_[i].free && blocks_[i].size >= size) {
                blocks_[i].free = false;
                if (blocks_[i].size > size) {
                    Block remainder{blocks_[i].offset + size,
                                    blocks_[i].size - size, true};
                    blocks_[i].size = size;
                    blocks_.insert(blocks_.begin() + i + 1, remainder);
                }
                return blocks_[i].offset;
            }
        }
        throw std::runtime_error("out of memory");
    }

    void deallocate(std::size_t offset) {
        for (auto& block : blocks_) {
            if (block.offset == offset && !block.free) {
                block.free = true;
                coalesce();
                return;
            }
        }
        throw std::runtime_error("invalid deallocation");
    }

    std::size_t available() const {
        std::size_t total = 0;
        for (const auto& b : blocks_)
            if (b.free) total += b.size;
        return total;
    }

    std::size_t largest_free() const {
        std::size_t max = 0;
        for (const auto& b : blocks_)
            if (b.free && b.size > max) max = b.size;
        return max;
    }

    std::size_t num_blocks() const { return blocks_.size(); }

    std::size_t pool_size() const { return pool_.size(); }

private:
    std::vector<std::uint8_t> pool_;
    std::vector<Block> blocks_;

    void coalesce() {
        for (std::size_t i = 0; i + 1 < blocks_.size(); ++i) {
            if (blocks_[i].free && blocks_[i + 1].free) {
                blocks_[i].size = blocks_[i + 1].size;
                blocks_.erase(blocks_.begin() + i + 1);
                // Don't decrement i — check this block with new next neighbor
            }
        }
    }
};
