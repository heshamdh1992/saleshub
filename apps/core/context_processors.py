def current_merchant(request):
    merchant = None
    user_role = None

    if request.user.is_authenticated:
        staff_profile = getattr(request.user, "staff_profile", None)
        if staff_profile:
            merchant = staff_profile.merchant
            user_role = staff_profile.role

    return {
        "current_merchant": merchant,
        "user_role": user_role,
    }