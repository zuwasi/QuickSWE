#include "resource_manager.h"
#include <iostream>
#include <sstream>

void ResourceManager::addResource(int id, const std::string& name, int priority) {
    resources_.push_back(std::make_unique<Resource>(id, name, priority));
}

std::string ResourceManager::getResourceInfo(int index) const {
    if (index < 0 || index >= (int)resources_.size()) {
        return "INVALID_INDEX";
    }
    if (!resources_[index]) {
        return "NULL_RESOURCE";
    }
    return resources_[index]->info();
}

void ResourceManager::archiveResource(std::shared_ptr<Resource> res) {
    archive_.push_back(res);
}

void ResourceManager::transferResource(int index) {
    if (index < 0 || index >= (int)resources_.size()) {
        return;
    }

    /* Move unique_ptr into a shared_ptr for archiving */
    std::shared_ptr<Resource> shared(std::move(resources_[index]));
    archiveResource(shared);

    /*
     * BUG: use-after-move — resources_[index] is now null after std::move,
     * but we still try to access it to log the transfer.
     */
    std::cout << "Transferred: " << resources_[index]->info() << std::endl;
}

int ResourceManager::resourceCount() const {
    int count = 0;
    for (const auto& r : resources_) {
        if (r) count++;
    }
    return count;
}

std::string ResourceManager::getAllInfo() const {
    std::ostringstream oss;
    for (int i = 0; i < (int)resources_.size(); i++) {
        if (resources_[i]) {
            oss << resources_[i]->info();
            if (i < (int)resources_.size() - 1) oss << ";";
        }
    }
    return oss.str();
}
