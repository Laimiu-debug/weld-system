"""Access policy for business entities whose scope is defined by workspace/factory."""


class WorkspaceEntityAccessMixin:
    @property
    def access_level(self) -> str:
        if self.workspace_type == "personal":
            return "private"
        return "factory" if self.factory_id else "company"
