#include <iostream>
#include <string>
#include <cstring>
#include "resource_manager.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: prog <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "add_and_info") {
        ResourceManager mgr;
        mgr.addResource(1, "TextureA", 5);
        mgr.addResource(2, "MeshB", 3);
        std::cout << mgr.getResourceInfo(0) << std::endl;
        std::cout << mgr.getResourceInfo(1) << std::endl;
        std::cout << "count=" << mgr.resourceCount() << std::endl;
    }
    else if (test == "transfer_and_access") {
        ResourceManager mgr;
        mgr.addResource(1, "TextureA", 5);
        mgr.addResource(2, "MeshB", 3);
        mgr.addResource(3, "ShaderC", 10);

        /* This will crash due to use-after-move */
        mgr.transferResource(0);

        /* After transfer, resource at index 0 should be null */
        std::cout << "after_transfer_0=" << mgr.getResourceInfo(0) << std::endl;
        std::cout << "still_valid_1=" << mgr.getResourceInfo(1) << std::endl;
        std::cout << "count=" << mgr.resourceCount() << std::endl;
    }
    else if (test == "transfer_all") {
        ResourceManager mgr;
        mgr.addResource(10, "Alpha", 1);
        mgr.addResource(20, "Beta", 2);

        mgr.transferResource(0);
        mgr.transferResource(1);

        std::cout << "count=" << mgr.resourceCount() << std::endl;
    }
    else if (test == "invalid_index") {
        ResourceManager mgr;
        mgr.addResource(1, "Test", 1);
        std::cout << mgr.getResourceInfo(-1) << std::endl;
        std::cout << mgr.getResourceInfo(5) << std::endl;
    }
    else if (test == "get_all") {
        ResourceManager mgr;
        mgr.addResource(1, "A", 1);
        mgr.addResource(2, "B", 2);
        std::cout << mgr.getAllInfo() << std::endl;
    }
    else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
