def create_failure_signature(
    workflow,
    failed_step
):

    workflow = (
        workflow
        .upper()
        .replace(" ", "_")
    )

    failed_step = (
        failed_step
        .upper()
    )

    return (
        f"{workflow}_"
        f"{failed_step}_FAILURE"
    )