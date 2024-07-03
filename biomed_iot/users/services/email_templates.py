import textwrap

def registration_confirmation_email(url):
    email_body =  f"""
    Dear User,

    Thank you for registering with Biomed IoT! We're excited to have you on board.

    To complete your registration, please confirm your email address by clicking on the link below:

    {url}

    Best regards,
    The Biomed IoT Team


    Note: If you received this email in error, please delete it.

    """
    return textwrap.dedent(email_body)
