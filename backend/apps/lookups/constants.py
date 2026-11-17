class LookupTypeCode:
    """
    Codes of the lookup types the application code relies on.

    Values inside each type (e.g. the actual category names) are data and can
    be added, renamed or deactivated at any time from the Django admin or the
    Configuration screen - no code change or redeploy needed.
    """

    TICKET_CATEGORY = "ticket_category"
    TICKET_PRIORITY = "ticket_priority"
