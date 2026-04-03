#include <iostream>
#include <string>
#include <cstring>
#include <vector>
#include "filehandle.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: prog <test_name>" << std::endl;
        return 1;
    }

    std::string test = argv[1];

    if (test == "basic_open_close") {
        MockFS::reset();
        {
            FileHandle fh("test.txt");
            std::cout << "fd=" << fh.fd() << std::endl;
            std::cout << "valid=" << fh.isValid() << std::endl;
        }
        std::cout << "open=" << MockFS::open_count << std::endl;
        std::cout << "close=" << MockFS::close_count << std::endl;
        std::cout << "balanced=" << MockFS::isBalanced() << std::endl;
    }
    else if (test == "factory_return") {
        MockFS::reset();
        {
            FileHandle fh = openFile("data.bin");
            std::cout << "fd=" << fh.fd() << std::endl;
            std::cout << "path=" << fh.path() << std::endl;
        }
        std::cout << "open=" << MockFS::open_count << std::endl;
        std::cout << "close=" << MockFS::close_count << std::endl;
        std::cout << "balanced=" << MockFS::isBalanced() << std::endl;
    }
    else if (test == "vector_storage") {
        MockFS::reset();
        {
            std::vector<FileHandle> handles;
            storeHandles(handles, "a.txt");
            storeHandles(handles, "b.txt");
            std::cout << "size=" << handles.size() << std::endl;
        }
        std::cout << "open=" << MockFS::open_count << std::endl;
        std::cout << "close=" << MockFS::close_count << std::endl;
        std::cout << "balanced=" << MockFS::isBalanced() << std::endl;
    }
    else if (test == "move_semantics") {
        MockFS::reset();
        {
            FileHandle fh1("file1.txt");
            FileHandle fh2(std::move(fh1));
            std::cout << "fh2_valid=" << fh2.isValid() << std::endl;
        }
        std::cout << "open=" << MockFS::open_count << std::endl;
        std::cout << "close=" << MockFS::close_count << std::endl;
        std::cout << "balanced=" << MockFS::isBalanced() << std::endl;
    }
    else {
        std::cout << "Unknown test: " << test << std::endl;
        return 1;
    }

    return 0;
}
