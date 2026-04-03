#ifndef FILEHANDLE_H
#define FILEHANDLE_H

#include <string>
#include <vector>

/* Mock filesystem that tracks open/close counts */
class MockFS {
public:
    static int open_count;
    static int close_count;

    static void reset() { open_count = 0; close_count = 0; }
    static int openFile(const std::string& path);
    static void closeFile(int fd);
    static bool isBalanced() { return open_count == close_count; }
};

class FileHandle {
public:
    explicit FileHandle(const std::string& path);
    ~FileHandle();

    /*
     * BUG: No copy constructor, copy assignment, move constructor, or move assignment
     * defined. The compiler generates default copy ops that do a shallow copy of fd_,
     * leading to double-close when both copies are destroyed.
     */

    int fd() const { return fd_; }
    bool isValid() const { return fd_ >= 0; }
    std::string path() const { return path_; }

private:
    int fd_;
    std::string path_;
};

/* Factory function that returns a FileHandle — triggers copy/move */
FileHandle openFile(const std::string& path);

/* Stores handles in a vector — triggers copy */
void storeHandles(std::vector<FileHandle>& vec, const std::string& path);

#endif
