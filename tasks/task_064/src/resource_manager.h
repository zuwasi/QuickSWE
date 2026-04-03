#ifndef RESOURCE_MANAGER_H
#define RESOURCE_MANAGER_H

#include <memory>
#include <string>
#include <vector>

struct Resource {
    int id;
    std::string name;
    int priority;

    Resource(int id, const std::string& name, int priority)
        : id(id), name(name), priority(priority) {}

    std::string info() const {
        return "Resource(" + std::to_string(id) + "," + name + "," + std::to_string(priority) + ")";
    }
};

class ResourceManager {
public:
    void addResource(int id, const std::string& name, int priority);
    std::string getResourceInfo(int index) const;
    void transferResource(int index);
    int resourceCount() const;
    std::string getAllInfo() const;

private:
    std::vector<std::unique_ptr<Resource>> resources_;

    /* Helper that "archives" a resource — takes shared_ptr by value */
    void archiveResource(std::shared_ptr<Resource> res);
    std::vector<std::shared_ptr<Resource>> archive_;
};

#endif
