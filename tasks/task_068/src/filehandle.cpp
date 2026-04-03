#include "filehandle.h"
#include <iostream>

int MockFS::open_count = 0;
int MockFS::close_count = 0;

int MockFS::openFile(const std::string& path) {
    open_count++;
    return open_count;  /* fd = sequential id */
}

void MockFS::closeFile(int fd) {
    if (fd >= 0) {
        close_count++;
    }
}

FileHandle::FileHandle(const std::string& path) : path_(path) {
    fd_ = MockFS::openFile(path);
}

FileHandle::~FileHandle() {
    if (fd_ >= 0) {
        MockFS::closeFile(fd_);
    }
}

/* BUG: returning by value triggers copy constructor (default shallow copy).
 * Both the temporary and the returned copy have the same fd_.
 * When the temporary is destroyed, fd_ is closed.
 * When the returned copy is destroyed, fd_ is closed again -> double-free. */
FileHandle openFile(const std::string& path) {
    FileHandle fh(path);
    return fh;
}

void storeHandles(std::vector<FileHandle>& vec, const std::string& path) {
    FileHandle fh(path);
    vec.push_back(fh);  /* BUG: copy into vector -> double-close */
}
