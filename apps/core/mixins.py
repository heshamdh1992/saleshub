from django.core.exceptions import PermissionDenied


class MerchantRequiredMixin:
    def get_merchant(self):
        user = self.request.user
        staff_profile = getattr(user, "staff_profile", None)
        if not staff_profile or not staff_profile.merchant:
            raise PermissionDenied("لا يوجد محل مرتبط بهذا المستخدم.")
        return staff_profile.merchant

    def get_staff_profile(self):
        staff_profile = getattr(self.request.user, "staff_profile", None)
        if not staff_profile:
            raise PermissionDenied("لا يوجد ملف موظف مرتبط بهذا المستخدم.")
        return staff_profile

    def get_role(self):
        return self.get_staff_profile().role


class OwnerRequiredMixin(MerchantRequiredMixin):
    allowed_roles = ["owner"]

    def dispatch(self, request, *args, **kwargs):
        if self.get_role() not in self.allowed_roles:
            raise PermissionDenied("ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return super().dispatch(request, *args, **kwargs)


class ManagerOrOwnerRequiredMixin(MerchantRequiredMixin):
    allowed_roles = ["owner", "manager"]

    def dispatch(self, request, *args, **kwargs):
        if self.get_role() not in self.allowed_roles:
            raise PermissionDenied("ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return super().dispatch(request, *args, **kwargs)


class CashierOrAboveRequiredMixin(MerchantRequiredMixin):
    allowed_roles = ["owner", "manager", "cashier"]

    def dispatch(self, request, *args, **kwargs):
        if self.get_role() not in self.allowed_roles:
            raise PermissionDenied("ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return super().dispatch(request, *args, **kwargs)